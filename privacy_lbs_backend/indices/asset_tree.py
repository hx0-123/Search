"""
AssetTree实现
安全查询索引，用于保护用户隐私
预计算和存储所有可能的加密查询区间和路径
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import math
from crypto.paillier_manager import PaillierManager
from indices.ktree import KTree


@dataclass
class AssetTreeNode:
    """AssetTree节点"""
    node_id: str
    value: str  # 加密的值 Epk(0) 或 Epk(1)
    interval_left: str  # 加密的区间左端点
    interval_right: str  # 加密的区间右端点
    children: List['AssetTreeNode'] = field(default_factory=list)
    is_leaf: bool = True
    trace: Optional[int] = None  # 查询路径值
    
    def get_interval(self) -> Tuple[str, str]:
        """获取加密区间"""
        return self.interval_left, self.interval_right


class AssetTree:
    """
    AssetTree - 安全查询索引
    基于KTree的高度和空间范围，预计算和存储所有可能的加密查询区间和路径
    """
    
    def __init__(self, ktree: KTree, paillier_manager: PaillierManager):
        """
        初始化AssetTree
        
        Args:
            ktree: 已构建的KTree
            paillier_manager: Paillier加密管理器
        """
        self.ktree = ktree
        self.paillier_manager = paillier_manager
        self.root: Optional[AssetTreeNode] = None
        self.size = 0
        self.height = ktree.depth
        
        # 存储所有可能的加密查询区间
        self.encrypted_intervals: Dict[str, Tuple[str, str]] = {}
        
        # 存储所有可能的加密查询路径
        self.encrypted_traces: Dict[int, str] = {}
    
    def build(self):
        """
        构建AssetTree索引树
        对应论文中的算法1
        """
        # 计算需要的节点数：2^(H_KT + 1)
        target_size = 2 ** (self.height + 1)
        
        # 初始化根节点
        node_list = []
        
        # 创建初始区间（基于KTree的空间域）
        x_range = self.ktree.x_max - self.ktree.x_min
        y_range = self.ktree.y_max - self.ktree.y_min
        
        # 计算基础区间大小
        x_mid = x_range / (2 ** self.height)
        y_mid = y_range / (2 ** self.height)
        
        # 创建根节点（覆盖整个空间域）
        root_interval_left = self.paillier_manager.encrypt(self.ktree.x_min)
        root_interval_right = self.paillier_manager.encrypt(self.ktree.x_max)
        
        root_node = AssetTreeNode(
            node_id="root",
            value=self.paillier_manager.encrypt_int(0),
            interval_left=root_interval_left,
            interval_right=root_interval_right
        )
        
        node_list.append(root_node)
        self.root = root_node
        self.size = 1
        
        # 递归构建树
        while len(node_list) > 0 and self.size < target_size:
            current_node = node_list.pop(0)
            
            if self.size >= target_size:
                break
            
            # 计算区间中点
            # 需要解密区间端点来计算中点（在实际协议中，这需要C1和C2协作）
            # 这里简化处理，直接使用空间域信息
            interval_mid = (self.ktree.x_min + self.ktree.x_max) / 2
            
            # 创建两个子区间
            # I'_l = [Epk(I_l), Epk(I_l + I_mid)]
            # I'_r = (Epk(I_l + I_mid), Epk(I_r)]
            
            # 计算 I_l + I_mid 的加密值
            # 由于同态加密的限制，这里需要特殊处理
            # 简化：使用预计算的区间
            
            # 创建左子节点
            left_interval_left = current_node.interval_left
            left_interval_right = self.paillier_manager.encrypt(interval_mid)
            
            left_node = AssetTreeNode(
                node_id=f"{current_node.node_id}_0",
                value=self.paillier_manager.encrypt_int(0),
                interval_left=left_interval_left,
                interval_right=left_interval_right
            )
            
            # 创建右子节点
            right_interval_left = self.paillier_manager.encrypt(interval_mid)
            right_interval_right = current_node.interval_right
            
            right_node = AssetTreeNode(
                node_id=f"{current_node.node_id}_1",
                value=self.paillier_manager.encrypt_int(1),
                interval_left=right_interval_left,
                interval_right=right_interval_right
            )
            
            current_node.children = [left_node, right_node]
            current_node.is_leaf = False
            
            node_list.append(left_node)
            node_list.append(right_node)
            
            self.size += 2
        
        # 构建完成后，预计算所有可能的查询路径
        self._precompute_traces()
    
    def _precompute_traces(self):
        """
        预计算所有可能的加密查询路径 (trace)
        trace = trace^x + 2 * trace^y
        """
        if not self.root:
            return
        
        # 遍历所有叶子节点，计算trace值
        self._compute_traces_recursive(self.root, 0, 0)
    
    def _compute_traces_recursive(self, node: AssetTreeNode, trace_x: int, trace_y: int):
        """
        递归计算trace值
        """
        if node.is_leaf:
            # 计算trace = trace^x + 2 * trace^y
            trace = trace_x + 2 * trace_y
            node.trace = trace
            
            # 存储加密的trace值
            encrypted_trace = self.paillier_manager.encrypt_int(trace)
            self.encrypted_traces[trace] = encrypted_trace
        else:
            # 递归处理子节点
            if len(node.children) >= 2:
                # 左子节点：trace_x不变
                self._compute_traces_recursive(node.children[0], trace_x, trace_y * 2)
                # 右子节点：trace_x + 1
                self._compute_traces_recursive(node.children[1], trace_x + 1, trace_y * 2)
    
    def get_query_trace(self, z_qx: int, z_qy: int) -> Optional[str]:
        """
        根据查询坐标获取加密的trace值
        
        Args:
            z_qx: 查询点的x坐标（变换后）
            z_qy: 查询点的y坐标（变换后）
            
        Returns:
            Optional[str]: 加密的trace值
        """
        trace = z_qx + 2 * z_qy
        return self.encrypted_traces.get(trace)
    
    def get_interval_for_region(self, region: int) -> Optional[Tuple[str, str]]:
        """
        根据KTree区域编号获取对应的加密区间
        
        Args:
            region: 区域编号 (0-3)
            
        Returns:
            Optional[Tuple[str, str]]: 加密区间 (left, right)
        """
        return self.encrypted_intervals.get(str(region))
    
    def precompute_all_intervals(self):
        """
        预计算所有可能的加密查询区间
        基于KTree的叶子节点区域
        """
        leaf_nodes = self.ktree.get_leaf_nodes()
        
        for leaf in leaf_nodes:
            region = leaf.region
            
            # 加密区间端点
            # 根据论文，区间需要基于KTree的结构进行变换
            x_mid = (leaf.x_max - leaf.x_min) / (2 ** self.height)
            y_mid = (leaf.y_max - leaf.y_min) / (2 ** self.height)
            
            # 计算变换后的区间
            # 根据公式7的约束条件
            interval_left_x = self.paillier_manager.encrypt(
                (leaf.x_min - self.ktree.x_min) / x_mid if x_mid > 0 else 0
            )
            interval_right_x = self.paillier_manager.encrypt(
                (leaf.x_max - self.ktree.x_min) / x_mid if x_mid > 0 else 0
            )
            
            interval_left_y = self.paillier_manager.encrypt(
                (leaf.y_min - self.ktree.y_min) / y_mid if y_mid > 0 else 0
            )
            interval_right_y = self.paillier_manager.encrypt(
                (leaf.y_max - self.ktree.y_min) / y_mid if y_mid > 0 else 0
            )
            
            # 存储区间（分别存储x和y方向）
            self.encrypted_intervals[f"{region}_x"] = (interval_left_x, interval_right_x)
            self.encrypted_intervals[f"{region}_y"] = (interval_left_y, interval_right_y)
    
    def ftrace(self, z_px: int, z_py: int, z_qx: int, z_qy: int) -> Tuple[int, int]:
        """
        分治查询函数
        根据查询坐标对获取trace值
        
        Args:
            z_px, z_py: 数据点的变换坐标
            z_qx, z_qy: 查询点的变换坐标
            
        Returns:
            Tuple[int, int]: (trace_p, trace_q)
        """
        trace_p = z_px + 2 * z_py
        trace_q = z_qx + 2 * z_qy
        
        return trace_p, trace_q
    
    def get_statistics(self) -> Dict:
        """
        获取AssetTree统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'size': self.size,
            'height': self.height,
            'interval_count': len(self.encrypted_intervals),
            'trace_count': len(self.encrypted_traces)
        }

