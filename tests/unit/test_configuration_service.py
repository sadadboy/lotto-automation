# tests/unit/test_configuration_service.py
import pytest
from unittest.mock import Mock, patch
import tempfile
import os

from src.domain.entities.configuration import Configuration
from src.domain.services.configuration_service import ConfigurationService
from src.infrastructure.repositories.file_configuration_repository import FileConfigurationRepository


@pytest.mark.unit
class TestConfigurationService:
    """Configuration Service 단위 테스트"""

    @pytest.fixture
    def mock_repository(self):
        """Mock Repository"""
        return Mock(spec=FileConfigurationRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """ConfigurationService 인스턴스"""
        return ConfigurationService(mock_repository)

    @pytest.fixture
    def sample_configuration(self, sample_user_credentials, sample_purchase_settings, sample_recharge_settings):
        """테스트용 Configuration"""
        return Configuration(
            user_credentials=sample_user_credentials,
            purchase_settings=sample_purchase_settings,
            recharge_settings=sample_recharge_settings
        )

    def test_service_initialization(self, mock_repository):
        """Service 초기화 테스트"""
        service = ConfigurationService(mock_repository)
        assert service.repository == mock_repository

    def test_create_initial_configuration_success(self, service, mock_repository):
        """최초 설정 생성 성공 테스트"""
        # Mock 설정
        mock_repository.exists.return_value = False
        mock_repository.save.return_value = True
        
        user_id = "test_user"
        password = "test_password"
        master_password = "master_123456"
        
        # 실행
        result = service.create_initial_configuration(user_id, password, master_password)
        
        # 검증
        assert result == True
        mock_repository.exists.assert_called_once()
        mock_repository.save.assert_called_once()

    def test_create_initial_configuration_already_exists(self, service, mock_repository):
        """이미 설정이 존재할 때 테스트"""
        # Mock 설정
        mock_repository.exists.return_value = True
        
        # 실행
        with pytest.raises(ValueError, match="설정이 이미 존재합니다"):
            service.create_initial_configuration("user", "pass", "master")
        
        # 검증
        mock_repository.exists.assert_called_once()
        mock_repository.save.assert_not_called()

    def test_load_configuration_success(self, service, mock_repository, sample_configuration):
        """설정 로드 성공 테스트"""
        # Mock 설정
        mock_repository.load.return_value = sample_configuration
        
        master_password = "master_123456"
        
        # 실행
        result = service.load_configuration(master_password)
        
        # 검증
        assert result == sample_configuration
        mock_repository.load.assert_called_once_with(master_password)

    def test_save_configuration_success(self, service, mock_repository, sample_configuration):
        """설정 저장 성공 테스트"""
        # Mock 설정
        mock_repository.save.return_value = True
        
        master_password = "master_123456"
        
        # 실행
        result = service.save_configuration(sample_configuration, master_password)
        
        # 검증
        assert result == True
        mock_repository.save.assert_called_once_with(sample_configuration, master_password)

    def test_update_purchase_settings_success(self, service, mock_repository, sample_configuration):
        """구매 설정 업데이트 성공 테스트"""
        # Mock 설정
        mock_repository.load.return_value = sample_configuration
        mock_repository.save.return_value = True
        
        new_schedule_time = "15:30"
        new_purchase_count = 3
        master_password = "master_123456"
        
        # 실행
        result = service.update_purchase_settings(
            schedule_time=new_schedule_time,
            purchase_count=new_purchase_count,
            master_password=master_password
        )
        
        # 검증
        assert result == True
        mock_repository.load.assert_called_once_with(master_password)
        mock_repository.save.assert_called_once()

    def test_update_recharge_settings_success(self, service, mock_repository, sample_configuration):
        """충전 설정 업데이트 성공 테스트"""
        # Mock 설정
        mock_repository.load.return_value = sample_configuration
        mock_repository.save.return_value = True
        
        new_minimum_balance = 10000
        new_recharge_amount = 100000
        master_password = "master_123456"
        
        # 실행
        result = service.update_recharge_settings(
            minimum_balance=new_minimum_balance,
            recharge_amount=new_recharge_amount,
            master_password=master_password
        )
        
        # 검증
        assert result == True
        mock_repository.load.assert_called_once_with(master_password)
        mock_repository.save.assert_called_once()

    def test_update_discord_settings_success(self, service, mock_repository, sample_configuration):
        """디스코드 설정 업데이트 성공 테스트"""
        # Mock 설정
        mock_repository.load.return_value = sample_configuration
        mock_repository.save.return_value = True
        
        webhook_url = "https://discord.com/api/webhooks/test"
        master_password = "master_123456"
        
        # 실행
        result = service.update_discord_settings(
            webhook_url=webhook_url,
            enable_notifications=True,
            master_password=master_password
        )
        
        # 검증
        assert result == True
        mock_repository.load.assert_called_once_with(master_password)
        mock_repository.save.assert_called_once()

    def test_validate_master_password_success(self, service, mock_repository, sample_configuration):
        """마스터 비밀번호 검증 성공 테스트"""
        # Mock 설정
        mock_repository.load.return_value = sample_configuration
        
        master_password = "master_123456"
        
        # 실행
        result = service.validate_master_password(master_password)
        
        # 검증
        assert result == True
        mock_repository.load.assert_called_once_with(master_password)

    def test_validate_master_password_failure(self, service, mock_repository):
        """마스터 비밀번호 검증 실패 테스트"""
        # Mock 설정 - 복호화 실패
        mock_repository.load.side_effect = ValueError("복호화 실패")
        
        wrong_password = "wrong_password"
        
        # 실행
        result = service.validate_master_password(wrong_password)
        
        # 검증
        assert result == False
        mock_repository.load.assert_called_once_with(wrong_password)

    def test_backup_configuration_success(self, service, mock_repository):
        """설정 백업 성공 테스트"""
        # Mock 설정
        backup_path = "/path/to/backup.json"
        mock_repository.backup.return_value = backup_path
        
        # 실행
        result = service.backup_configuration()
        
        # 검증
        assert result == backup_path
        mock_repository.backup.assert_called_once_with(None)

    def test_backup_configuration_with_suffix(self, service, mock_repository):
        """설정 백업 (접미사 포함) 테스트"""
        # Mock 설정
        backup_suffix = "manual_backup"
        backup_path = f"/path/to/backup_{backup_suffix}.json"
        mock_repository.backup.return_value = backup_path
        
        # 실행
        result = service.backup_configuration(backup_suffix)
        
        # 검증
        assert result == backup_path
        mock_repository.backup.assert_called_once_with(backup_suffix)

    def test_delete_configuration_success(self, service, mock_repository):
        """설정 삭제 성공 테스트"""
        # Mock 설정
        mock_repository.delete.return_value = True
        
        # 실행
        result = service.delete_configuration()
        
        # 검증
        assert result == True
        mock_repository.delete.assert_called_once()

    def test_configuration_exists(self, service, mock_repository):
        """설정 존재 여부 확인 테스트"""
        # Mock 설정
        mock_repository.exists.return_value = True
        
        # 실행
        result = service.configuration_exists()
        
        # 검증
        assert result == True
        mock_repository.exists.assert_called_once()

    def test_get_configuration_summary(self, service, mock_repository, sample_configuration):
        """설정 요약 정보 조회 테스트"""
        # Mock 설정
        mock_repository.load.return_value = sample_configuration
        mock_repository.get_file_path.return_value = "/path/to/config.json"
        
        master_password = "master_123456"
        
        # 실행
        result = service.get_configuration_summary(master_password)
        
        # 검증
        assert isinstance(result, dict)
        assert "user_id_masked" in result
        assert "purchase_schedule" in result
        assert "auto_recharge_enabled" in result
        assert "discord_notifications" in result
        assert "file_path" in result
        
        mock_repository.load.assert_called_once_with(master_password)
        mock_repository.get_file_path.assert_called_once()

    def test_validate_configuration_integrity(self, service, mock_repository):
        """설정 무결성 검증 테스트"""
        # Mock 설정
        mock_repository.validate_file_integrity.return_value = True
        
        # 실행
        result = service.validate_configuration_integrity()
        
        # 검증
        assert result == True
        mock_repository.validate_file_integrity.assert_called_once()

    def test_error_handling_invalid_parameters(self, service):
        """잘못된 매개변수 오류 처리 테스트"""
        # 빈 사용자 ID
        with pytest.raises(ValueError, match="사용자 ID는 필수"):
            service.create_initial_configuration("", "password", "master")
        
        # 짧은 마스터 비밀번호
        with pytest.raises(ValueError, match="마스터 비밀번호는 최소 6자"):
            service.create_initial_configuration("user", "password", "123")
        
        # None 값들
        with pytest.raises(ValueError):
            service.create_initial_configuration(None, "password", "master")
