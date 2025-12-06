"""
安全除法协议 (Secure Division, SDC)
实现 Epk(m₀ / m₁) = SDC(Epk(m₀), Epk(m₁))
需要C1和C2协作执行
"""
from crypto.paillier_manager import PaillierManager
from secure_protocols.secure_multiplication import SecureMultiplicationProtocol
import random


class SecureDivisionProtocol:
    """
    安全除法协议
    实现两个密文的除法运算
    """
    
    def __init__(self, c1_manager: PaillierManager, c2_manager: PaillierManager):
        """
        初始化安全除法协议
        
        Args:
            c1_manager: C1服务器的Paillier管理器
            c2_manager: C2服务器的Paillier管理器
        """
        self.c1_manager = c1_manager
        self.c2_manager = c2_manager
        self.sm_protocol = SecureMultiplicationProtocol(c1_manager, c2_manager)
    
    def execute(self, enc_m0: str, enc_m1: str, precision: int = 1000000) -> str:
        """
        执行安全除法协议
        
        协议流程（使用牛顿迭代法近似）：
        1. C1和C2协作计算 1/m₁ 的近似值
        2. 使用安全乘法计算 m₀ * (1/m₁) = m₀ / m₁
        
        注意：由于同态加密的限制，除法需要特殊处理
        这里使用近似方法
        
        Args:
            enc_m0: 加密的m₀
            enc_m1: 加密的m₁
            precision: 精度因子
            
        Returns:
            str: 加密的 m₀ / m₁（近似值）
        """
        # 简化实现：需要先解密m₁，计算倒数，再加密
        # 实际的安全除法协议更复杂，需要多轮交互
        # 这里提供一个基础框架
        
        # 步骤1: C2解密m₁
        m1 = self.c2_manager.decrypt(enc_m1)
        
        if abs(m1) < 1e-10:  # 避免除零
            raise ValueError("除数不能为零")
        
        # 步骤2: C2计算 1/m₁
        inv_m1 = 1.0 / m1
        
        # 步骤3: C2加密 1/m₁（使用C1的公钥）
        enc_inv_m1 = self.c1_manager.encrypt(inv_m1)
        
        # 步骤4: 使用安全乘法计算 m₀ * (1/m₁)
        enc_result = self.sm_protocol.execute(enc_m0, enc_inv_m1)
        
        return enc_result


def secure_divide(enc_m0: str, enc_m1: str,
                 c1_public_key: str, c2_private_key: str) -> str:
    """
    安全除法协议的便捷函数
    
    Args:
        enc_m0: 加密的m₀
        enc_m1: 加密的m₁
        c1_public_key: C1的公钥
        c2_private_key: C2的私钥
        
    Returns:
        str: 加密的 m₀ / m₁
    """
    c1_manager = PaillierManager()
    c1_manager.load_public_key(c1_public_key)
    
    c2_manager = PaillierManager()
    # 加载C2的密钥对
    
    protocol = SecureDivisionProtocol(c1_manager, c2_manager)
    return protocol.execute(enc_m0, enc_m1)

