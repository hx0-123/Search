"""
数据所有者API视图
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
import json
import uuid
from .models import DataOwner, EncryptedSpatialObject, IndexMetadata
from .serializers import DataUploadSerializer, DataOwnerSerializer, EncryptedSpatialObjectSerializer
from indices.ktree import KTree, SpatialObject
from indices.asset_tree import AssetTree
from crypto.paillier_manager import PaillierManager


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_data(request):
    """
    数据上传接口
    POST /api/data/upload/
    
    允许数据所有者上传加密数据并构建索引
    """
    serializer = DataUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    owner_id = serializer.validated_data['owner_id']
    objects_data = serializer.validated_data['objects']
    public_key_str = serializer.validated_data['public_key']
    
    # 获取或创建数据所有者
    data_owner, created = DataOwner.objects.get_or_create(
        owner_id=owner_id,
        defaults={
            'user': request.user,
            'public_key': public_key_str
        }
    )
    
    if not created:
        # 更新公钥
        data_owner.public_key = public_key_str
        data_owner.save()
    
    # 初始化Paillier管理器
    paillier_manager = PaillierManager()
    paillier_manager.load_public_key(public_key_str)
    
    # 加密并存储对象
    encrypted_objects = []
    spatial_objects = []
    
    # 确定空间域范围
    if objects_data:
        x_coords = [obj['x'] for obj in objects_data]
        y_coords = [obj['y'] for obj in objects_data]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # 扩展边界（添加10%的边距）
        x_range = x_max - x_min
        y_range = y_max - y_min
        x_min -= x_range * 0.1
        x_max += x_range * 0.1
        y_min -= y_range * 0.1
        y_max += y_range * 0.1
    else:
        return Response({'error': 'No objects provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 创建KTree
    ktree = KTree(x_min, x_max, y_min, y_max, threshold=10, max_depth=10)
    
    # 处理每个对象
    for obj_data in objects_data:
        obj_id = obj_data.get('object_id', str(uuid.uuid4()))
        x = obj_data['x']
        y = obj_data['y']
        keywords = obj_data.get('keywords', [])
        document = obj_data.get('document', '')
        
        # 加密位置
        enc_x = paillier_manager.encrypt(x)
        enc_y = paillier_manager.encrypt(y)
        
        # 加密关键词（简化：加密关键词的哈希值）
        encrypted_keywords = [paillier_manager.encrypt_int(hash(kw) % 1000000) for kw in keywords]
        
        # 创建空间对象并插入KTree
        spatial_obj = SpatialObject(
            object_id=obj_id,
            x=x,
            y=y,
            keywords=keywords,
            document=document
        )
        node_path = ktree.insert(spatial_obj)
        spatial_objects.append(spatial_obj)
        
        # 获取节点区域
        node = ktree.get_node_by_path(node_path)
        region = node.region if node else 0
        
        # 保存加密对象到数据库
        encrypted_obj = EncryptedSpatialObject.objects.create(
            data_owner=data_owner,
            object_id=obj_id,
            original_x=x,  # 仅用于调试
            original_y=y,  # 仅用于调试
            encrypted_location_x=enc_x,
            encrypted_location_y=enc_y,
            encrypted_keywords=json.dumps(encrypted_keywords),
            encrypted_document=paillier_manager.encrypt(document) if document else '',
            ktree_node_path=node_path,
            ktree_region=region
        )
        encrypted_objects.append(encrypted_obj)
    
    # 构建KTree的关键词列表
    ktree.build_keyword_lists()
    
    # 加密关键词列表
    ktree.encrypt_keyword_lists(paillier_manager)
    
    # 构建AssetTree
    asset_tree = AssetTree(ktree, paillier_manager)
    asset_tree.build()
    asset_tree.precompute_all_intervals()
    
    # 保存索引元数据
    stats = ktree.get_statistics()
    index_metadata, created = IndexMetadata.objects.get_or_create(
        data_owner=data_owner,
        defaults={
            'ktree_depth': stats['depth'],
            'ktree_node_count': stats['node_count'],
            'ktree_leaf_count': stats['leaf_count'],
            'spatial_domain_x_min': stats['spatial_domain']['x_min'],
            'spatial_domain_x_max': stats['spatial_domain']['x_max'],
            'spatial_domain_y_min': stats['spatial_domain']['y_min'],
            'spatial_domain_y_max': stats['spatial_domain']['y_max'],
            'assettree_size': asset_tree.size,
            'build_status': 'completed',
            'build_started_at': timezone.now(),
            'build_completed_at': timezone.now(),
            'index_storage_type': 'redis'  # 实际应该存储到Redis
        }
    )
    
    if not created:
        # 更新索引元数据
        index_metadata.ktree_depth = stats['depth']
        index_metadata.ktree_node_count = stats['node_count']
        index_metadata.ktree_leaf_count = stats['leaf_count']
        index_metadata.assettree_size = asset_tree.size
        index_metadata.build_status = 'completed'
        index_metadata.build_completed_at = timezone.now()
        index_metadata.save()
    
    # 更新数据所有者统计
    data_owner.total_objects = len(encrypted_objects)
    data_owner.encrypted_objects = len(encrypted_objects)
    data_owner.index_built = True
    data_owner.index_version = str(uuid.uuid4())[:8]
    data_owner.save()
    
    return Response({
        'message': 'Data uploaded and index built successfully',
        'owner_id': owner_id,
        'objects_count': len(encrypted_objects),
        'index_built': True,
        'index_metadata': {
            'ktree_depth': stats['depth'],
            'ktree_node_count': stats['node_count'],
            'ktree_leaf_count': stats['leaf_count'],
            'assettree_size': asset_tree.size
        }
    }, status=status.HTTP_201_CREATED)
