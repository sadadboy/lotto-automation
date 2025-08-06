# tests/integration/test_configuration_integration.py
import pytest
import tempfile
import os
from pathlib import Path

from src.domain.entities.configuration import Configuration
from src.domain.services.configuration_service import ConfigurationService
from src.application.usecases.configuration_usecase import ConfigurationUseCase
from src.infrastructure.repositories.file_configuration_repository import FileConfigurationRepository


@pytest.mark.integration
class TestConfigurationIntegration:
    """Configuration 시스템 통합 테스트
    
    모든 레이어(Entity, Service, UseCase, Repository)가 
    함께 작동하는지 확인하는 통합 테스트입니다.
    """

    @pytest.fixture
    def temp_config_dir(self):
        """임시 설정 디렉토리"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def repository(self, temp_config_dir):
        """FileConfigurationRepository 인스턴스"""
        config_file = os.path.join(temp_config_dir, "lotto_config.json")
        return FileConfigurationRepository(config_file)

    @pytest.fixture
    def service(self, repository):
        """ConfigurationService 인스턴스"""
        return ConfigurationService(repository)

    @pytest.fixture
    def usecase(self, service):
        """ConfigurationUseCase 인스턴스"""
        return ConfigurationUseCase(service)

    def test_complete_configuration_workflow(self, usecase, temp_config_dir):
        """완전한 설정 관리 워크플로우 테스트"""
        
        # 1. 최초 설정 생성
        setup_data = {
            "user_id": "integration_test_user",
            "password": "integration_test_password",
            "master_password": "master_password_123456",
            "schedule_time": "15:30",
            "purchase_count": 3,
            "auto_recharge": True,
            "minimum_balance": 10000,
            "recharge_amount": 100000,
            "discord_webhook": "https://discord.com/api/webhooks/integration_test"
        }
        
        # 최초 설정 생성
        result = usecase.setup_initial_configuration(setup_data)
        assert result["success"] == True, f"설정 생성 실패: {result.get('error')}"
        assert "integration_test_user" in result["data"]["user_id_masked"]
        
        # 2. 설정 상태 확인
        status = usecase.get_configuration_status()
        assert status["exists"] == True
        assert status["integrity_valid"] == True
        assert status["status"] == "healthy"
        
        # 3. 마스터 비밀번호 검증
        password_check = usecase.validate_master_password("master_password_123456")
        assert password_check["valid"] == True
        
        wrong_password_check = usecase.validate_master_password("wrong_password")
        assert wrong_password_check["valid"] == False
        
        # 4. 대시보드 데이터 조회
        dashboard_data = usecase.get_configuration_dashboard_data("master_password_123456")
        assert dashboard_data["success"] == True
        assert dashboard_data["data"]["purchase_schedule"] == "15:30"
        assert dashboard_data["data"]["purchase_count"] == 3
        assert dashboard_data["data"]["auto_recharge_enabled"] == True
        assert dashboard_data["data"]["minimum_balance"] == 10000
        
        # 5. 구매 설정 업데이트
        purchase_update = {
            "schedule_time": "16:00",
            "purchase_count": 5,
            "lotto_list": [
                {"type": "자동", "numbers": []},
                {"type": "수동", "numbers": [1, 2, 3, 4, 5, 6]},
                {"type": "반자동", "numbers": [7, 8, 9]},
                {"type": "AI추천", "numbers": []},
                {"type": "통계분석", "numbers": []}
            ]
        }
        
        update_result = usecase.update_purchase_configuration(
            purchase_update, "master_password_123456"
        )
        assert update_result["success"] == True
        
        # 6. 업데이트된 설정 확인
        updated_dashboard = usecase.get_configuration_dashboard_data("master_password_123456")
        assert updated_dashboard["data"]["purchase_schedule"] == "16:00"
        assert updated_dashboard["data"]["purchase_count"] == 5
        
        # 7. 충전 설정 업데이트
        recharge_update = {
            "auto_recharge": False,
            "minimum_balance": 3000,
            "recharge_amount": 30000
        }
        
        recharge_result = usecase.update_recharge_configuration(
            recharge_update, "master_password_123456"
        )
        assert recharge_result["success"] == True
        
        # 8. 디스코드 설정 업데이트
        discord_update = {
            "webhook_url": "https://discord.com/api/webhooks/updated",
            "enable_notifications": False
        }
        
        discord_result = usecase.update_discord_configuration(
            discord_update, "master_password_123456"
        )
        assert discord_result["success"] == True
        
        # 9. 설정 백업
        backup_result = usecase.backup_configuration("integration_test_backup")
        assert backup_result["success"] == True
        assert os.path.exists(backup_result["backup_path"])
        
        # 10. 설정 상태 체크
        health_check = usecase.get_configuration_health_check("master_password_123456")
        assert health_check["healthy"] == True
        assert health_check["exists"] == True
        assert health_check["integrity_valid"] == True
        assert health_check["configuration_valid"] == True
        
        # 11. 설정 초기화 (백업 포함)
        reset_result = usecase.reset_configuration(create_backup=True)
        assert reset_result["success"] == True
        assert "backup_created" in reset_result
        
        # 12. 초기화 후 상태 확인
        final_status = usecase.get_configuration_status()
        assert final_status["exists"] == False

    def test_error_handling_workflow(self, usecase):
        """오류 처리 워크플로우 테스트"""
        
        # 1. 설정이 없을 때 대시보드 데이터 조회
        dashboard_result = usecase.get_configuration_dashboard_data("any_password")
        assert dashboard_result["success"] == False
        assert "설정이 존재하지 않습니다" in dashboard_result["error"]
        
        # 2. 잘못된 설정 데이터로 최초 설정 시도
        invalid_setup = {
            "user_id": "",  # 빈 사용자 ID
            "password": "test_password",
            "master_password": "123"  # 너무 짧은 비밀번호
        }
        
        result = usecase.setup_initial_configuration(invalid_setup)
        assert result["success"] == False
        assert "필수 필드" in result["error"]
        
        # 3. 유효한 설정 생성
        valid_setup = {
            "user_id": "test_user",
            "password": "test_password",
            "master_password": "valid_master_123456"
        }
        
        setup_result = usecase.setup_initial_configuration(valid_setup)
        assert setup_result["success"] == True
        
        # 4. 중복 설정 생성 시도
        duplicate_result = usecase.setup_initial_configuration(valid_setup)
        assert duplicate_result["success"] == False
        assert "이미 설정이 존재합니다" in duplicate_result["error"]
        
        # 5. 잘못된 비밀번호로 업데이트 시도
        update_result = usecase.update_purchase_configuration(
            {"schedule_time": "14:00"}, "wrong_password"
        )
        assert update_result["success"] == False

    def test_repository_layer_directly(self, repository, sample_user_credentials, 
                                     sample_purchase_settings, sample_recharge_settings):
        """Repository 레이어 직접 테스트"""
        
        # Configuration 객체 생성
        configuration = Configuration(
            user_credentials=sample_user_credentials,
            purchase_settings=sample_purchase_settings,
            recharge_settings=sample_recharge_settings
        )
        
        master_password = "repository_test_123456"
        
        # 1. 저장
        save_result = repository.save(configuration, master_password)
        assert save_result == True
        assert repository.exists() == True
        
        # 2. 로드
        loaded_config = repository.load(master_password)
        assert isinstance(loaded_config, Configuration)
        assert loaded_config.user_credentials.user_id == sample_user_credentials.user_id
        assert loaded_config.purchase_settings.schedule_time == sample_purchase_settings.schedule_time
        
        # 3. 무결성 검증
        integrity = repository.validate_file_integrity()
        assert integrity == True
        
        # 4. 백업
        backup_path = repository.backup("direct_test")
        assert backup_path is not None
        assert os.path.exists(backup_path)
        
        # 5. 삭제
        delete_result = repository.delete()
        assert delete_result == True
        assert repository.exists() == False

    def test_service_layer_directly(self, service):
        """Service 레이어 직접 테스트"""
        
        master_password = "service_test_123456"
        
        # 1. 최초 설정 생성
        create_result = service.create_initial_configuration(
            user_id="service_test_user",
            password="service_test_password",
            master_password=master_password
        )
        assert create_result == True
        
        # 2. 설정 로드
        configuration = service.load_configuration(master_password)
        assert isinstance(configuration, Configuration)
        assert configuration.user_credentials.user_id == "service_test_user"
        
        # 3. 구매 설정 업데이트
        purchase_update_result = service.update_purchase_settings(
            master_password=master_password,
            schedule_time="17:30",
            purchase_count=4
        )
        assert purchase_update_result == True
        
        # 4. 업데이트 확인
        updated_config = service.load_configuration(master_password)
        assert updated_config.purchase_settings.schedule_time == "17:30"
        assert updated_config.purchase_settings.purchase_count == 4
        
        # 5. 설정 요약 조회
        summary = service.get_configuration_summary(master_password)
        assert "user_id_masked" in summary
        assert summary["purchase_schedule"] == "17:30"
        assert summary["purchase_count"] == 4

    def test_entity_validation_integration(self):
        """엔티티 검증 통합 테스트"""
        
        from src.domain.entities.user_credentials import UserCredentials
        from src.domain.entities.purchase_settings import PurchaseSettings
        from src.domain.entities.recharge_settings import RechargeSettings
        
        # 1. 유효한 엔티티들 생성
        credentials = UserCredentials("valid_user", "valid_password")
        purchase = PurchaseSettings("14:00", 2, [
            {"type": "자동", "numbers": []},
            {"type": "수동", "numbers": [1, 2, 3, 4, 5, 6]}
        ])
        recharge = RechargeSettings(True, 5000, 50000)
        
        # 2. Configuration 생성
        config = Configuration(
            user_credentials=credentials,
            purchase_settings=purchase,
            recharge_settings=recharge
        )
        
        assert config.is_valid() == True
        
        # 3. 딕셔너리 변환
        config_dict = config.to_dict()
        assert "purchase" in config_dict
        assert "recharge" in config_dict
        
        # 4. 딕셔너리에서 다시 생성
        recreated_config = Configuration.from_dict(config_dict, credentials)
        assert recreated_config.is_valid() == True
        assert recreated_config.purchase_settings.schedule_time == "14:00"
