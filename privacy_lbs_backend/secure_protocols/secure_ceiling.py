"""
安全向上取整协议 (Secure Ceiling, SCEIL)
实现 [Epk(a)] → Epk([a])
对应论文中的算法2
需要C1和C2协作执行
"""
from crypto.paillier_manager import PaillierManager
import random


class SecureCeilingProtocol:
    """
    安全向上取整协议
    对应论文中的算法2：SCEIL
    """
    
    def __init__(self, c1_manager: PaillierManager, c2_manager: PaillierManager):
        """
        初始化安全向上取整协议
        
        Args:
            c1_manager: C1服务器的Paillier管理器（只有公钥）
            c2_manager: C2服务器的Paillier管理器（有私钥）
        """
        self.c1_manager = c1_manager
        self.c2_manager = c2_manager
    
    def execute(self, enc_a: str) -> str:
        """
        执行安全向上取整协议
        
        算法2: SCEIL
        输入: C1持有 Epk(a)
        输出: Epk([a])  (向上取整)
        
        协议流程：
        1. C1生成随机整数 r ∈ Z，计算 Epk(r)
        2. C1计算 Epk(a) + Epk(r) = Epk(a + r)，发送给C2
        3. C2解密得到 b' = Dsk(Epk(a + r)) = a + r
        4. C2计算 [b']（向上取整），发送给C1
        5. C1计算 Epk([b']) - Epk(r) = Epk([a + r] - r)
           注意：这里需要调整，因为 [a + r] - r 不一定等于 [a]
           实际应该：Epk([a + r]) - Epk(r) = Epk([a + r] - r)
           但我们需要 Epk([a])，所以需要特殊处理
        
        修正后的协议：
        1. C1生成随机整数 r ∈ Z
        2. C1计算 Epk(a + r)，发送给C2
        3. C2解密得到 a + r，计算 [a + r]，加密得到 Epk([a + r])
        4. C1计算 Epk([a + r]) - Epk(r) = Epk([a + r] - r)
           由于 [a + r] = [a] + r（对于整数r），所以 [a + r] - r = [a]
        
        Args:
            enc_a: 加密的a
            
        Returns:
            str: 加密的 [a]（向上取整）
        """
        # 步骤1: C1生成随机整数 r
        r = random.randint(1, 1000000)
        enc_r = self.c1_manager.encrypt_int(r)
        
        # 步骤2: C1计算 Epk(a + r)
        enc_a_plus_r = self.c1_manager.add(enc_a, enc_r)
        
        # 步骤3: C2解密得到 a + r
        a_plus_r = self.c2_manager.decrypt(enc_a_plus_r)
        
        # 步骤4: C2计算 [a + r]（向上取整）
        import math
        ceil_a_plus_r = math.ceil(a_plus_r)
        
        # C2加密 [a + r]（使用C1的公钥）
        enc_ceil_a_plus_r = self.c1_manager.encrypt_int(int(ceil_a_plus_r))
        
        # 步骤5: C1计算 Epk([a + r]) - Epk(r) = Epk([a + r] - r)
        # 由于 [a + r] = [a] + r（对于整数r），所以结果是 Epk([a])
        enc_neg_r = self.c1_manager.multiply_plaintext(enc_r, -1.0)
        enc_result = self.c1_manager.add(enc_ceil_a_plus_r, enc_neg_r)
        
        return enc_result


def secure_ceiling(enc_a: str, c1_public_key: str, c2_private_key: str) -> str:
    """
    安全向上取整协议的便捷函数
    
    Args:
        enc_a: 加密的a
        c1_public_key: C1的公钥
        c2_private_key: C2的私钥
        
    Returns:
        str: 加密的 [a]（向上取整）
    """
    c1_manager = PaillierManager()
    c1_manager.load_public_key(c1_public_key)
    
    c2_manager = PaillierManager()
    # 加载C2的密钥对
    
    protocol = SecureCeilingProtocol(c1_manager, c2_manager)
    return protocol.execute(enc_a)

