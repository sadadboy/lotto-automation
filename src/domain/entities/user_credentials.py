# src/domain/entities/user_credentials.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class UserCredentials:
    """사용자 인증 정보 엔티티"""
    
    user_id: str
    password: str
    
    def __post_init__(self):
        """생성 후 검증"""
        self._validate()
    
    def _validate(self):
        """사용자 인증 정보 검증"""
        if not self.user_id or not self.user_id.strip():
            raise ValueError("사용자 ID는 필수입니다.")
        
        if not self.password or not self.password.strip():
            raise ValueError("비밀번호는 필수입니다.")
        
        if len(self.user_id.strip()) < 3:
            raise ValueError("사용자 ID는 최소 3자 이상이어야 합니다.")
        
        if len(self.password.strip()) < 4:
            raise ValueError("비밀번호는 최소 4자 이상이어야 합니다.")
    
    def is_valid(self) -> bool:
        """인증 정보가 유효한지 확인"""
        try:
            self._validate()
            return True
        except ValueError:
            return False
    
    def mask_sensitive_data(self) -> dict:
        """민감한 데이터를 마스킹하여 반환"""
        return {
            "user_id": self.user_id[:2] + "*" * (len(self.user_id) - 2),
            "password": "*" * len(self.password)
        }
