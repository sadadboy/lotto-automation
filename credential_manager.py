#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인증정보 암호화 저장 관리자
"""
import os
import json
import base64
import getpass
from typing import Optional, Dict
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class UserCredentials:
    """사용자 인증 정보"""
    user_id: str
    password: str
    recharge_password: str = ""  # 충전 비밀번호 (6자리)


class CredentialEncryption:
    """인증정보 암호화 처리"""
    
    def __init__(self, master_password: str, salt: Optional[bytes] = None):
        self.salt = salt or os.urandom(16)
        self.key = self._derive_key(master_password.encode(), self.salt)
        self.fernet = Fernet(self.key)
    
    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """패스워드에서 키 유도"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt(self, data: str) -> str:
        """데이터 암호화"""
        encrypted = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """데이터 복호화"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.fernet.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    def get_salt(self) -> str:
        """Salt 값 반환 (저장용)"""
        return base64.urlsafe_b64encode(self.salt).decode()


class CredentialManager:
    """인증정보 관리자"""
    
    def __init__(self, credentials_file: str = "credentials.enc"):
        self.credentials_file = credentials_file
        self.encryption = None
        
    def _get_master_password(self, prompt: str = "마스터 패스워드: ") -> str:
        """마스터 패스워드 입력받기 (환경변수 우선)"""
        import os
        
        # 1. 환경변수에서 먼저 확인
        env_password = os.getenv('LOTTO_MASTER_PASSWORD')
        if env_password:
            print("✅ 환경변수에서 마스터 패스워드 로드")
            return env_password
        
        # 2. Docker secrets 확인 (/run/secrets/master_password)
        secrets_path = '/run/secrets/master_password'
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, 'r') as f:
                    password = f.read().strip()
                    if password:
                        print("✅ Docker secrets에서 마스터 패스워드 로드")
                        return password
            except Exception as e:
                print(f"⚠️ Docker secrets 읽기 실패: {e}")
        
        # 3. 인터랙티브 입력 (로컬 개발용)
        return getpass.getpass(prompt)
    
    def _init_encryption(self, master_password: str):
        """암호화 서비스 초기화"""
        if self.encryption:
            return
        
        salt = self._load_salt()
        self.encryption = CredentialEncryption(master_password, salt)
    
    def _load_salt(self) -> Optional[bytes]:
        """파일에서 salt 로드"""
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'salt' in data:
                        return base64.urlsafe_b64decode(data['salt'].encode())
            except Exception:
                pass
        return None
    
    def save_credentials(self, credentials: UserCredentials, master_password: str = None) -> bool:
        """인증정보 암호화 저장"""
        try:
            if not master_password:
                master_password = self._get_master_password("저장용 마스터 패스워드 설정: ")
            
            self._init_encryption(master_password)
            
            # 인증 정보를 JSON으로 직렬화
            credentials_data = {
                'user_id': credentials.user_id,
                'password': credentials.password,
                'recharge_password': credentials.recharge_password
            }
            credentials_json = json.dumps(credentials_data)
            
            # 암호화
            encrypted_credentials = self.encryption.encrypt(credentials_json)
            
            # 저장할 데이터 구성
            save_data = {
                'encrypted_credentials': encrypted_credentials,
                'salt': self.encryption.get_salt(),
                'version': '1.0',
                'created_at': str(os.path.getctime(self.credentials_file)) if os.path.exists(self.credentials_file) else None
            }
            
            # 파일에 저장
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            # 파일 권한 설정 (Unix 계열에서만)
            if os.name == 'posix':
                os.chmod(self.credentials_file, 0o600)
            
            print(f"✅ 인증정보가 암호화되어 저장되었습니다: {self.credentials_file}")
            return True
            
        except Exception as e:
            print(f"❌ 인증정보 저장 실패: {e}")
            return False
    
    def load_credentials(self, master_password: str = None) -> Optional[UserCredentials]:
        """인증정보 복호화 로드"""
        if not self.has_credentials():
            return None
        
        try:
            if not master_password:
                master_password = self._get_master_password("인증정보 로드용 마스터 패스워드: ")
            
            self._init_encryption(master_password)
            
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            encrypted_credentials = data.get('encrypted_credentials')
            if not encrypted_credentials:
                print("❌ 암호화된 인증정보가 없습니다.")
                return None
            
            # 복호화
            credentials_json = self.encryption.decrypt(encrypted_credentials)
            credentials_data = json.loads(credentials_json)
            
            return UserCredentials(
                user_id=credentials_data['user_id'],
                password=credentials_data['password'],
                recharge_password=credentials_data.get('recharge_password', '')
            )
            
        except Exception as e:
            print(f"❌ 인증정보 로드 실패: {e}")
            print("마스터 패스워드가 틀렸거나 파일이 손상되었을 수 있습니다.")
            return None
    
    def has_credentials(self) -> bool:
        """인증정보 파일 존재 여부"""
        return os.path.exists(self.credentials_file)
    
    def delete_credentials(self) -> bool:
        """인증정보 파일 삭제"""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
                print(f"✅ 인증정보 파일이 삭제되었습니다: {self.credentials_file}")
            return True
        except Exception as e:
            print(f"❌ 인증정보 삭제 실패: {e}")
            return False
    
    def setup_credentials(self, force_new: bool = False) -> Optional[UserCredentials]:
        """인증정보 설정 (신규 또는 업데이트)"""
        
        if not force_new and self.has_credentials():
            print("\n📋 기존 인증정보가 존재합니다.")
            choice = input("기존 정보를 사용하시겠습니까? (y/N): ").strip().lower()
            
            if choice in ['y', 'yes']:
                return self.load_credentials()
        
        print("\n=== 로또 자동구매 인증정보 설정 ===")
        
        try:
            # 사용자 입력
            user_id = input("로또 사이트 아이디: ").strip()
            if not user_id:
                print("❌ 아이디를 입력해주세요.")
                return None
            
            password = getpass.getpass("로또 사이트 비밀번호: ").strip()
            if not password:
                print("❌ 비밀번호를 입력해주세요.")
                return None
            
            recharge_password = getpass.getpass("충전 비밀번호 (6자리, 선택사항): ").strip()
            if recharge_password and len(recharge_password) != 6:
                print("⚠️ 충전 비밀번호는 6자리여야 합니다. 빈 값으로 저장됩니다.")
                recharge_password = ""
            
            credentials = UserCredentials(
                user_id=user_id,
                password=password,
                recharge_password=recharge_password
            )
            
            # 저장 여부 확인
            save_choice = input("\n인증정보를 암호화하여 저장하시겠습니까? (Y/n): ").strip().lower()
            if save_choice not in ['n', 'no']:
                if self.save_credentials(credentials):
                    print("✅ 인증정보 설정이 완료되었습니다.")
                else:
                    print("⚠️ 저장에 실패했지만 이번 세션에서는 사용할 수 있습니다.")
            
            return credentials
            
        except KeyboardInterrupt:
            print("\n❌ 사용자가 취소했습니다.")
            return None
        except Exception as e:
            print(f"❌ 인증정보 설정 중 오류: {e}")
            return None
    
    def update_credentials(self) -> bool:
        """기존 인증정보 업데이트"""
        print("\n=== 인증정보 업데이트 ===")
        credentials = self.setup_credentials(force_new=True)
        return credentials is not None
    
    def test_credentials_file(self) -> bool:
        """인증정보 파일 테스트"""
        if not self.has_credentials():
            print("❌ 인증정보 파일이 없습니다.")
            return False
        
        print("🔍 인증정보 파일 테스트 중...")
        credentials = self.load_credentials()
        
        if credentials:
            print("✅ 인증정보 파일 정상 - 로드 성공")
            print(f"   사용자: {credentials.user_id}")
            print(f"   충전비밀번호: {'설정됨' if credentials.recharge_password else '미설정'}")
            return True
        else:
            print("❌ 인증정보 파일 손상 또는 마스터 패스워드 불일치")
            return False


def main():
    """테스트용 메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='인증정보 관리자')
    parser.add_argument('--setup', action='store_true', help='인증정보 설정')
    parser.add_argument('--update', action='store_true', help='인증정보 업데이트')
    parser.add_argument('--test', action='store_true', help='인증정보 테스트')
    parser.add_argument('--delete', action='store_true', help='인증정보 삭제')
    parser.add_argument('--file', default='credentials.enc', help='인증정보 파일 경로')
    
    args = parser.parse_args()
    
    manager = CredentialManager(args.file)
    
    if args.setup:
        manager.setup_credentials()
    elif args.update:
        manager.update_credentials()
    elif args.test:
        manager.test_credentials_file()
    elif args.delete:
        confirm = input("정말로 인증정보를 삭제하시겠습니까? (yes): ").strip()
        if confirm == 'yes':
            manager.delete_credentials()
        else:
            print("❌ 삭제가 취소되었습니다.")
    else:
        print("❌ 옵션을 선택해주세요: --setup, --update, --test, --delete")


if __name__ == "__main__":
    main()
