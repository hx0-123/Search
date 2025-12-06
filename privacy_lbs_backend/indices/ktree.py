"""
KTree实现
实现空间分区四叉树、数据插入、倒排关键词列表构建和加密
"""
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
import json
from crypto.paillier_manager import PaillierManager


@dataclass
class SpatialObject:
    """空间对象"""
    object_id: str
    x: float
    y: float
    keywords: List[str]
    document: Optional[str] = None


@dataclass
class KTreeNode:
    """KTree节点"""
    node_id: str
    depth: int
    region: int  # 区域编号 0-3
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    objects: List[SpatialObject] = field(default_factory=list)
    children: List['KTreeNode'] = field(default_factory=list)
    is_leaf: bool = True
    keyword_list: Dict[str, List[str]] = field(default_factory=dict)  # 倒排关键词列表
    encrypted_keyword_list: Dict[str, List[str]] = field(default_factory=dict)  # 加密的倒排关键词列表
    
    def get_center(self) -> Tuple[float, float]:
        """获取区域中心点"""
        x_mid = (self.x_min + self.x_max) / 2
        y_mid = (self.y_min + self.y_max) / 2
        return x_mid, y_mid
    
    def contains(self, x: float, y: float) -> bool:
        """判断点是否在区域内"""
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max
    
    def get_region_for_point(self, x: float, y: float) -> int:
        """
        根据点的坐标确定所属区域编号
        区域划分：
        0: [x_min, x_mid], [y_min, y_mid]  (左下)
        1: (x_mid, x_max], [y_min, y_mid]  (右下)
        2: [x_min, x_mid], (y_mid, y_max]  (左上)
        3: (x_mid, x_max], (y_mid, y_max]  (右上)
        """
        x_mid = (self.x_min + self.x_max) / 2
        y_mid = (self.y_min + self.y_max) / 2
        
        if x <= x_mid:
            if y <= y_mid:
                return 0
            else:
                return 2
        else:
            if y <= y_mid:
                return 1
            else:
                return 3


class KTree:
    """
    KTree - 安全存储索引结构
    实现空间四叉树分区、数据插入、倒排关键词列表构建和加密
    """
    
    def __init__(self, x_min: float, x_max: float, y_min: float, y_max: float,
                 threshold: int = 10, max_depth: int = 10):
        """
        初始化KTree
        
        Args:
            x_min: 空间域X轴最小值
            x_max: 空间域X轴最大值
            y_min: 空间域Y轴最小值
            y_max: 空间域Y轴最大值
            threshold: 叶子节点最大对象数阈值 (N_TS)
            max_depth: 最大深度
        """
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.threshold = threshold
        self.max_depth = max_depth
        self.depth = 0
        
        # 创建根节点
        self.root = KTreeNode(
            node_id="root",
            depth=0,
            region=0,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max
        )
        
        self.node_count = 1
        self.leaf_count = 1
    
    def _normalize_coordinate(self, x: float, y: float) -> Tuple[float, float]:
        """
        归一化坐标
        根据公式6: x_pi' = (x_pi - x_D^min) / x_mid
        """
        x_mid = (self.x_max - self.x_min) / 2
        y_mid = (self.y_max - self.y_min) / 2
        
        x_norm = (x - self.x_min) / x_mid if x_mid > 0 else 0
        y_norm = (y - self.y_min) / y_mid if y_mid > 0 else 0
        
        return x_norm, y_norm
    
    def _get_region_function(self, coord_norm: float) -> int:
        """
        区域函数
        根据公式: f(x_pi') = {0, if x_pi' <= 1; 4, else}
        """
        return 0 if coord_norm <= 1.0 else 4
    
    def insert(self, obj: SpatialObject) -> str:
        """
        插入空间对象到KTree
        
        Args:
            obj: 空间对象
            
        Returns:
            str: 对象插入的节点路径
        """
        return self._insert_recursive(self.root, obj, [])
    
    def _insert_recursive(self, node: KTreeNode, obj: SpatialObject, path: List[int]) -> str:
        """
        递归插入对象
        
        Args:
            node: 当前节点
            obj: 要插入的对象
            path: 当前路径
            
        Returns:
            str: 节点路径字符串
        """
        # 如果节点是叶子节点且对象数未超过阈值，直接插入
        if node.is_leaf and len(node.objects) < self.threshold:
            node.objects.append(obj)
            node_path = "/".join(map(str, path)) if path else "root"
            return node_path
        
        # 如果节点是叶子节点但对象数超过阈值，需要分裂
        if node.is_leaf and len(node.objects) >= self.threshold and node.depth < self.max_depth:
            self._split_node(node)
        
        # 如果节点有子节点，递归插入到合适的子节点
        if not node.is_leaf:
            region = node.get_region_for_point(obj.x, obj.y)
            child = node.children[region]
            new_path = path + [region]
            return self._insert_recursive(child, obj, new_path)
        
        # 如果无法分裂（达到最大深度），直接插入当前节点
        node.objects.append(obj)
        node_path = "/".join(map(str, path)) if path else "root"
        return node_path
    
    def _split_node(self, node: KTreeNode):
        """
        分裂节点为四个子区域
        """
        x_mid = (node.x_min + node.x_max) / 2
        y_mid = (node.y_min + node.y_max) / 2
        
        # 创建四个子节点
        regions = [
            (0, node.x_min, x_mid, node.y_min, y_mid),      # 左下
            (1, x_mid, node.x_max, node.y_min, y_mid),      # 右下
            (2, node.x_min, x_mid, y_mid, node.y_max),      # 左上
            (3, x_mid, node.x_max, y_mid, node.y_max),      # 右上
        ]
        
        for region, x_min, x_max, y_min, y_max in regions:
            child = KTreeNode(
                node_id=f"{node.node_id}_{region}",
                depth=node.depth + 1,
                region=region,
                x_min=x_min,
                x_max=x_max,
                y_min=y_min,
                y_max=y_max
            )
            node.children.append(child)
            self.node_count += 1
        
        # 将当前节点的对象重新分配到子节点
        objects_to_redistribute = node.objects[:]
        node.objects = []
        node.is_leaf = False
        self.leaf_count += 3  # 新增3个叶子节点，当前节点不再是叶子
        
        for obj in objects_to_redistribute:
            region = node.get_region_for_point(obj.x, obj.y)
            child = node.children[region]
            child.objects.append(obj)
            if len(child.objects) >= self.threshold and child.depth < self.max_depth:
                self._split_node(child)
        
        # 更新树深度
        self.depth = max(self.depth, node.depth + 1)
    
    def build_keyword_lists(self):
        """
        为所有叶子节点构建倒排关键词列表 (KwList)
        """
        self._build_keyword_lists_recursive(self.root)
    
    def _build_keyword_lists_recursive(self, node: KTreeNode):
        """
        递归构建关键词列表
        """
        if node.is_leaf:
            # 为叶子节点构建倒排关键词列表
            keyword_list = {}
            for obj in node.objects:
                for keyword in obj.keywords:
                    if keyword not in keyword_list:
                        keyword_list[keyword] = []
                    keyword_list[keyword].append(obj.object_id)
            node.keyword_list = keyword_list
        else:
            # 递归处理子节点
            for child in node.children:
                self._build_keyword_lists_recursive(child)
    
    def encrypt_keyword_lists(self, paillier_manager: PaillierManager):
        """
        加密所有叶子节点的倒排关键词列表
        
        Args:
            paillier_manager: Paillier加密管理器
        """
        self._encrypt_keyword_lists_recursive(self.root, paillier_manager)
    
    def _encrypt_keyword_lists_recursive(self, node: KTreeNode, paillier_manager: PaillierManager):
        """
        递归加密关键词列表
        """
        if node.is_leaf:
            # 加密倒排关键词列表
            encrypted_keyword_list = {}
            for keyword, object_ids in node.keyword_list.items():
                # 加密每个对象ID（这里简化处理，实际可能需要更复杂的加密策略）
                encrypted_object_ids = [
                    paillier_manager.encrypt_int(hash(obj_id) % 1000000)  # 简化：加密对象ID的哈希值
                    for obj_id in object_ids
                ]
                encrypted_keyword_list[keyword] = encrypted_object_ids
            node.encrypted_keyword_list = encrypted_keyword_list
        else:
            # 递归处理子节点
            for child in node.children:
                self._encrypt_keyword_lists_recursive(child, paillier_manager)
    
    def get_leaf_nodes(self) -> List[KTreeNode]:
        """
        获取所有叶子节点
        
        Returns:
            List[KTreeNode]: 叶子节点列表
        """
        leaf_nodes = []
        self._collect_leaf_nodes(self.root, leaf_nodes)
        return leaf_nodes
    
    def _collect_leaf_nodes(self, node: KTreeNode, leaf_nodes: List[KTreeNode]):
        """递归收集叶子节点"""
        if node.is_leaf:
            leaf_nodes.append(node)
        else:
            for child in node.children:
                self._collect_leaf_nodes(child, leaf_nodes)
    
    def get_node_by_path(self, path: str) -> Optional[KTreeNode]:
        """
        根据路径获取节点
        
        Args:
            path: 节点路径（如 "root/0/1"）
            
        Returns:
            Optional[KTreeNode]: 节点对象
        """
        if path == "root" or path == "":
            return self.root
        
        parts = path.split("/")
        if parts[0] == "root":
            parts = parts[1:]
        
        node = self.root
        for part in parts:
            region = int(part)
            if not node.is_leaf and region < len(node.children):
                node = node.children[region]
            else:
                return None
        
        return node
    
    def get_statistics(self) -> Dict:
        """
        获取KTree统计信息
        
        Returns:
            Dict: 统计信息
        """
        leaf_nodes = self.get_leaf_nodes()
        return {
            'depth': self.depth,
            'node_count': self.node_count,
            'leaf_count': len(leaf_nodes),
            'total_objects': sum(len(node.objects) for node in leaf_nodes),
            'spatial_domain': {
                'x_min': self.x_min,
                'x_max': self.x_max,
                'y_min': self.y_min,
                'y_max': self.y_max
            }
        }

