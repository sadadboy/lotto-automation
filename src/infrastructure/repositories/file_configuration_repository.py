# src/infrastructure/repositories/file_configuration_repository.py
import os
import json
import shutil
import threading
from datetime import datetime
from typing import Optional
from pathlib import Path

from src.domain.repositories.configuration_repository import ConfigurationRepository
from src.domain.entities.configuration import Configuration


class FileConfigurationRepository(ConfigurationRepository):
    """파일 기반 Configuration Repository 구현체
    
    JSON 파일을 사용하여 설정을 저장하고 로드하는 Repository 구현체입니다.
    사용자 인증 정보는 암호화되어 저장됩니다.
    """

    def __init__(self, file_path: str = "config/lotto_config.json"):
        """Repository 초기화
        
        Args:
            file_path: 설정 파일 경로
        """
        self.file_path = Path(file_path)
        self._lock = threading.Lock()  # 스레드 안전성을 위한 락
        
        # 디렉토리가 없으면 생성
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, configuration: Configuration, master_password: str) -> bool:
        """설정을 JSON 파일로 저장
        
        Args:
            configuration: 저장할 설정 객체
            master_password: 암호화에 사용할 마스터 비밀번호
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            with self._lock:
                # 설정 검증
                if not configuration.is_valid():
                    raise ValueError("유효하지 않은 설정입니다.")
                
                if not master_password or len(master_password.strip()) < 6:
                    raise ValueError("마스터 비밀번호는 최소 6자 이상이어야 합니다.")
                
                # 설정을 딕셔너리로 변환
                config_data = configuration.to_dict(include_credentials=False)
                
                # 인증 정보 암호화 추가
                config_data["encrypted_credentials"] = configuration.encrypt_credentials(master_password)
                
                # 메타데이터 추가
                config_data["metadata"] = {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "encrypted": True
                }
                
                # 임시 파일에 먼저 저장 (원자적 쓰기)
                temp_file = self.file_path.with_suffix('.tmp')
                
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                
                # 임시 파일을 실제 파일로 이동 (원자적 연산)
                shutil.move(str(temp_file), str(self.file_path))
                
                return True
                
        except (ValueError, TypeError, PermissionError, OSError) as e:
            # 임시 파일 정리
            temp_file = self.file_path.with_suffix('.tmp')
            if temp_file.exists():
                temp_file.unlink()
            
            print(f"설정 저장 실패: {e}")
            return False

    def load(self, master_password: str) -> Configuration:
        """JSON 파일에서 설정 로드
        
        Args:
            master_password: 복호화에 사용할 마스터 비밀번호
            
        Returns:
            Configuration: 로드된 설정 객체
            
        Raises:
            FileNotFoundError: 설정 파일이 존재하지 않음
            ValueError: 잘못된 비밀번호 또는 손상된 파일
        """
        with self._lock:
            if not self.exists():
                raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {self.file_path}")
            
            if not master_password or len(master_password.strip()) < 6:
                raise ValueError("마스터 비밀번호는 최소 6자 이상이어야 합니다.")
            
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 파일 무결성 검증
                if not self._validate_config_data(config_data):
                    raise ValueError("설정 파일이 손상되었습니다.")
                
                # 인증 정보 복호화
                encrypted_credentials = config_data.get("encrypted_credentials", {})
                if not encrypted_credentials:
                    raise ValueError("암호화된 인증 정보를 찾을 수 없습니다.")
                
                # 임시 Configuration 객체로 복호화 수행
                from src.domain.entities.user_credentials import UserCredentials
                from src.domain.entities.purchase_settings import PurchaseSettings
                from src.domain.entities.recharge_settings import RechargeSettings
                
                temp_credentials = UserCredentials("temp", "temp_pass")
                temp_config = Configuration(
                    user_credentials=temp_credentials,
                    purchase_settings=PurchaseSettings("14:00", 1),
                    recharge_settings=RechargeSettings.default()
                )
                
                # 실제 인증 정보 복호화
                user_credentials = temp_config.decrypt_credentials(encrypted_credentials, master_password)
                
                # 전체 Configuration 객체 생성
                configuration = Configuration.from_dict(config_data, user_credentials)
                
                return configuration
                
            except json.JSONDecodeError:
                raise ValueError("설정 파일 형식이 올바르지 않습니다.")
            except Exception as e:
                raise ValueError(f"설정 로드 실패: {str(e)}")

    def exists(self) -> bool:
        """설정 파일 존재 여부 확인"""
        return self.file_path.exists() and self.file_path.is_file()

    def delete(self) -> bool:
        """설정 파일 삭제"""
        try:
            with self._lock:
                if self.exists():
                    self.file_path.unlink()
                return True
        except (PermissionError, OSError) as e:
            print(f"설정 파일 삭제 실패: {e}")
            return False

    def backup(self, backup_suffix: Optional[str] = None) -> Optional[str]:
        """설정 파일 백업"""
        try:
            with self._lock:
                if not self.exists():
                    return None
                
                if backup_suffix is None:
                    backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                backup_path = self.file_path.with_suffix(f'.backup_{backup_suffix}.json')
                shutil.copy2(str(self.file_path), str(backup_path))
                
                return str(backup_path)
                
        except (PermissionError, OSError) as e:
            print(f"설정 파일 백업 실패: {e}")
            return None

    def get_file_path(self) -> str:
        """설정 파일 경로 반환"""
        return str(self.file_path.absolute())

    def validate_file_integrity(self) -> bool:
        """설정 파일 무결성 검증"""
        try:
            if not self.exists():
                return False
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return self._validate_config_data(config_data)
            
        except (json.JSONDecodeError, PermissionError, OSError):
            return False

    def _validate_config_data(self, config_data: dict) -> bool:
        """설정 데이터 구조 검증"""
        required_keys = ["purchase", "recharge", "encrypted_credentials"]
        
        if not isinstance(config_data, dict):
            return False
        
        for key in required_keys:
            if key not in config_data:
                return False
        
        # 암호화된 인증 정보 검증
        encrypted_creds = config_data.get("encrypted_credentials", {})
        if not isinstance(encrypted_creds, dict):
            return False
        
        cred_keys = ["encrypted_user_id", "encrypted_password"]
        for key in cred_keys:
            if key not in encrypted_creds:
                return False
        
        return True
