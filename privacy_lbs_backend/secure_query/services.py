"""
C1云服务器服务层
实现安全剪枝、任务分发等核心逻辑
"""
import json
import uuid
from typing import List, Dict, Tuple, Optional
from django.core.cache import cache
from django.utils import timezone
from .models import SecureQuery, QueryLog
from data_owner.models import EncryptedSpatialObject, DataOwner, IndexMetadata
from indices.ktree import KTree, SpatialObject
from indices.asset_tree import AssetTree
from crypto.paillier_manager import PaillierManager
# 注意：安全协议需要C1和C2协作，这里仅导入类型
# from secure_protocols.secure_less_than import SecureLessThanProtocol
# from secure_protocols.secure_squared_euclidean_distance import SecureSquaredEuclideanDistanceProtocol
from fog_node.tasks import compute_encrypted_scores


class C1QueryService:
    """C1查询服务 - 系统的"大脑" """
    
    def __init__(self, public_key: str):
        """
        初始化C1服务
        
        Args:
            public_key: Paillier公钥（序列化字符串）
        """
        self.paillier_manager = PaillierManager()
        self.paillier_manager.load_public_key(public_key)
        # 注意：C1只有公钥，没有私钥
    
    def receive_query(self, query_data: Dict) -> SecureQuery:
        """
        接收查询请求
        
        Args:
            query_data: 查询数据字典
            
        Returns:
            SecureQuery: 创建的查询对象
        """
        query_id = str(uuid.uuid4())
        
        query = SecureQuery.objects.create(
            query_id=query_id,
            user=query_data['user'],
            encrypted_location_x=query_data['encrypted_location_x'],
            encrypted_location_y=query_data['encrypted_location_y'],
            encrypted_keywords=json.dumps(query_data['encrypted_keywords']),
            text_weight=query_data.get('text_weight', 0.5),
            distance_weight=query_data.get('distance_weight', 0.5),
            top_k=query_data.get('top_k', 10),
            is_continuous=query_data.get('is_continuous', False),
            status='pending'
        )
        
        QueryLog.objects.create(
            query=query,
            log_type='query_received',
            message=f"Query {query_id} received",
            metadata={'query_data': query_data}
        )
        
        return query
    
    def secure_pruning(self, query: SecureQuery, data_owner: DataOwner) -> List[Dict]:
        """
        安全剪枝 - 两级剪枝过程
        使用QL_qi和QS_qi进行空间和关键词剪枝
        
        Args:
            query: 查询对象
            data_owner: 数据所有者
            
        Returns:
            List[Dict]: 候选对象列表（加密状态）
        """
        QueryLog.objects.create(
            query=query,
            log_type='pruning_started',
            message="Starting secure pruning process"
        )
        
        # 获取索引元数据
        try:
            index_metadata = IndexMetadata.objects.get(data_owner=data_owner)
        except IndexMetadata.DoesNotExist:
            QueryLog.objects.create(
                query=query,
                log_type='pruning_error',
                message="Index not built for data owner"
            )
            return []
        
        # 第一级剪枝：空间剪枝 (QL_qi)
        # 使用AssetTree进行空间区域匹配
        spatial_candidates = self._spatial_pruning(query, data_owner, index_metadata)
        
        QueryLog.objects.create(
            query=query,
            log_type='spatial_pruning_completed',
            message=f"Spatial pruning found {len(spatial_candidates)} candidates",
            metadata={'candidate_count': len(spatial_candidates)}
        )
        
        # 第二级剪枝：关键词剪枝 (QS_qi)
        keyword_candidates = self._keyword_pruning(query, spatial_candidates, data_owner)
        
        QueryLog.objects.create(
            query=query,
            log_type='keyword_pruning_completed',
            message=f"Keyword pruning found {len(keyword_candidates)} candidates",
            metadata={'candidate_count': len(keyword_candidates)}
        )
        
        return keyword_candidates
    
    def _spatial_pruning(self, query: SecureQuery, data_owner: DataOwner, 
                        index_metadata: IndexMetadata) -> List[Dict]:
        """
        空间剪枝 (QL_qi)
        使用AssetTree和KTree进行空间区域匹配
        
        Args:
            query: 查询对象
            data_owner: 数据所有者
            index_metadata: 索引元数据
            
        Returns:
            List[Dict]: 空间候选对象
        """
        # 从缓存或存储中加载AssetTree（实际实现中需要从Redis/Cassandra加载）
        # 这里简化处理，直接查询数据库
        
        # 获取所有加密空间对象
        encrypted_objects = EncryptedSpatialObject.objects.filter(data_owner=data_owner)
        
        # 简化：返回所有对象（实际应该使用AssetTree进行精确匹配）
        candidates = []
        for obj in encrypted_objects:
            candidates.append({
                'object_id': obj.object_id,
                'encrypted_location_x': obj.encrypted_location_x,
                'encrypted_location_y': obj.encrypted_location_y,
                'encrypted_keywords': obj.encrypted_keywords,
                'ktree_node_path': obj.ktree_node_path,
                'ktree_region': obj.ktree_region
            })
        
        return candidates
    
    def _keyword_pruning(self, query: SecureQuery, spatial_candidates: List[Dict],
                         data_owner: DataOwner) -> List[Dict]:
        """
        关键词剪枝 (QS_qi)
        使用加密的关键词列表进行匹配
        
        Args:
            query: 查询对象
            spatial_candidates: 空间候选对象
            data_owner: 数据所有者
            
        Returns:
            List[Dict]: 关键词匹配的候选对象
        """
        # 获取查询关键词
        query_keywords = json.loads(query.encrypted_keywords)
        
        # 简化：返回所有空间候选（实际应该使用加密关键词列表进行匹配）
        # 在实际实现中，需要使用同态加密进行关键词匹配
        return spatial_candidates
    
    def distribute_tasks(self, query: SecureQuery, candidates: List[Dict]) -> List[str]:
        """
        任务分发
        使用Celery将候选集和查询密文打包成异步任务，分发给雾节点
        
        Args:
            query: 查询对象
            candidates: 候选对象列表
            
        Returns:
            List[str]: 任务ID列表
        """
        QueryLog.objects.create(
            query=query,
            log_type='task_distribution_started',
            message=f"Distributing {len(candidates)} candidates to fog nodes"
        )
        
        # 将候选集分批（每批处理一定数量的对象）
        batch_size = 50
        task_ids = []
        
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            
            # 创建Celery任务
            task = compute_encrypted_scores.delay(
                query_id=query.query_id,
                encrypted_query_x=query.encrypted_location_x,
                encrypted_query_y=query.encrypted_location_y,
                encrypted_query_keywords=query.encrypted_keywords,
                candidates=batch,
                text_weight=query.text_weight,
                distance_weight=query.distance_weight
            )
            
            task_ids.append(task.id)
            
            QueryLog.objects.create(
                query=query,
                log_type='task_created',
                message=f"Task {task.id} created for batch {i // batch_size + 1}",
                metadata={'task_id': task.id, 'batch_size': len(batch)}
            )
        
        return task_ids
    
    def aggregate_results(self, query: SecureQuery, task_ids: List[str]) -> List[Dict]:
        """
        聚合结果
        收集所有雾节点的计算结果，进行排序和Top-K选择
        
        Args:
            query: 查询对象
            task_ids: 任务ID列表
            
        Returns:
            List[Dict]: Top-K结果列表
        """
        QueryLog.objects.create(
            query=query,
            log_type='result_aggregation_started',
            message=f"Aggregating results from {len(task_ids)} tasks"
        )
        
        # 等待所有任务完成并收集结果
        all_results = []
        
        for task_id in task_ids:
            # 从缓存中获取任务结果（实际应该从Celery结果后端获取）
            result_key = f"task_result_{task_id}"
            result = cache.get(result_key)
            
            if result:
                all_results.extend(result.get('scores', []))
        
        # 简化：返回所有结果（实际需要使用安全协议进行排序）
        # 由于结果都是加密的，排序需要使用安全协议
        
        # 取Top-K
        top_k_results = all_results[:query.top_k]
        
        QueryLog.objects.create(
            query=query,
            log_type='result_aggregation_completed',
            message=f"Aggregated {len(top_k_results)} top results",
            metadata={'result_count': len(top_k_results)}
        )
        
        return top_k_results


class ContinuousQueryEngine:
    """连续查询引擎 - 安全区域监控机制"""
    
    def __init__(self, c1_service: C1QueryService):
        """
        初始化连续查询引擎
        
        Args:
            c1_service: C1查询服务
        """
        self.c1_service = c1_service
    
    def calculate_secure_area(self, query: SecureQuery) -> Dict:
        """
        计算安全区域 (QS_qi)
        为用户的首次查询计算安全区域
        
        Args:
            query: 查询对象
            
        Returns:
            Dict: 安全区域信息（加密状态）
        """
        # 简化实现：安全区域基于查询位置和一定半径
        # 实际实现中需要使用更复杂的算法
        
        secure_area = {
            'query_id': query.query_id,
            'encrypted_center_x': query.encrypted_location_x,
            'encrypted_center_y': query.encrypted_location_y,
            'radius': 1000.0,  # 简化：固定半径
            'created_at': timezone.now().isoformat()
        }
        
        # 存储到缓存
        cache_key = f"secure_area_{query.query_id}"
        cache.set(cache_key, secure_area, timeout=3600)  # 1小时过期
        
        QueryLog.objects.create(
            query=query,
            log_type='secure_area_calculated',
            message="Secure area calculated for continuous query",
            metadata=secure_area
        )
        
        return secure_area
    
    def check_location_in_secure_area(self, query: SecureQuery, 
                                     new_location_x: str, 
                                     new_location_y: str) -> bool:
        """
        检查新位置是否在安全区域内
        
        Args:
            query: 查询对象
            new_location_x: 新的加密X坐标
            new_location_y: 新的加密Y坐标
            
        Returns:
            bool: 是否在安全区域内
        """
        # 从缓存获取安全区域
        cache_key = f"secure_area_{query.query_id}"
        secure_area = cache.get(cache_key)
        
        if not secure_area:
            return False
        
        # 使用安全协议计算距离（简化实现）
        # 实际应该使用SSED协议计算加密距离
        # 然后使用SLESS协议判断是否在半径内
        
        # 简化：总是返回False，触发完整查询
        # 实际实现中需要使用安全协议进行判断
        return False
    
    def handle_location_update(self, query: SecureQuery, 
                               new_location_x: str, 
                               new_location_y: str) -> Dict:
        """
        处理位置更新
        
        Args:
            query: 查询对象
            new_location_x: 新的加密X坐标
            new_location_y: 新的加密Y坐标
            
        Returns:
            Dict: 处理结果
        """
        QueryLog.objects.create(
            query=query,
            log_type='location_update_received',
            message="Location update received for continuous query"
        )
        
        # 检查是否在安全区域内
        in_secure_area = self.check_location_in_secure_area(
            query, new_location_x, new_location_y
        )
        
        if in_secure_area:
            # 在安全区域内，返回缓存结果
            cache_key = f"query_result_{query.query_id}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                QueryLog.objects.create(
                    query=query,
                    log_type='cached_result_returned',
                    message="Returned cached result (within secure area)"
                )
                return {
                    'status': 'cached',
                    'result': cached_result
                }
        
        # 不在安全区域内，触发完整查询
        QueryLog.objects.create(
            query=query,
            log_type='full_query_triggered',
            message="Triggering full query (outside secure area)"
        )
        
        # 更新查询位置
        query.encrypted_location_x = new_location_x
        query.encrypted_location_y = new_location_y
        query.save()
        
        # 重新计算安全区域
        secure_area = self.calculate_secure_area(query)
        
        return {
            'status': 'full_query',
            'secure_area': secure_area,
            'message': 'Full query triggered, secure area updated'
        }

