"""
Paillier同态加密管理器
实现密钥生成、加密、解密和基本同态加法操作
"""
import json
from typing import Tuple, Optional
from phe import paillier
import base64


class PaillierManager:
    """
    Paillier同态加密管理器
    提供密钥生成、加密、解密和同态运算功能
    """
    
    def __init__(self, public_key: Optional[paillier.PaillierPublicKey] = None,
                 private_key: Optional[paillier.PaillierPrivateKey] = None):
        """
        初始化Paillier管理器
        
        Args:
            public_key: 公钥对象（可选）
            private_key: 私钥对象（可选）
        """
        self.public_key = public_key
        self.private_key = private_key
    
    @classmethod
    def generate_keypair(cls, key_length: int = 1024) -> Tuple['PaillierManager', dict]:
        """
        生成Paillier密钥对
        
        Args:
            key_length: 密钥长度（默认1024位）
            
        Returns:
            (manager, keypair_dict): 管理器实例和密钥字典
        """
        public_key, private_key = paillier.generate_paillier_keypair(n_length=key_length)
        manager = cls(public_key=public_key, private_key=private_key)
        
        # 序列化密钥对
        keypair_dict = manager.serialize_keypair()
        
        return manager, keypair_dict
    
    def serialize_keypair(self) -> dict:
        """
        序列化密钥对为字典格式
        
        Returns:
            dict: 包含公钥和私钥的字典
        """
        if not self.public_key or not self.private_key:
            raise ValueError("密钥对未初始化")
        
        # 序列化公钥
        public_key_str = self._serialize_public_key(self.public_key)
        
        # 序列化私钥
        private_key_str = self._serialize_private_key(self.private_key)
        
        return {
            'public_key': public_key_str,
            'private_key': private_key_str,
            'key_length': self.public_key.n.bit_length()
        }
    
    def load_keypair(self, keypair_dict: dict):
        """
        从字典加载密钥对
        
        Args:
            keypair_dict: 包含公钥和私钥的字典
        """
        self.public_key = self._deserialize_public_key(keypair_dict['public_key'])
        self.private_key = self._deserialize_private_key(
            keypair_dict['private_key'],
            self.public_key
        )
    
    def load_public_key(self, public_key_str: str):
        """
        仅加载公钥（用于加密操作）
        
        Args:
            public_key_str: 序列化的公钥字符串
        """
        self.public_key = self._deserialize_public_key(public_key_str)
    
    def _serialize_public_key(self, public_key: paillier.PaillierPublicKey) -> str:
        """序列化公钥为字符串"""
        key_data = {
            'n': str(public_key.n),
            'g': str(public_key.g)
        }
        json_str = json.dumps(key_data)
        return base64.b64encode(json_str.encode()).decode()
    
    def _deserialize_public_key(self, public_key_str: str) -> paillier.PaillierPublicKey:
        """从字符串反序列化公钥"""
        json_str = base64.b64decode(public_key_str.encode()).decode()
        key_data = json.loads(json_str)
        n = int(key_data['n'])
        g = int(key_data['g'])
        return paillier.PaillierPublicKey(n=n, g=g)
    
    def _serialize_private_key(self, private_key: paillier.PaillierPrivateKey) -> str:
        """序列化私钥为字符串"""
        key_data = {
            'p': str(private_key.p),
            'q': str(private_key.q)
        }
        json_str = json.dumps(key_data)
        return base64.b64encode(json_str.encode()).decode()
    
    def _deserialize_private_key(self, private_key_str: str,
                                 public_key: paillier.PaillierPublicKey) -> paillier.PaillierPrivateKey:
        """从字符串反序列化私钥"""
        json_str = base64.b64decode(private_key_str.encode()).decode()
        key_data = json.loads(json_str)
        p = int(key_data['p'])
        q = int(key_data['q'])
        return paillier.PaillierPrivateKey(public_key=public_key, p=p, q=q)
    
    def encrypt(self, plaintext: float) -> str:
        """
        加密明文数据
        
        Args:
            plaintext: 要加密的明文（浮点数或整数）
            
        Returns:
            str: 序列化后的密文字符串
        """
        if not self.public_key:
            raise ValueError("公钥未初始化")
        
        # 将浮点数转换为整数（乘以精度因子）
        precision = 1000000  # 保留6位小数精度
        plaintext_int = int(plaintext * precision)
        
        # 加密
        encrypted_number = self.public_key.encrypt(plaintext_int)
        
        # 序列化密文
        return self._serialize_encrypted_number(encrypted_number)
    
    def encrypt_int(self, plaintext: int) -> str:
        """
        加密整数明文
        
        Args:
            plaintext: 要加密的整数
            
        Returns:
            str: 序列化后的密文字符串
        """
        if not self.public_key:
            raise ValueError("公钥未初始化")
        
        encrypted_number = self.public_key.encrypt(plaintext)
        return self._serialize_encrypted_number(encrypted_number)
    
    def decrypt(self, ciphertext: str) -> float:
        """
        解密密文数据
        
        Args:
            ciphertext: 序列化后的密文字符串
            
        Returns:
            float: 解密后的明文
        """
        if not self.private_key:
            raise ValueError("私钥未初始化")
        
        # 反序列化密文
        encrypted_number = self._deserialize_encrypted_number(ciphertext)
        
        # 解密
        plaintext_int = self.private_key.decrypt(encrypted_number)
        
        # 将整数转换回浮点数
        precision = 1000000
        return plaintext_int / precision
    
    def decrypt_int(self, ciphertext: str) -> int:
        """
        解密整数密文
        
        Args:
            ciphertext: 序列化后的密文字符串
            
        Returns:
            int: 解密后的整数
        """
        if not self.private_key:
            raise ValueError("私钥未初始化")
        
        encrypted_number = self._deserialize_encrypted_number(ciphertext)
        return self.private_key.decrypt(encrypted_number)
    
    def _serialize_encrypted_number(self, encrypted_number: paillier.EncryptedNumber) -> str:
        """序列化加密数字为字符串"""
        # 获取密文的字符串表示
        ciphertext_str = str(encrypted_number.ciphertext())
        exponent = encrypted_number.exponent
        
        data = {
            'ciphertext': ciphertext_str,
            'exponent': exponent
        }
        json_str = json.dumps(data)
        return base64.b64encode(json_str.encode()).decode()
    
    def _deserialize_encrypted_number(self, ciphertext_str: str) -> paillier.EncryptedNumber:
        """从字符串反序列化加密数字"""
        json_str = base64.b64decode(ciphertext_str.encode()).decode()
        data = json.loads(json_str)
        ciphertext = int(data['ciphertext'])
        exponent = data['exponent']
        
        return paillier.EncryptedNumber(self.public_key, ciphertext, exponent)
    
    def add(self, ciphertext1: str, ciphertext2: str) -> str:
        """
        同态加法：E(a) + E(b) = E(a + b)
        
        Args:
            ciphertext1: 第一个密文
            ciphertext2: 第二个密文
            
        Returns:
            str: 加密后的和
        """
        if not self.public_key:
            raise ValueError("公钥未初始化")
        
        enc1 = self._deserialize_encrypted_number(ciphertext1)
        enc2 = self._deserialize_encrypted_number(ciphertext2)
        
        # 同态加法
        result = enc1 + enc2
        
        return self._serialize_encrypted_number(result)
    
    def add_plaintext(self, ciphertext: str, plaintext: float) -> str:
        """
        密文与明文相加：E(a) + b = E(a + b)
        
        Args:
            ciphertext: 密文
            plaintext: 明文（浮点数）
            
        Returns:
            str: 加密后的和
        """
        if not self.public_key:
            raise ValueError("公钥未初始化")
        
        enc = self._deserialize_encrypted_number(ciphertext)
        precision = 1000000
        plaintext_int = int(plaintext * precision)
        
        # 密文与明文相加
        result = enc + plaintext_int
        
        return self._serialize_encrypted_number(result)
    
    def multiply_plaintext(self, ciphertext: str, plaintext: float) -> str:
        """
        密文与明文相乘：E(a) * b = E(a * b)
        
        Args:
            ciphertext: 密文
            plaintext: 明文（浮点数）
            
        Returns:
            str: 加密后的乘积
        """
        if not self.public_key:
            raise ValueError("公钥未初始化")
        
        enc = self._deserialize_encrypted_number(ciphertext)
        precision = 1000000
        plaintext_int = int(plaintext * precision)
        
        # 密文与明文相乘
        result = enc * plaintext_int
        
        return self._serialize_encrypted_number(result)
    
    def encrypt_list(self, plaintext_list: list) -> list:
        """
        批量加密列表
        
        Args:
            plaintext_list: 明文列表
            
        Returns:
            list: 密文列表
        """
        return [self.encrypt(item) for item in plaintext_list]
    
    def decrypt_list(self, ciphertext_list: list) -> list:
        """
        批量解密列表
        
        Args:
            ciphertext_list: 密文列表
            
        Returns:
            list: 明文列表
        """
        return [self.decrypt(item) for item in ciphertext_list]

