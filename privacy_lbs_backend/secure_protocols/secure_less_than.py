"""
安全小于计算协议 (Secure Less Than, SLESS)
实现 SLESS(Epk(m₁), Epk(m₂)) = Epk(Bool(m₁ < m₂))
需要C1和C2协作执行
"""
from typing import Tuple
from crypto.paillier_manager import PaillierManager
import random


class SecureLessThanProtocol:
    """
    安全小于比较协议
    判断两个密文的大小关系，返回加密的布尔值
    """
    
    def __init__(self, c1_manager: PaillierManager, c2_manager: PaillierManager):
        """
        初始化安全小于协议
        
        Args:
            c1_manager: C1服务器的Paillier管理器（只有公钥）
            c2_manager: C2服务器的Paillier管理器（有私钥）
        """
        self.c1_manager = c1_manager
        self.c2_manager = c2_manager
    
    def execute(self, enc_m1: str, enc_m2: str) -> str:
        """
        执行安全小于比较协议
        
        协议流程（简化版）：
        1. C1计算 Epk(m₁ - m₂) = Epk(m₁) - Epk(m₂)
        2. C1生成随机数r，计算 Epk(m₁ - m₂ + r)
        3. C1发送给C2
        4. C2解密得到 (m₁ - m₂ + r)，判断符号
        5. C2返回加密的布尔结果给C1
        6. C1根据r调整结果
        
        更安全的实现：
        1. C1计算 Epk(m₁ - m₂)
        2. C1生成随机数r，计算 Epk(m₁ - m₂ + r)
        3. C2解密并判断 (m₁ - m₂ + r) 的符号
        4. C2返回加密的布尔值
        5. C1根据r的符号调整结果
        
        Args:
            enc_m1: 加密的m₁
            enc_m2: 加密的m₂
            
        Returns:
            str: 加密的布尔值，1表示m₁ < m₂，0表示m₁ >= m₂
        """
        # 步骤1: C1计算 Epk(m₁ - m₂) = Epk(m₁) + Epk(-m₂)
        enc_neg_m2 = self.c1_manager.multiply_plaintext(enc_m2, -1.0)
        enc_diff = self.c1_manager.add(enc_m1, enc_neg_m2)
        
        # 步骤2: C1生成随机数r（正数）
        r = random.randint(1, 1000000)
        enc_r = self.c1_manager.encrypt_int(r)
        enc_diff_plus_r = self.c1_manager.add(enc_diff, enc_r)
        
        # 步骤3: C2解密得到 (m₁ - m₂ + r)
        diff_plus_r = self.c2_manager.decrypt_int(enc_diff_plus_r)
        
        # 步骤4: C2判断 (m₁ - m₂ + r) 的符号
        # 如果 diff_plus_r < r，说明 m₁ - m₂ < 0，即 m₁ < m₂
        # 如果 diff_plus_r >= r，说明 m₁ - m₂ >= 0，即 m₁ >= m₂
        result_bool = 1 if diff_plus_r < r else 0
        
        # 步骤5: C2返回加密的布尔结果（使用C1的公钥）
        enc_result = self.c1_manager.encrypt_int(result_bool)
        
        return enc_result


def secure_less_than(enc_m1: str, enc_m2: str,
                    c1_public_key: str, c2_private_key: str) -> str:
    """
    安全小于比较协议的便捷函数
    
    Args:
        enc_m1: 加密的m₁
        enc_m2: 加密的m₂
        c1_public_key: C1的公钥（序列化字符串）
        c2_private_key: C2的私钥（序列化字符串）
        
    Returns:
        str: 加密的布尔值，1表示m₁ < m₂，0表示m₁ >= m₂
    """
    c1_manager = PaillierManager()
    c1_manager.load_public_key(c1_public_key)
    
    c2_manager = PaillierManager()
    # 加载C2的密钥对（包含公钥和私钥）
    
    protocol = SecureLessThanProtocol(c1_manager, c2_manager)
    return protocol.execute(enc_m1, enc_m2)

