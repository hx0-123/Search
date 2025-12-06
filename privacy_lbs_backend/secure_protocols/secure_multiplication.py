"""
安全乘法协议 (Secure Multiplication, SM)
实现 Epk(m₀ · m₁) = SM(Epk(m₀), Epk(m₁))
需要C1和C2协作执行
"""
from typing import Tuple
from crypto.paillier_manager import PaillierManager
import random


class SecureMultiplicationProtocol:
    """
    安全乘法协议
    实现两个密文的乘法运算，需要两个云服务器C1和C2协作
    """
    
    def __init__(self, c1_manager: PaillierManager, c2_manager: PaillierManager):
        """
        初始化安全乘法协议
        
        Args:
            c1_manager: C1服务器的Paillier管理器（只有公钥）
            c2_manager: C2服务器的Paillier管理器（有私钥）
        """
        self.c1_manager = c1_manager
        self.c2_manager = c2_manager
    
    def execute(self, enc_m0: str, enc_m1: str) -> str:
        """
        执行安全乘法协议
        
        协议流程：
        1. C1生成随机数r，计算 Epk(m₀) * Epk(r) = Epk(m₀ + r)
        2. C1发送 Epk(m₀ + r) 给C2
        3. C2解密得到 (m₀ + r)，计算 (m₀ + r) * Epk(m₁) = Epk((m₀ + r) * m₁)
        4. C2发送 Epk((m₀ + r) * m₁) 给C1
        5. C1计算 Epk((m₀ + r) * m₁) - Epk(r * m₁) = Epk(m₀ * m₁)
        
        Args:
            enc_m0: 加密的m₀
            enc_m1: 加密的m₁
            
        Returns:
            str: 加密的 m₀ * m₁
        """
        # 步骤1: C1生成随机数r
        r = random.randint(1, 1000000)  # 随机整数
        
        # 步骤2: C1计算 Epk(m₀ + r)
        enc_r = self.c1_manager.encrypt_int(r)
        enc_m0_plus_r = self.c1_manager.add(enc_m0, enc_r)
        
        # 步骤3: C2解密得到 (m₀ + r)
        m0_plus_r = self.c2_manager.decrypt_int(enc_m0_plus_r)
        
        # 步骤4: C2计算 Epk((m₀ + r) * m₁)
        # 注意：这里需要将m0_plus_r转换为浮点数进行同态乘法
        # 但由于Paillier支持密文与整数相乘，我们可以直接使用
        # C2需要使用C1的公钥进行加密操作
        enc_result = self.c1_manager.multiply_plaintext(enc_m1, float(m0_plus_r))
        
        # 步骤5: C1计算 Epk((m₀ + r) * m₁) - Epk(r * m₁)
        enc_r_times_m1 = self.c1_manager.multiply_plaintext(enc_m1, float(r))
        
        # 计算 Epk((m₀ + r) * m₁ - r * m₁) = Epk(m₀ * m₁)
        # 由于是同态运算，我们需要使用负数的加密形式
        # Epk(-r * m₁) = Epk(0) - Epk(r * m₁)
        enc_zero = self.c1_manager.encrypt_int(0)
        enc_neg_r_times_m1 = self.c1_manager.add(enc_zero, enc_r_times_m1)
        
        # 实际上，我们需要使用更精确的方法
        # 由于Paillier支持密文与负数相乘，我们可以：
        enc_neg_r_times_m1 = self.c1_manager.multiply_plaintext(enc_m1, float(-r))
        
        # 最终结果
        enc_m0_times_m1 = self.c1_manager.add(enc_result, enc_neg_r_times_m1)
        
        return enc_m0_times_m1


def secure_multiply(enc_m0: str, enc_m1: str, 
                   c1_public_key: str, c2_private_key: str) -> str:
    """
    安全乘法协议的便捷函数
    
    Args:
        enc_m0: 加密的m₀
        enc_m1: 加密的m₁
        c1_public_key: C1的公钥（序列化字符串）
        c2_private_key: C2的私钥（序列化字符串，包含公钥信息）
        
    Returns:
        str: 加密的 m₀ * m₁
    """
    # 初始化C1管理器（只有公钥）
    c1_manager = PaillierManager()
    c1_manager.load_public_key(c1_public_key)
    
    # 初始化C2管理器（有私钥）
    c2_manager = PaillierManager()
    # 需要从私钥字符串中提取公钥信息
    # 这里假设私钥字符串包含完整的密钥对信息
    # 实际实现中需要根据序列化格式调整
    
    protocol = SecureMultiplicationProtocol(c1_manager, c2_manager)
    return protocol.execute(enc_m0, enc_m1)

