"""
安全查询API视图
实现C1云服务器的核心逻辑
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
import json
from .models import SecureQuery, QueryLog
from .serializers import QueryInitiateSerializer, LocationUpdateSerializer, QueryResultSerializer
from .services import C1QueryService, ContinuousQueryEngine
from data_owner.models import DataOwner


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_query(request):
    """
    查询发起接口
    POST /api/query/initiate/
    
    允许用户提交加密连续查询
    """
    serializer = QueryInitiateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # 获取数据所有者（简化：使用第一个数据所有者）
    # 实际应该根据查询参数确定数据所有者
    try:
        data_owner = DataOwner.objects.first()
        if not data_owner:
            return Response(
                {'error': 'No data owner found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except DataOwner.DoesNotExist:
        return Response(
            {'error': 'No data owner found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 初始化C1服务
    c1_service = C1QueryService(data_owner.public_key)
    
    # 准备查询数据
    query_data = {
        'user': request.user,
        'encrypted_location_x': serializer.validated_data['encrypted_location_x'],
        'encrypted_location_y': serializer.validated_data['encrypted_location_y'],
        'encrypted_keywords': serializer.validated_data['encrypted_keywords'],
        'text_weight': serializer.validated_data.get('text_weight', 0.5),
        'distance_weight': serializer.validated_data.get('distance_weight', 0.5),
        'top_k': serializer.validated_data.get('top_k', 10),
        'is_continuous': serializer.validated_data.get('is_continuous', False)
    }
    
    # 接收查询
    query = c1_service.receive_query(query_data)
    
    # 如果是连续查询，计算安全区域
    if query.is_continuous:
        continuous_engine = ContinuousQueryEngine(c1_service)
        secure_area = continuous_engine.calculate_secure_area(query)
    else:
        secure_area = None
    
    # 执行安全剪枝
    candidates = c1_service.secure_pruning(query, data_owner)
    
    if not candidates:
        query.status = 'completed'
        query.completed_at = timezone.now()
        query.save()
        
        return Response({
            'query_id': query.query_id,
            'status': 'completed',
            'message': 'No candidates found',
            'encrypted_results': []
        }, status=status.HTTP_200_OK)
    
    # 分发任务到雾节点
    task_ids = c1_service.distribute_tasks(query, candidates)
    
    # 更新查询状态
    query.status = 'processing'
    query.metadata = {
        'task_ids': task_ids,
        'candidate_count': len(candidates),
        'secure_area': secure_area
    }
    query.save()
    
    # 异步聚合结果（实际应该使用Celery任务）
    # 这里简化处理，直接返回任务ID
    return Response({
        'query_id': query.query_id,
        'status': 'processing',
        'message': 'Query initiated, processing in background',
        'task_ids': task_ids,
        'secure_area': secure_area
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_location(request):
    """
    位置更新接口
    POST /api/query/update_location/
    
    允许用户更新位置，触发安全区域检查
    """
    serializer = LocationUpdateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    query_id = serializer.validated_data['query_id']
    new_location_x = serializer.validated_data['encrypted_location_x']
    new_location_y = serializer.validated_data['encrypted_location_y']
    
    # 获取查询对象
    try:
        query = SecureQuery.objects.get(query_id=query_id, user=request.user)
    except SecureQuery.DoesNotExist:
        return Response(
            {'error': 'Query not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not query.is_continuous:
        return Response(
            {'error': 'Query is not continuous'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 获取数据所有者
    try:
        data_owner = DataOwner.objects.first()
        if not data_owner:
            return Response(
                {'error': 'No data owner found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    except DataOwner.DoesNotExist:
        return Response(
            {'error': 'No data owner found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 初始化服务和引擎
    c1_service = C1QueryService(data_owner.public_key)
    continuous_engine = ContinuousQueryEngine(c1_service)
    
    # 处理位置更新
    result = continuous_engine.handle_location_update(
        query, new_location_x, new_location_y
    )
    
    if result['status'] == 'cached':
        # 返回缓存结果
        return Response({
            'query_id': query_id,
            'status': 'cached',
            'message': 'Result from cache (within secure area)',
            'encrypted_results': result['result']
        }, status=status.HTTP_200_OK)
    else:
        # 触发完整查询
        # 执行安全剪枝
        candidates = c1_service.secure_pruning(query, data_owner)
        
        if not candidates:
            query.status = 'completed'
            query.completed_at = timezone.now()
            query.save()
            
            return Response({
                'query_id': query_id,
                'status': 'completed',
                'message': 'No candidates found',
                'encrypted_results': []
            }, status=status.HTTP_200_OK)
        
        # 分发任务
        task_ids = c1_service.distribute_tasks(query, candidates)
        
        # 更新查询状态
        query.status = 'processing'
        query.metadata = {
            'task_ids': task_ids,
            'candidate_count': len(candidates),
            'secure_area': result.get('secure_area')
        }
        query.save()
        
        return Response({
            'query_id': query_id,
            'status': 'processing',
            'message': result.get('message', 'Full query triggered'),
            'task_ids': task_ids,
            'secure_area': result.get('secure_area')
        }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_query_result(request, query_id):
    """
    获取查询结果
    GET /api/query/{query_id}/result/
    """
    try:
        query = SecureQuery.objects.get(query_id=query_id, user=request.user)
    except SecureQuery.DoesNotExist:
        return Response(
            {'error': 'Query not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 解析加密结果
    encrypted_results = []
    if query.encrypted_results:
        try:
            encrypted_results = json.loads(query.encrypted_results)
        except (json.JSONDecodeError, TypeError):
            encrypted_results = []
    
    serializer = QueryResultSerializer({
        'query_id': query.query_id,
        'status': query.status,
        'encrypted_results': encrypted_results,
        'message': f'Query {query.status}'
    })
    
    return Response(serializer.data, status=status.HTTP_200_OK)
