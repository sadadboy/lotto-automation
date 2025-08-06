# tests/unit/test_configuration_usecase.py
import pytest
from unittest.mock import Mock, patch
import tempfile

from src.application.usecases.configuration_usecase import ConfigurationUseCase
from src.domain.services.configuration_service import ConfigurationService
from src.domain.entities.configuration import Configuration


@pytest.mark.unit
class TestConfigurationUseCase:
    """Configuration UseCase 단위 테스트"""

    @pytest.fixture
    def mock_service(self):
        """Mock ConfigurationService"""
        return Mock(spec=ConfigurationService)

    @pytest.fixture
    def usecase(self, mock_service):
        """ConfigurationUseCase 인스턴스"""
        return ConfigurationUseCase(mock_service)

    @pytest.fixture
    def sample_configuration(self, sample_user_credentials, sample_purchase_settings, sample_recharge_settings):
        """테스트용 Configuration"""
        return Configuration(
            user_credentials=sample_user_credentials,
            purchase_settings=sample_purchase_settings,
            recharge_settings=sample_recharge_settings
        )

    def test_setup_initial_configuration_success(self, usecase, mock_service):
        """최초 설정 구성 성공 테스트"""
        # Mock 설정
        mock_service.configuration_exists.return_value = False
        mock_service.create_initial_configuration.return_value = True
        
        setup_data = {
            "user_id": "test_user",
            "password": "test_password",
            "master_password": "master_123456",
            "schedule_time": "14:00",
            "purchase_count": 3,
            "auto_recharge": True,
            "minimum_balance": 5000,
            "recharge_amount": 50000,
            "discord_webhook": "https://discord.com/api/webhooks/test"
        }
        
        # 실행
        result = usecase.setup_initial_configuration(setup_data)
        
        # 검증
        assert result["success"] == True
        assert "message" in result
        mock_service.configuration_exists.assert_called_once()
        mock_service.create_initial_configuration.assert_called_once()

    def test_setup_initial_configuration_already_exists(self, usecase, mock_service):
        """이미 설정이 존재할 때 테스트"""
        # Mock 설정
        mock_service.configuration_exists.return_value = True
        
        setup_data = {
            "user_id": "test_user",
            "password": "test_password",
            "master_password": "master_123456"
        }
        
        # 실행
        result = usecase.setup_initial_configuration(setup_data)
        
        # 검증
        assert result["success"] == False
        assert "이미 설정이 존재합니다" in result["error"]
        mock_service.configuration_exists.assert_called_once()

    def test_get_configuration_dashboard_data_success(self, usecase, mock_service, sample_configuration):
        """대시보드 데이터 조회 성공 테스트"""
        # Mock 설정
        mock_summary = {
            "user_id_masked": "te***",
            "purchase_schedule": "14:00",
            "purchase_count": 3,
            "auto_recharge_enabled": True,
            "minimum_balance": 5000,
            "discord_notifications": True
        }
        mock_service.get_configuration_summary.return_value = mock_summary
        mock_service.configuration_exists.return_value = True
        mock_service.validate_configuration_integrity.return_value = True
        
        master_password = "master_123456"
        
        # 실행
        result = usecase.get_configuration_dashboard_data(master_password)
        
        # 검증
        assert result["success"] == True
        assert result["data"] == mock_summary
        assert result["exists"] == True
        assert result["integrity_valid"] == True
        mock_service.get_configuration_summary.assert_called_once_with(master_password)

    def test_update_purchase_configuration_success(self, usecase, mock_service):
        """구매 설정 업데이트 성공 테스트"""
        # Mock 설정
        mock_service.update_purchase_settings.return_value = True
        
        update_data = {
            "schedule_time": "15:30",
            "purchase_count": 4,
            "lotto_list": [
                {"type": "자동", "numbers": []},
                {"type": "수동", "numbers": [1, 2, 3, 4, 5, 6]}
            ]
        }
        master_password = "master_123456"
        
        # 실행
        result = usecase.update_purchase_configuration(update_data, master_password)
        
        # 검증
        assert result["success"] == True
        mock_service.update_purchase_settings.assert_called_once()

    def test_update_recharge_configuration_success(self, usecase, mock_service):
        """충전 설정 업데이트 성공 테스트"""
        # Mock 설정
        mock_service.update_recharge_settings.return_value = True
        
        update_data = {
            "auto_recharge": False,
            "minimum_balance": 10000,
            "recharge_amount": 100000
        }
        master_password = "master_123456"
        
        # 실행
        result = usecase.update_recharge_configuration(update_data, master_password)
        
        # 검증
        assert result["success"] == True
        mock_service.update_recharge_settings.assert_called_once()

    def test_update_discord_configuration_success(self, usecase, mock_service):
        """디스코드 설정 업데이트 성공 테스트"""
        # Mock 설정
        mock_service.update_discord_settings.return_value = True
        
        update_data = {
            "webhook_url": "https://discord.com/api/webhooks/new",
            "enable_notifications": False
        }
        master_password = "master_123456"
        
        # 실행
        result = usecase.update_discord_configuration(update_data, master_password)
        
        # 검증
        assert result["success"] == True
        mock_service.update_discord_settings.assert_called_once()

    def test_validate_master_password_success(self, usecase, mock_service):
        """마스터 비밀번호 검증 성공 테스트"""
        # Mock 설정
        mock_service.validate_master_password.return_value = True
        
        master_password = "master_123456"
        
        # 실행
        result = usecase.validate_master_password(master_password)
        
        # 검증
        assert result["valid"] == True
        mock_service.validate_master_password.assert_called_once_with(master_password)

    def test_validate_master_password_failure(self, usecase, mock_service):
        """마스터 비밀번호 검증 실패 테스트"""
        # Mock 설정
        mock_service.validate_master_password.return_value = False
        
        wrong_password = "wrong_password"
        
        # 실행
        result = usecase.validate_master_password(wrong_password)
        
        # 검증
        assert result["valid"] == False
        mock_service.validate_master_password.assert_called_once_with(wrong_password)

    def test_backup_configuration_success(self, usecase, mock_service):
        """설정 백업 성공 테스트"""
        # Mock 설정
        backup_path = "/path/to/backup.json"
        mock_service.backup_configuration.return_value = backup_path
        
        # 실행
        result = usecase.backup_configuration()
        
        # 검증
        assert result["success"] == True
        assert result["backup_path"] == backup_path
        mock_service.backup_configuration.assert_called_once_with(None)

    def test_backup_configuration_with_name(self, usecase, mock_service):
        """이름 지정 백업 테스트"""
        # Mock 설정
        backup_name = "manual_backup"
        backup_path = f"/path/to/backup_{backup_name}.json"
        mock_service.backup_configuration.return_value = backup_path
        
        # 실행
        result = usecase.backup_configuration(backup_name)
        
        # 검증
        assert result["success"] == True
        assert result["backup_path"] == backup_path
        mock_service.backup_configuration.assert_called_once_with(backup_name)

    def test_reset_configuration_success(self, usecase, mock_service):
        """설정 초기화 성공 테스트"""
        # Mock 설정
        mock_service.backup_configuration.return_value = "/path/to/backup.json"
        mock_service.delete_configuration.return_value = True
        
        # 실행
        result = usecase.reset_configuration(create_backup=True)
        
        # 검증
        assert result["success"] == True
        assert "backup_created" in result
        mock_service.backup_configuration.assert_called_once()
        mock_service.delete_configuration.assert_called_once()

    def test_reset_configuration_no_backup(self, usecase, mock_service):
        """백업 없이 설정 초기화 테스트"""
        # Mock 설정
        mock_service.delete_configuration.return_value = True
        
        # 실행
        result = usecase.reset_configuration(create_backup=False)
        
        # 검증
        assert result["success"] == True
        assert "backup_created" not in result
        mock_service.backup_configuration.assert_not_called()
        mock_service.delete_configuration.assert_called_once()

    def test_get_configuration_status(self, usecase, mock_service):
        """설정 상태 조회 테스트"""
        # Mock 설정
        mock_service.configuration_exists.return_value = True
        mock_service.validate_configuration_integrity.return_value = True
        
        # 실행
        result = usecase.get_configuration_status()
        
        # 검증
        assert result["exists"] == True
        assert result["integrity_valid"] == True
        mock_service.configuration_exists.assert_called_once()
        mock_service.validate_configuration_integrity.assert_called_once()

    def test_error_handling_invalid_setup_data(self, usecase, mock_service):
        """잘못된 설정 데이터 오류 처리 테스트"""
        # Mock 설정
        mock_service.configuration_exists.return_value = False
        
        # 필수 필드 누락
        invalid_data = {
            "user_id": "test_user",
            # password 누락
            "master_password": "master_123456"
        }
        
        # 실행
        result = usecase.setup_initial_configuration(invalid_data)
        
        # 검증
        assert result["success"] == False
        assert "필수 필드" in result["error"]

    def test_error_handling_service_failure(self, usecase, mock_service):
        """서비스 레이어 실패 오류 처리 테스트"""
        # Mock 설정 - 서비스에서 예외 발생
        mock_service.configuration_exists.return_value = False
        mock_service.create_initial_configuration.side_effect = ValueError("서비스 오류")
        
        setup_data = {
            "user_id": "test_user",
            "password": "test_password", 
            "master_password": "master_123456"
        }
        
        # 실행
        result = usecase.setup_initial_configuration(setup_data)
        
        # 검증
        assert result["success"] == False
        assert "서비스 오류" in result["error"]

    def test_get_configuration_health_check(self, usecase, mock_service):
        """설정 상태 체크 테스트"""
        # Mock 설정
        mock_service.configuration_exists.return_value = True
        mock_service.validate_configuration_integrity.return_value = True
        mock_summary = {
            "user_id_masked": "te***",
            "configuration_valid": True
        }
        mock_service.get_configuration_summary.return_value = mock_summary
        
        master_password = "master_123456"
        
        # 실행
        result = usecase.get_configuration_health_check(master_password)
        
        # 검증
        assert result["healthy"] == True
        assert result["exists"] == True
        assert result["integrity_valid"] == True
        assert result["configuration_valid"] == True
