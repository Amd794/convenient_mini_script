#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件加密/解密工具

这个脚本提供了文件和目录的加密与解密功能，支持多种加密算法，
提供密码保护、文件完整性校验，以及批量处理能力。
可用于保护敏感数据和个人隐私文件。
"""

import argparse
import base64
import getpass
import hashlib
import json
import logging
import os
import random
import string
import sys
import time
from typing import List, Optional, Tuple

# 导入加密所需的库
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:
    print("缺少所需的加密库。请安装：pip install cryptography")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class EncryptionAlgorithm:
    """加密算法枚举"""
    AES = "aes"
    FERNET = "fernet"


class FileEncryptor:
    """
    文件加密/解密工具类
    
    提供对文件和目录的加密和解密功能
    """

    # 加密文件扩展名
    ENCRYPTED_EXTENSION = ".encrypted"
    # 加密元数据文件扩展名
    METADATA_EXTENSION = ".meta"
    # 盐值大小（字节）
    SALT_SIZE = 16
    # 密钥派生迭代次数
    KDF_ITERATIONS = 100000
    # AES块大小（字节）
    AES_BLOCK_SIZE = 16

    def __init__(self,
                 password: str,
                 algorithm: str = EncryptionAlgorithm.FERNET,
                 chunk_size: int = 64 * 1024):
        """
        初始化加密器
        
        Args:
            password: 加密密码
            algorithm: 加密算法 ('aes' 或 'fernet')
            chunk_size: 处理大文件时的块大小（字节）
        """
        self.password = password
        self.algorithm = algorithm.lower()
        self.chunk_size = chunk_size

        if self.algorithm not in [EncryptionAlgorithm.AES, EncryptionAlgorithm.FERNET]:
            raise ValueError(f"不支持的加密算法: {algorithm}")

    def encrypt_file(self,
                     source_path: str,
                     target_path: Optional[str] = None,
                     delete_original: bool = False) -> str:
        """
        加密单个文件
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径（如果为None，则在源文件旁创建加密文件）
            delete_original: 是否删除原始文件
            
        Returns:
            加密后的文件路径
        """
        if not os.path.isfile(source_path):
            raise ValueError(f"源路径不是文件: {source_path}")

        # 如果没有指定目标路径，则在源文件旁创建
        if target_path is None:
            target_path = source_path + self.ENCRYPTED_EXTENSION

        # 生成盐值
        salt = os.urandom(self.SALT_SIZE)

        # 根据算法选择加密方法
        if self.algorithm == EncryptionAlgorithm.FERNET:
            # 生成密钥
            key = self._derive_key(salt)
            # 创建Fernet实例
            fernet = Fernet(base64.urlsafe_b64encode(key))

            # 计算文件哈希值
            file_hash = self._calculate_file_hash(source_path)

            # 对文件进行加密
            with open(source_path, 'rb') as f_in, open(target_path, 'wb') as f_out:
                # 写入盐值
                f_out.write(salt)

                # 分块读取并加密文件
                while True:
                    data = f_in.read(self.chunk_size)
                    if not data:
                        break

                    # 加密数据块
                    encrypted_data = fernet.encrypt(data)
                    f_out.write(len(encrypted_data).to_bytes(4, byteorder='big'))
                    f_out.write(encrypted_data)

        elif self.algorithm == EncryptionAlgorithm.AES:
            # 生成密钥和初始化向量
            key = self._derive_key(salt)
            iv = os.urandom(self.AES_BLOCK_SIZE)

            # 计算文件哈希值
            file_hash = self._calculate_file_hash(source_path)

            # 创建AES加密器
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            with open(source_path, 'rb') as f_in, open(target_path, 'wb') as f_out:
                # 写入盐值和初始化向量
                f_out.write(salt)
                f_out.write(iv)

                # 分块读取并加密文件
                while True:
                    data = f_in.read(self.chunk_size)
                    if not data:
                        break

                    # 确保数据块长度是16字节的倍数（AES要求）
                    if len(data) % self.AES_BLOCK_SIZE != 0:
                        # PKCS7填充
                        padding_length = self.AES_BLOCK_SIZE - (len(data) % self.AES_BLOCK_SIZE)
                        data += bytes([padding_length]) * padding_length

                    # 加密数据块
                    encrypted_data = encryptor.update(data)
                    f_out.write(encrypted_data)

                # 写入最后的加密块
                f_out.write(encryptor.finalize())

        # 创建元数据文件，包含算法、哈希等信息
        metadata_path = target_path + self.METADATA_EXTENSION
        metadata = {
            "algorithm": self.algorithm,
            "original_filename": os.path.basename(source_path),
            "original_size": os.path.getsize(source_path),
            "hash": file_hash,
            "encrypted_time": time.time(),
            "encrypted_size": os.path.getsize(target_path)
        }

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        # 如果需要删除原始文件
        if delete_original:
            self._secure_delete(source_path)

        return target_path

    def decrypt_file(self,
                     source_path: str,
                     target_path: Optional[str] = None,
                     delete_encrypted: bool = False,
                     verify_hash: bool = True) -> str:
        """
        解密文件
        
        Args:
            source_path: 源文件路径（加密文件）
            target_path: 目标文件路径（解密后的文件）
            delete_encrypted: 是否删除加密文件
            verify_hash: 是否验证文件完整性
            
        Returns:
            解密后的文件路径
        """
        if not os.path.isfile(source_path):
            raise ValueError(f"源路径不是文件: {source_path}")

        # 查找元数据文件
        metadata_path = source_path + self.METADATA_EXTENSION
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 使用元数据中的算法
            algorithm = metadata.get("algorithm", self.algorithm)
            original_filename = metadata.get("original_filename")
            original_hash = metadata.get("hash")
        else:
            # 如果没有元数据，使用当前设置的算法
            algorithm = self.algorithm
            original_filename = os.path.basename(source_path)
            if original_filename.endswith(self.ENCRYPTED_EXTENSION):
                original_filename = original_filename[:-len(self.ENCRYPTED_EXTENSION)]
            original_hash = None

        # 如果没有指定目标路径，则在当前目录下恢复原始文件名
        if target_path is None:
            target_dir = os.path.dirname(source_path)
            target_path = os.path.join(target_dir, original_filename)

        try:
            # 读取盐值
            with open(source_path, 'rb') as f:
                salt = f.read(self.SALT_SIZE)

                # 根据算法选择解密方法
                if algorithm == EncryptionAlgorithm.FERNET:
                    # 生成密钥
                    key = self._derive_key(salt)
                    # 创建Fernet实例
                    fernet = Fernet(base64.urlsafe_b64encode(key))

                    with open(target_path, 'wb') as f_out:
                        while True:
                            # 读取块大小
                            size_bytes = f.read(4)
                            if not size_bytes:
                                break

                            # 解析块大小
                            block_size = int.from_bytes(size_bytes, byteorder='big')
                            # 读取加密数据块
                            encrypted_data = f.read(block_size)
                            if not encrypted_data:
                                break

                            # 解密数据块
                            decrypted_data = fernet.decrypt(encrypted_data)
                            f_out.write(decrypted_data)

                elif algorithm == EncryptionAlgorithm.AES:
                    # 读取初始化向量
                    iv = f.read(self.AES_BLOCK_SIZE)

                    # 生成密钥
                    key = self._derive_key(salt)

                    # 创建AES解密器
                    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                    decryptor = cipher.decryptor()

                    # 读取所有加密数据
                    encrypted_data = f.read()

                    # 解密数据
                    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

                    # 处理填充
                    if decrypted_data:
                        # 获取填充长度（PKCS7填充方案）
                        padding_length = decrypted_data[-1]
                        # 去除填充
                        if padding_length > 0 and padding_length <= self.AES_BLOCK_SIZE:
                            # 验证填充
                            if all(b == padding_length for b in decrypted_data[-padding_length:]):
                                decrypted_data = decrypted_data[:-padding_length]

                    # 写入解密后的数据
                    with open(target_path, 'wb') as f_out:
                        f_out.write(decrypted_data)

            # 验证文件哈希
            if verify_hash and original_hash:
                decrypted_hash = self._calculate_file_hash(target_path)
                if decrypted_hash != original_hash:
                    logger.warning(f"文件哈希不匹配，可能已损坏或篡改: {target_path}")
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    raise ValueError("文件完整性验证失败")

            # 如果需要删除加密文件
            if delete_encrypted:
                self._secure_delete(source_path)
                # 删除元数据文件
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)

            return target_path

        except (InvalidToken, ValueError) as e:
            logger.error(f"解密失败: {e}")
            # 如果解密过程中出错，删除可能部分解密的文件
            if os.path.exists(target_path):
                os.remove(target_path)
            raise ValueError(f"解密失败，可能是密码错误或文件已损坏: {e}")

    def encrypt_directory(self,
                          source_dir: str,
                          target_dir: Optional[str] = None,
                          delete_original: bool = False,
                          recursive: bool = True,
                          exclude_patterns: List[str] = None) -> Tuple[int, int]:
        """
        加密目录中的所有文件
        
        Args:
            source_dir: 源目录路径
            target_dir: 目标目录路径（如果为None，则在源目录旁创建加密目录）
            delete_original: 是否删除原始文件
            recursive: 是否递归处理子目录
            exclude_patterns: 要排除的文件模式列表
            
        Returns:
            成功加密的文件数量和失败的文件数量
        """
        if not os.path.isdir(source_dir):
            raise ValueError(f"源路径不是目录: {source_dir}")

        # 规范化源目录路径
        source_dir = os.path.abspath(source_dir)

        # 如果没有指定目标目录，则在源目录旁创建
        if target_dir is None:
            target_dir = source_dir + "_encrypted"

        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)

        # 排除模式
        exclude_patterns = exclude_patterns or []

        success_count = 0
        fail_count = 0

        # 遍历源目录
        for root, dirs, files in os.walk(source_dir):
            # 计算相对路径
            rel_path = os.path.relpath(root, source_dir)

            # 创建对应的目标子目录
            if rel_path != '.':
                target_subdir = os.path.join(target_dir, rel_path)
                os.makedirs(target_subdir, exist_ok=True)
            else:
                target_subdir = target_dir

            # 处理文件
            for file in files:
                # 检查是否排除
                if any(self._match_pattern(file, pattern) for pattern in exclude_patterns):
                    logger.debug(f"跳过排除的文件: {file}")
                    continue

                source_file = os.path.join(root, file)
                target_file = os.path.join(target_subdir, file + self.ENCRYPTED_EXTENSION)

                try:
                    self.encrypt_file(source_file, target_file, delete_original)
                    success_count += 1
                except Exception as e:
                    logger.error(f"加密文件失败 {source_file}: {e}")
                    fail_count += 1

            # 如果不递归处理，则跳出循环
            if not recursive:
                break

        return success_count, fail_count

    def decrypt_directory(self,
                          source_dir: str,
                          target_dir: Optional[str] = None,
                          delete_encrypted: bool = False,
                          verify_hash: bool = True) -> Tuple[int, int]:
        """
        解密目录中的所有加密文件
        
        Args:
            source_dir: 源目录路径（包含加密文件）
            target_dir: 目标目录路径（存放解密后的文件）
            delete_encrypted: 是否删除加密文件
            verify_hash: 是否验证文件完整性
            
        Returns:
            成功解密的文件数量和失败的文件数量
        """
        if not os.path.isdir(source_dir):
            raise ValueError(f"源路径不是目录: {source_dir}")

        # 规范化源目录路径
        source_dir = os.path.abspath(source_dir)

        # 如果没有指定目标目录，则在源目录旁创建
        if target_dir is None:
            if source_dir.endswith("_encrypted"):
                target_dir = source_dir[:-10] + "_decrypted"
            else:
                target_dir = source_dir + "_decrypted"

        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)

        success_count = 0
        fail_count = 0

        # 遍历源目录
        for root, dirs, files in os.walk(source_dir):
            # 计算相对路径
            rel_path = os.path.relpath(root, source_dir)

            # 创建对应的目标子目录
            if rel_path != '.':
                target_subdir = os.path.join(target_dir, rel_path)
                os.makedirs(target_subdir, exist_ok=True)
            else:
                target_subdir = target_dir

            # 过滤加密文件
            encrypted_files = [f for f in files if f.endswith(self.ENCRYPTED_EXTENSION) and
                               not f.endswith(self.METADATA_EXTENSION)]

            # 处理文件
            for file in encrypted_files:
                source_file = os.path.join(root, file)

                # 获取原始文件名（从元数据或者去除扩展名）
                metadata_file = source_file + self.METADATA_EXTENSION
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    original_filename = metadata.get("original_filename")
                else:
                    # 去除加密扩展名
                    original_filename = file[:-len(self.ENCRYPTED_EXTENSION)]

                target_file = os.path.join(target_subdir, original_filename)

                try:
                    self.decrypt_file(source_file, target_file, delete_encrypted, verify_hash)
                    success_count += 1
                except Exception as e:
                    logger.error(f"解密文件失败 {source_file}: {e}")
                    fail_count += 1

        return success_count, fail_count

    def _derive_key(self, salt: bytes) -> bytes:
        """
        从密码和盐值派生密钥
        
        Args:
            salt: 盐值
            
        Returns:
            派生的密钥
        """
        # 使用PBKDF2HMAC从密码派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256位密钥
            salt=salt,
            iterations=self.KDF_ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(self.password.encode())

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件的SHA-256哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            哈希值的十六进制字符串
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(self.chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _secure_delete(self, file_path: str, passes: int = 3) -> None:
        """
        安全删除文件（覆盖内容后删除）
        
        Args:
            file_path: 文件路径
            passes: 覆盖次数
        """
        if not os.path.exists(file_path):
            return

        # 获取文件大小
        file_size = os.path.getsize(file_path)

        try:
            with open(file_path, 'rb+') as f:
                # 多次覆盖文件内容
                for _ in range(passes):
                    # 移动到文件开头
                    f.seek(0)

                    # 覆盖文件内容
                    remaining = file_size
                    while remaining > 0:
                        chunk_size = min(self.chunk_size, remaining)
                        # 生成随机数据
                        if _ == 0:
                            # 第一次用0覆盖
                            data = b'\x00' * chunk_size
                        elif _ == 1:
                            # 第二次用1覆盖
                            data = b'\xff' * chunk_size
                        else:
                            # 最后一次用随机数据覆盖
                            data = os.urandom(chunk_size)

                        f.write(data)
                        remaining -= chunk_size

                    # 刷新写入
                    f.flush()
                    os.fsync(f.fileno())
        except Exception as e:
            logger.warning(f"安全删除文件时出错 {file_path}: {e}")

        # 最后删除文件
        os.remove(file_path)

    def _match_pattern(self, name: str, pattern: str) -> bool:
        """
        检查文件名是否匹配给定模式
        
        Args:
            name: 文件名
            pattern: 匹配模式（支持通配符）
            
        Returns:
            是否匹配
        """
        import fnmatch
        return fnmatch.fnmatch(name, pattern)


def generate_random_password(length: int = 16) -> str:
    """
    生成随机密码
    
    Args:
        length: 密码长度
        
    Returns:
        随机密码
    """
    # 包含字母、数字和特殊字符
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    return ''.join(random.choice(chars) for _ in range(length))


def get_password(prompt: str, confirm: bool = False) -> str:
    """
    安全地获取密码输入
    
    Args:
        prompt: 提示信息
        confirm: 是否需要确认密码
        
    Returns:
        输入的密码
    """
    while True:
        password = getpass.getpass(prompt)

        if not password:
            print("错误: 密码不能为空")
            continue

        if confirm:
            confirm_password = getpass.getpass("再次输入密码以确认: ")
            if password != confirm_password:
                print("错误: 两次密码输入不一致")
                continue

        return password


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="文件加密/解密工具")

    # 操作选择
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--encrypt", action="store_true", help="加密文件或目录")
    group.add_argument("-d", "--decrypt", action="store_true", help="解密文件或目录")
    group.add_argument("-g", "--generate-password", action="store_true", help="生成随机密码")

    # 文件和目录路径
    parser.add_argument("path", nargs="?", help="要处理的文件或目录路径")
    parser.add_argument("-o", "--output", help="输出文件或目录路径")

    # 加密选项
    parser.add_argument("-a", "--algorithm", choices=["aes", "fernet"], default="fernet",
                        help="加密算法 (默认: fernet)")
    parser.add_argument("-p", "--password", help="加密/解密密码 (不推荐在命令行中使用)")
    parser.add_argument("--password-file", help="从文件读取密码")

    # 文件处理选项
    parser.add_argument("--delete", action="store_true", help="处理后删除原始文件")
    parser.add_argument("-r", "--recursive", action="store_true", default=True,
                        help="递归处理子目录（默认启用）")
    parser.add_argument("--no-recursive", action="store_false", dest="recursive",
                        help="不递归处理子目录")
    parser.add_argument("--exclude", nargs="+", help="排除的文件模式列表（如 *.log *.tmp）")
    parser.add_argument("--no-verify", action="store_false", dest="verify",
                        help="解密时不验证文件完整性")

    # 密码生成选项
    parser.add_argument("--length", type=int, default=16,
                        help="生成的随机密码长度（默认: 16）")

    # 输出选项
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，减少输出")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细模式，显示更多信息")

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 配置日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 生成随机密码
    if args.generate_password:
        password = generate_random_password(args.length)
        print(f"生成的随机密码: {password}")
        return 0

    # 检查路径
    if not args.path:
        logger.error("请指定要处理的文件或目录路径")
        return 1

    if not os.path.exists(args.path):
        logger.error(f"指定的路径不存在: {args.path}")
        return 1

    # 获取密码
    password = None
    if args.password:
        # 从命令行参数获取密码（不推荐）
        password = args.password
        logger.warning("在命令行中提供密码是不安全的，请考虑使用交互式输入")
    elif args.password_file:
        # 从文件读取密码
        try:
            with open(args.password_file, 'r') as f:
                password = f.read().strip()
        except Exception as e:
            logger.error(f"从文件读取密码失败: {e}")
            return 1
    else:
        # 交互式输入密码
        try:
            if args.encrypt:
                password = get_password("输入加密密码: ", confirm=True)
            else:
                password = get_password("输入解密密码: ")
        except KeyboardInterrupt:
            print("\n操作已取消")
            return 1

    # 创建加密器
    encryptor = FileEncryptor(
        password=password,
        algorithm=args.algorithm
    )

    try:
        if args.encrypt:
            # 加密操作
            if os.path.isfile(args.path):
                # 加密单个文件
                output_path = encryptor.encrypt_file(
                    source_path=args.path,
                    target_path=args.output,
                    delete_original=args.delete
                )
                logger.info(f"文件已加密: {output_path}")
            else:
                # 加密整个目录
                success, fail = encryptor.encrypt_directory(
                    source_dir=args.path,
                    target_dir=args.output,
                    delete_original=args.delete,
                    recursive=args.recursive,
                    exclude_patterns=args.exclude
                )
                logger.info(f"目录加密完成: 成功 {success} 个文件, 失败 {fail} 个文件")

        else:
            # 解密操作
            if os.path.isfile(args.path):
                # 解密单个文件
                output_path = encryptor.decrypt_file(
                    source_path=args.path,
                    target_path=args.output,
                    delete_encrypted=args.delete,
                    verify_hash=args.verify
                )
                logger.info(f"文件已解密: {output_path}")
            else:
                # 解密整个目录
                success, fail = encryptor.decrypt_directory(
                    source_dir=args.path,
                    target_dir=args.output,
                    delete_encrypted=args.delete,
                    verify_hash=args.verify
                )
                logger.info(f"目录解密完成: 成功 {success} 个文件, 失败 {fail} 个文件")

        return 0

    except Exception as e:
        logger.error(f"处理过程中出错: {e}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n操作已被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序出错: {e}")
        sys.exit(2)
