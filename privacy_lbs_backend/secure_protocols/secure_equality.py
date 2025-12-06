"""
安全等于协议 (Secure Equality, SEQ)
实现 SEQ(Epk(m₀), Epk(m₁)) = Epk(Bool(m₀ == m₁))
需要C1和C2协作执行
"""
from crypto.paillier_manager import PaillierManager
from secure_protocols.secure_less_than import SecureLessThanProtocol
import random


class SecureEqualityProtocol:
    """
    安全等于比较协议
    判断两个密文是否相等
    """
    
    def __init__(self, c1_manager: PaillierManager, c2_manager: PaillierManager):
        """
        初始化安全等于协议
        
        Args:
            c1_manager: C1服务器的Paillier管理器
            c2_manager: C2服务器的Paillier管理器
        """
        self.c1_manager = c1_manager
        self.c2_manager = c2_manager
        self.sless_protocol = SecureLessThanProtocol(c1_manager, c2_manager)
    
    def execute(self, enc_m0: str, enc_m1: str) -> str:
        """
        执行安全等于比较协议
        
        协议流程：
        1. 计算 Epk(m₀ - m₁)
        2. 判断 Epk(m₀ - m₁) == Epk(0)
        3. 使用安全小于协议判断 |m₀ - m₁| < ε（误差阈值）
        
        简化实现：
        1. C1计算 Epk(m₀ - m₁)
        2. C2解密并判断是否接近0
        
        Args:
            enc_m0: 加密的m₀
            enc_m1: 加密的m₁
            
        Returns:
            str: 加密的布尔值，1表示m₀ == m₁，0表示m₀ != m₁
        """
        # 步骤1: C1计算 Epk(m₀ - m₁)
        enc_neg_m1 = self.c1_manager.multiply_plaintext(enc_m1, -1.0)
        enc_diff = self.c1_manager.add(enc_m0, enc_neg_m1)
        
        # 步骤2: C1生成随机数r
        r = random.randint(1, 1000000)
        enc_r = self.c1_manager.encrypt_int(r)
        enc_diff_plus_r = self.c1_manager.add(enc_diff, enc_r)
        
        # 步骤3: C2解密得到 (m₀ - m₁ + r)
        diff_plus_r = self.c2_manager.decrypt_int(enc_diff_plus_r)
        
        # 步骤4: C2判断是否相等（考虑浮点数误差）
        epsilon = 1000  # 误差阈值（考虑精度因子）
        is_equal = 1 if abs(diff_plus_r - r) < epsilon else 0
        
        # 步骤5: C2返回加密的布尔结果（使用C1的公钥）
        enc_result = self.c1_manager.encrypt_int(is_equal)
        
        return enc_result


def secure_equality(enc_m0: str, enc_m1: str,
                   c1_public_key: str, c2_private_key: str) -> str:
    """
    安全等于比较协议的便捷函数
    
    Args:
        enc_m0: 加密的m₀
        enc_m1: 加密的m₁
        c1_public_key: C1的公钥
        c2_private_key: C2的私钥
        
    Returns:
        str: 加密的布尔值，1表示m₀ == m₁，0表示m₀ != m₁
    """
    c1_manager = PaillierManager()
    c1_manager.load_public_key(c1_public_key)
    
    c2_manager = PaillierManager()
    # 加载C2的密钥对
    
    protocol = SecureEqualityProtocol(c1_manager, c2_manager)
    return protocol.execute(enc_m0, enc_m1)

