"""
安全平方欧氏距离计算协议 (Secure Squared Euclidean Distance, SSED)
实现 SSED(Epk(m₁), Epk(m₂)) = Epk((x₁ - x₂)² + (y₁ - y₂)²)
需要C1和C2协作执行
"""
from crypto.paillier_manager import PaillierManager
from secure_protocols.secure_multiplication import SecureMultiplicationProtocol


class SecureSquaredEuclideanDistanceProtocol:
    """
    安全平方欧氏距离计算协议
    计算两个加密点的平方欧氏距离
    """
    
    def __init__(self, c1_manager: PaillierManager, c2_manager: PaillierManager):
        """
        初始化安全平方欧氏距离协议
        
        Args:
            c1_manager: C1服务器的Paillier管理器
            c2_manager: C2服务器的Paillier管理器
        """
        self.c1_manager = c1_manager
        self.c2_manager = c2_manager
        self.sm_protocol = SecureMultiplicationProtocol(c1_manager, c2_manager)
    
    def execute(self, enc_x1: str, enc_y1: str, enc_x2: str, enc_y2: str) -> str:
        """
        执行安全平方欧氏距离计算
        
        计算: (x₁ - x₂)² + (y₁ - y₂)²
        
        协议流程：
        1. 计算 Epk(x₁ - x₂) 和 Epk(y₁ - y₂)
        2. 使用安全乘法计算 Epk((x₁ - x₂)²) 和 Epk((y₁ - y₂)²)
        3. 同态加法得到最终结果
        
        Args:
            enc_x1: 加密的x₁
            enc_y1: 加密的y₁
            enc_x2: 加密的x₂
            enc_y2: 加密的y₂
            
        Returns:
            str: 加密的平方欧氏距离
        """
        # 步骤1: 计算 Epk(x₁ - x₂) 和 Epk(y₁ - y₂)
        enc_neg_x2 = self.c1_manager.multiply_plaintext(enc_x2, -1.0)
        enc_neg_y2 = self.c1_manager.multiply_plaintext(enc_y2, -1.0)
        
        enc_diff_x = self.c1_manager.add(enc_x1, enc_neg_x2)
        enc_diff_y = self.c1_manager.add(enc_y1, enc_neg_y2)
        
        # 步骤2: 使用安全乘法计算 Epk((x₁ - x₂)²) 和 Epk((y₁ - y₂)²)
        enc_diff_x_squared = self.sm_protocol.execute(enc_diff_x, enc_diff_x)
        enc_diff_y_squared = self.sm_protocol.execute(enc_diff_y, enc_diff_y)
        
        # 步骤3: 同态加法得到最终结果
        enc_result = self.c1_manager.add(enc_diff_x_squared, enc_diff_y_squared)
        
        return enc_result


def secure_squared_euclidean_distance(enc_x1: str, enc_y1: str, enc_x2: str, enc_y2: str,
                                     c1_public_key: str, c2_private_key: str) -> str:
    """
    安全平方欧氏距离计算的便捷函数
    
    Args:
        enc_x1: 加密的x₁
        enc_y1: 加密的y₁
        enc_x2: 加密的x₂
        enc_y2: 加密的y₂
        c1_public_key: C1的公钥
        c2_private_key: C2的私钥
        
    Returns:
        str: 加密的平方欧氏距离
    """
    c1_manager = PaillierManager()
    c1_manager.load_public_key(c1_public_key)
    
    c2_manager = PaillierManager()
    # 加载C2的密钥对
    
    protocol = SecureSquaredEuclideanDistanceProtocol(c1_manager, c2_manager)
    return protocol.execute(enc_x1, enc_y1, enc_x2, enc_y2)

