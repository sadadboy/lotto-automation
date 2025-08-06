# tests/unit/test_configuration.py
import pytest
from unittest.mock import patch, mock_open
from datetime import datetime

from src.domain.entities.configuration import Configuration, DiscordSettings
from src.domain.entities.user_credentials import UserCredentials
from src.domain.entities.purchase_settings import PurchaseSettings
from src.domain.entities.recharge_settings import RechargeSettings


@pytest.mark.unit
class TestConfiguration:
    """Configuration 엔티티 단위 테스트"""

    def test_configuration_creation(self, sample_user_credentials, sample_purchase_settings, sample_recharge_settings):
        """Configuration 엔티티 생성 테스트"""
        config = Configuration(
            user_credentials=sample_user_credentials,
            purchase_settings=sample_purchase_settings,
            recharge_settings=sample_recharge_settings
        )
        
        assert isinstance(config, Configuration)
        assert config.user_credentials.user_id == "test_user"
        assert config.purchase_settings.schedule_time == "14:00"
        assert config.recharge_settings.minimum_balance == 5000

    def test_configuration_validation(self, sample_user_credentials, sample_recharge_settings):
        """Configuration 검증 테스트"""
        # 유효한 설정
        valid_purchase_settings = PurchaseSettings(
            schedule_time="14:00",
            purchase_count=2,
            lotto_list=[
                {"type": "자동", "numbers": []},
                {"type": "수동", "numbers": [1, 2, 3, 4, 5, 6]}
            ]
        )
        
        config = Configuration(
            user_credentials=sample_user_credentials,
            purchase_settings=valid_purchase_settings,
            recharge_settings=sample_recharge_settings
        )
        
        assert config.is_valid() == True
        
        # 무효한 설정 - 잘못된 시간 형식
        with pytest.raises(ValueError, match="잘못된 시간 형식"):
            invalid_purchase_settings = PurchaseSettings(
                schedule_time="25:00",  # 잘못된 시간
                purchase_count=1,
                lotto_list=[]
            )

    def test_configuration_encrypt_decrypt(self, sample_user_credentials, sample_purchase_settings, sample_recharge_settings):
        """Configuration 암호화/복호화 테스트"""
        config = Configuration(
            user_credentials=sample_user_credentials,
            purchase_settings=sample_purchase_settings,
            recharge_settings=sample_recharge_settings
        )
        
        # 암호화
        encrypted_data = config.encrypt_credentials("master_key_123")
        assert isinstance(encrypted_data, dict)
        assert "encrypted_user_id" in encrypted_data
        assert "encrypted_password" in encrypted_data
        
        # 복호화
        decrypted_credentials = config.decrypt_credentials(
            encrypted_data, "master_key_123"
        )
        assert decrypted_credentials.user_id == "test_user"
        assert decrypted_credentials.password == "test_password"

    def test_configuration_to_dict(self, sample_user_credentials, sample_purchase_settings, sample_recharge_settings):
        """Configuration을 dict로 변환 테스트"""
        config = Configuration(
            user_credentials=sample_user_credentials,
            purchase_settings=sample_purchase_settings,
            recharge_settings=sample_recharge_settings
        )
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "purchase" in config_dict
        assert "recharge" in config_dict
        assert "discord" in config_dict
        assert config_dict["purchase"]["schedule_time"] == "14:00"

    def test_configuration_from_dict(self, sample_user_credentials):
        """dict에서 Configuration 생성 테스트"""
        config_data = {
            "purchase": {
                "schedule_time": "14:00",
                "count": 5,
                "lotto_list": [
                    {"type": "자동", "numbers": []},
                    {"type": "수동", "numbers": [1, 2, 3, 4, 5, 6]}
                ]
            },
            "recharge": {
                "auto_recharge": True,
                "minimum_balance": 5000,
                "recharge_amount": 50000
            },
            "discord": {
                "webhook_url": "https://discord.com/api/webhooks/test",
                "enable_notifications": True
            }
        }
        
        config = Configuration.from_dict(config_data, sample_user_credentials)
        
        assert isinstance(config, Configuration)
        assert config.purchase_settings.schedule_time == "14:00"
        assert config.recharge_settings.auto_recharge == True


@pytest.mark.unit
class TestUserCredentials:
    """UserCredentials 엔티티 단위 테스트"""
    
    def test_valid_credentials(self):
        """유효한 인증 정보 테스트"""
        credentials = UserCredentials("test_user", "test_pass")
        assert credentials.user_id == "test_user"
        assert credentials.password == "test_pass"
        assert credentials.is_valid() == True
    
    def test_invalid_credentials(self):
        """무효한 인증 정보 테스트"""
        with pytest.raises(ValueError, match="사용자 ID는 필수"):
            UserCredentials("", "test_pass")
        
        with pytest.raises(ValueError, match="비밀번호는 필수"):
            UserCredentials("test_user", "")
        
        with pytest.raises(ValueError, match="사용자 ID는 최소 3자"):
            UserCredentials("ab", "test_pass")
            
        with pytest.raises(ValueError, match="비밀번호는 최소 4자"):
            UserCredentials("test_user", "123")


@pytest.mark.unit
class TestPurchaseSettings:
    """PurchaseSettings 엔티티 단위 테스트"""
    
    def test_valid_purchase_settings(self):
        """유효한 구매 설정 테스트"""
        settings = PurchaseSettings(
            schedule_time="14:30",
            purchase_count=2,
            lotto_list=[
                {"type": "자동", "numbers": []},
                {"type": "수동", "numbers": [1, 2, 3, 4, 5, 6]}
            ]
        )
        assert settings.is_valid() == True
        assert settings.schedule_time == "14:30"
        assert settings.purchase_count == 2
    
    def test_invalid_time_format(self):
        """잘못된 시간 형식 테스트"""
        with pytest.raises(ValueError, match="잘못된 시간 형식"):
            PurchaseSettings("25:00", 1, [])
    
    def test_invalid_purchase_count(self):
        """잘못된 구매 수량 테스트"""
        with pytest.raises(ValueError, match="구매 수량은 1~5개"):
            PurchaseSettings("14:00", 0, [])
        
        with pytest.raises(ValueError, match="구매 수량은 1~5개"):
            PurchaseSettings("14:00", 6, [])


@pytest.mark.unit  
class TestRechargeSettings:
    """RechargeSettings 엔티티 단위 테스트"""
    
    def test_valid_recharge_settings(self):
        """유효한 충전 설정 테스트"""
        settings = RechargeSettings(
            auto_recharge=True,
            minimum_balance=5000,
            recharge_amount=50000
        )
        assert settings.is_valid() == True
        assert settings.should_recharge(3000) == True
        assert settings.should_recharge(10000) == False
    
    def test_invalid_recharge_settings(self):
        """무효한 충전 설정 테스트"""
        with pytest.raises(ValueError, match="최소 잔액은 0 이상"):
            RechargeSettings(True, -1000, 50000)
        
        with pytest.raises(ValueError, match="충전 금액은 1,000원 이상"):
            RechargeSettings(True, 5000, 500)
        
        with pytest.raises(ValueError, match="최소 잔액이 충전 금액보다 작아야"):
            RechargeSettings(True, 60000, 50000)
