# src/domain/entities/configuration.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .user_credentials import UserCredentials
from .purchase_settings import PurchaseSettings
from .recharge_settings import RechargeSettings


@dataclass
class DiscordSettings:
    """디스코드 알림 설정"""
    webhook_url: str = ""
    enable_notifications: bool = True
    
    def is_valid(self) -> bool:
        """설정이 유효한지 확인"""
        if self.enable_notifications and not self.webhook_url:
            return False
        return True
    
    def to_dict(self) -> dict:
        return {
            "webhook_url": self.webhook_url,
            "enable_notifications": self.enable_notifications
        }


@dataclass
class Configuration:
    """메인 설정 엔티티"""
    
    user_credentials: UserCredentials
    purchase_settings: PurchaseSettings
    recharge_settings: RechargeSettings = field(default_factory=RechargeSettings.default)
    discord_settings: DiscordSettings = field(default_factory=DiscordSettings)
    
    def __post_init__(self):
        """생성 후 검증"""
        self._validate()
    
    def _validate(self):
        """전체 설정 검증"""
        if not isinstance(self.user_credentials, UserCredentials):
            raise ValueError("user_credentials는 UserCredentials 타입이어야 합니다.")
        
        if not isinstance(self.purchase_settings, PurchaseSettings):
            raise ValueError("purchase_settings는 PurchaseSettings 타입이어야 합니다.")
        
        if not isinstance(self.recharge_settings, RechargeSettings):
            raise ValueError("recharge_settings는 RechargeSettings 타입이어야 합니다.")
        
        if not isinstance(self.discord_settings, DiscordSettings):
            raise ValueError("discord_settings는 DiscordSettings 타입이어야 합니다.")
    
    def is_valid(self) -> bool:
        """전체 설정이 유효한지 확인"""
        try:
            self._validate()
            return (self.user_credentials.is_valid() and 
                   self.purchase_settings.is_valid() and 
                   self.recharge_settings.is_valid() and
                   self.discord_settings.is_valid())
        except (ValueError, TypeError):
            return False
    
    def _generate_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """패스워드에서 암호화 키 생성"""
        if salt is None:
            salt = b'lotto_salt_2024'  # 고정 salt (실제로는 랜덤 생성 권장)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_credentials(self, master_password: str) -> Dict[str, str]:
        """사용자 인증 정보 암호화"""
        key = self._generate_key_from_password(master_password)
        fernet = Fernet(key)
        
        encrypted_user_id = fernet.encrypt(self.user_credentials.user_id.encode())
        encrypted_password = fernet.encrypt(self.user_credentials.password.encode())
        
        return {
            "encrypted_user_id": base64.urlsafe_b64encode(encrypted_user_id).decode(),
            "encrypted_password": base64.urlsafe_b64encode(encrypted_password).decode()
        }
    
    def decrypt_credentials(self, encrypted_data: Dict[str, str], master_password: str) -> UserCredentials:
        """사용자 인증 정보 복호화"""
        key = self._generate_key_from_password(master_password)
        fernet = Fernet(key)
        
        encrypted_user_id = base64.urlsafe_b64decode(encrypted_data["encrypted_user_id"])
        encrypted_password = base64.urlsafe_b64decode(encrypted_data["encrypted_password"])
        
        user_id = fernet.decrypt(encrypted_user_id).decode()
        password = fernet.decrypt(encrypted_password).decode()
        
        return UserCredentials(user_id=user_id, password=password)
    
    def to_dict(self, include_credentials: bool = False) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        config_dict = {
            "purchase": self.purchase_settings.to_dict(),
            "recharge": self.recharge_settings.to_dict(),
            "discord": self.discord_settings.to_dict()
        }
        
        if include_credentials:
            config_dict["credentials"] = {
                "user_id": self.user_credentials.user_id,
                "password": self.user_credentials.password
            }
        
        return config_dict
    
    @classmethod
    def create_default(cls) -> 'Configuration':
        """기본 설정으로 Configuration 생성"""
        return cls(
            user_credentials=UserCredentials("", ""),
            purchase_settings=PurchaseSettings("14:00", 1),
            recharge_settings=RechargeSettings.default(),
            discord_settings=DiscordSettings()
        )
    
    @classmethod
    def from_dict_simple(cls, data: Dict[str, Any]) -> 'Configuration':
        """단순 딕셔너리에서 Configuration 생성 (호환성용)"""
        # 기존 설정 파일 형식 지원
        user_creds = UserCredentials(
            user_id=data.get('login', {}).get('user_id', '') or data.get('user_credentials', {}).get('user_id', ''),
            password=data.get('login', {}).get('password', '') or data.get('user_credentials', {}).get('password', '')
        )
        
        purchase_data = data.get('purchase', {}) or data.get('purchase_settings', {})
        purchase_settings = PurchaseSettings(
            schedule_time=purchase_data.get('schedule_time', '14:00'),
            purchase_count=purchase_data.get('count', purchase_data.get('games_per_purchase', 1)),
            lotto_list=purchase_data.get('lotto_list', [])
        )
        
        payment_data = data.get('payment', {}) or data.get('recharge_settings', {})
        recharge_settings = RechargeSettings(
            auto_recharge=payment_data.get('auto_recharge', True),
            minimum_balance=payment_data.get('min_balance', payment_data.get('minimum_balance', 5000)),
            recharge_amount=payment_data.get('recharge_amount', 50000)
        )
        
        discord_data = data.get('discord', {}) or data.get('discord_settings', {})
        discord_settings = DiscordSettings(
            webhook_url=discord_data.get('webhook_url', ''),
            enable_notifications=discord_data.get('enable_notifications', True)
        )
        
        return cls(
            user_credentials=user_creds,
            purchase_settings=purchase_settings,
            recharge_settings=recharge_settings,
            discord_settings=discord_settings
        )
    
    def to_dict_compatible(self) -> Dict[str, Any]:
        """기존 설정 파일 형식과 호환되는 딕셔너리 반환"""
        return {
            'user_credentials': {
                'user_id': self.user_credentials.user_id,
                'password': self.user_credentials.password
            },
            'purchase_settings': {
                'games_per_purchase': self.purchase_settings.purchase_count,
                'max_amount_per_game': 1000,
                'purchase_method': 'auto',
                'number_selection_method': 'mixed'
            },
            'payment': {
                'auto_recharge': self.recharge_settings.auto_recharge,
                'recharge_amount': self.recharge_settings.recharge_amount,
                'min_balance': self.recharge_settings.minimum_balance,
                'recharge_method': 'account_transfer'
            }
        }
        """딕셔너리에서 Configuration 생성"""
        purchase_data = data.get("purchase", {})
        purchase_settings = PurchaseSettings(
            schedule_time=purchase_data.get("schedule_time", "14:00"),
            purchase_count=purchase_data.get("count", 1),
            lotto_list=purchase_data.get("lotto_list", [])
        )
        
        recharge_data = data.get("recharge", {})
        recharge_settings = RechargeSettings(
            auto_recharge=recharge_data.get("auto_recharge", True),
            minimum_balance=recharge_data.get("minimum_balance", 5000),
            recharge_amount=recharge_data.get("recharge_amount", 50000)
        )
        
        discord_data = data.get("discord", {})
        discord_settings = DiscordSettings(
            webhook_url=discord_data.get("webhook_url", ""),
            enable_notifications=discord_data.get("enable_notifications", True)
        )
        
        return cls(
            user_credentials=user_credentials,
            purchase_settings=purchase_settings,
            recharge_settings=recharge_settings,
            discord_settings=discord_settings
        )
    
    def save_to_file(self, file_path: str, master_password: str):
        """설정을 파일로 저장 (인증 정보는 암호화)"""
        config_data = self.to_dict(include_credentials=False)
        config_data["encrypted_credentials"] = self.encrypt_credentials(master_password)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str, master_password: str) -> 'Configuration':
        """파일에서 설정 로드 (인증 정보 복호화)"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        encrypted_credentials = data.get("encrypted_credentials", {})
        
        # 임시 Configuration 객체 생성하여 복호화 메서드 사용
        temp_credentials = UserCredentials("temp", "temp")
        temp_config = cls(
            user_credentials=temp_credentials,
            purchase_settings=PurchaseSettings("14:00", 1),
            recharge_settings=RechargeSettings.default()
        )
        
        # 실제 인증 정보 복호화
        user_credentials = temp_config.decrypt_credentials(encrypted_credentials, master_password)
        
        return cls.from_dict(data, user_credentials)
    
    @classmethod
    def create_default(cls) -> 'Configuration':
        """기본 설정으로 Configuration 생성"""
        return cls(
            user_credentials=UserCredentials("", ""),
            purchase_settings=PurchaseSettings("14:00", 1),
            recharge_settings=RechargeSettings.default(),
            discord_settings=DiscordSettings()
        )
    
    @classmethod
    def from_dict_simple(cls, data: Dict[str, Any]) -> 'Configuration':
        """단순 딕셔너리에서 Configuration 생성 (호훈성용)"""
        # 기존 설정 파일 형식 지원
        user_creds = UserCredentials(
            user_id=data.get('login', {}).get('user_id', '') or data.get('user_credentials', {}).get('user_id', ''),
            password=data.get('login', {}).get('password', '') or data.get('user_credentials', {}).get('password', '')
        )
        
        purchase_data = data.get('purchase', {}) or data.get('purchase_settings', {})
        purchase_settings = PurchaseSettings(
            schedule_time=purchase_data.get('schedule_time', '14:00'),
            purchase_count=purchase_data.get('count', purchase_data.get('games_per_purchase', 1)),
            lotto_list=purchase_data.get('lotto_list', [])
        )
        
        payment_data = data.get('payment', {}) or data.get('recharge_settings', {})
        recharge_settings = RechargeSettings(
            auto_recharge=payment_data.get('auto_recharge', True),
            minimum_balance=payment_data.get('min_balance', payment_data.get('minimum_balance', 5000)),
            recharge_amount=payment_data.get('recharge_amount', 50000)
        )
        
        discord_data = data.get('discord', {}) or data.get('discord_settings', {})
        discord_settings = DiscordSettings(
            webhook_url=discord_data.get('webhook_url', ''),
            enable_notifications=discord_data.get('enable_notifications', True)
        )
        
        return cls(
            user_credentials=user_creds,
            purchase_settings=purchase_settings,
            recharge_settings=recharge_settings,
            discord_settings=discord_settings
        )
    
    def to_dict_compatible(self) -> Dict[str, Any]:
        """기존 설정 파일 형식과 호훈되는 딕셔너리 반환"""
        return {
            'user_credentials': {
                'user_id': self.user_credentials.user_id,
                'password': self.user_credentials.password
            },
            'purchase_settings': {
                'games_per_purchase': self.purchase_settings.purchase_count,
                'max_amount_per_game': 1000,
                'purchase_method': 'auto',
                'number_selection_method': 'mixed'
            },
            'payment': {
                'auto_recharge': self.recharge_settings.auto_recharge,
                'recharge_amount': self.recharge_settings.recharge_amount,
                'min_balance': self.recharge_settings.minimum_balance,
                'recharge_method': 'account_transfer'
            }
        }
