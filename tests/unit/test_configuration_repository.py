# tests/unit/test_configuration_repository.py
import pytest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os
import json

from src.domain.entities.configuration import Configuration
from src.domain.repositories.configuration_repository import ConfigurationRepository
from src.infrastructure.repositories.file_configuration_repository import FileConfigurationRepository


@pytest.mark.unit
class TestConfigurationRepositoryInterface:
    """Configuration Repository 인터페이스 테스트"""

    def test_repository_interface_methods(self):
        """Repository 인터페이스가 필요한 메서드들을 가지고 있는지 테스트"""
        # ConfigurationRepository는 추상 베이스 클래스여야 함
        assert hasattr(ConfigurationRepository, 'save')
        assert hasattr(ConfigurationRepository, 'load')
        assert hasattr(ConfigurationRepository, 'exists')
        assert hasattr(ConfigurationRepository, 'delete')
        assert hasattr(ConfigurationRepository, 'backup')


@pytest.mark.unit
class TestFileConfigurationRepository:
    """File Configuration Repository 구현체 테스트"""

    @pytest.fixture
    def temp_config_file(self):
        """임시 설정 파일 생성"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            yield f.name
        # 테스트 후 정리
        if os.path.exists(f.name):
            os.unlink(f.name)

    @pytest.fixture
    def repository(self, temp_config_file):
        """FileConfigurationRepository 인스턴스"""
        return FileConfigurationRepository(temp_config_file)

    @pytest.fixture
    def sample_configuration(self, sample_user_credentials, sample_purchase_settings, sample_recharge_settings):
        """테스트용 Configuration"""
        return Configuration(
            user_credentials=sample_user_credentials,
            purchase_settings=sample_purchase_settings,
            recharge_settings=sample_recharge_settings
        )

    def test_save_configuration_success(self, repository, sample_configuration, temp_config_file):
        """설정 저장 성공 테스트"""
        master_password = "test_master_123"
        
        # 저장 실행
        result = repository.save(sample_configuration, master_password)
        
        # 결과 검증
        assert result == True
        assert os.path.exists(temp_config_file)
        
        # 파일 내용 검증
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert "purchase" in saved_data
        assert "recharge" in saved_data
        assert "encrypted_credentials" in saved_data
        assert "encrypted_user_id" in saved_data["encrypted_credentials"]

    def test_load_configuration_success(self, repository, sample_configuration, temp_config_file):
        """설정 로드 성공 테스트"""
        master_password = "test_master_123"
        
        # 먼저 저장
        repository.save(sample_configuration, master_password)
        
        # 로드 실행
        loaded_config = repository.load(master_password)
        
        # 결과 검증
        assert isinstance(loaded_config, Configuration)
        assert loaded_config.user_credentials.user_id == sample_configuration.user_credentials.user_id
        assert loaded_config.purchase_settings.schedule_time == sample_configuration.purchase_settings.schedule_time
        assert loaded_config.recharge_settings.auto_recharge == sample_configuration.recharge_settings.auto_recharge

    def test_load_configuration_file_not_exists(self, repository):
        """설정 파일이 없을 때 로드 테스트"""
        with pytest.raises(FileNotFoundError):
            repository.load("any_password")

    def test_load_configuration_wrong_password(self, repository, sample_configuration):
        """잘못된 비밀번호로 로드 테스트"""
        # 올바른 비밀번호로 저장
        repository.save(sample_configuration, "correct_password")
        
        # 잘못된 비밀번호로 로드 시도
        with pytest.raises(Exception):  # 복호화 실패 예외
            repository.load("wrong_password")

    def test_exists_configuration(self, repository, sample_configuration, temp_config_file):
        """설정 파일 존재 여부 테스트"""
        # 파일이 없을 때
        assert repository.exists() == False
        
        # 파일이 있을 때
        repository.save(sample_configuration, "test_password")
        assert repository.exists() == True

    def test_delete_configuration(self, repository, sample_configuration, temp_config_file):
        """설정 파일 삭제 테스트"""
        # 파일 생성
        repository.save(sample_configuration, "test_password")
        assert repository.exists() == True
        
        # 삭제 실행
        result = repository.delete()
        
        # 결과 검증
        assert result == True
        assert repository.exists() == False

    def test_backup_configuration(self, repository, sample_configuration, temp_config_file):
        """설정 파일 백업 테스트"""
        # 원본 파일 생성
        repository.save(sample_configuration, "test_password")
        
        # 백업 실행
        backup_path = repository.backup()
        
        # 결과 검증
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path != temp_config_file
        
        # 백업 파일 내용 검증
        with open(temp_config_file, 'r') as original:
            original_content = original.read()
        with open(backup_path, 'r') as backup:
            backup_content = backup.read()
        
        assert original_content == backup_content
        
        # 백업 파일 정리
        os.unlink(backup_path)

    def test_save_configuration_permission_error(self, repository, sample_configuration):
        """파일 저장 권한 오류 테스트"""
        # 존재하지 않는 디렉토리에 저장 시도
        invalid_repository = FileConfigurationRepository("/invalid/path/config.json")
        
        result = invalid_repository.save(sample_configuration, "test_password")
        assert result == False

    def test_repository_thread_safety(self, repository, sample_configuration):
        """Repository 스레드 안전성 테스트"""
        import threading
        import time
        
        master_password = "test_password"
        results = []
        
        def save_config():
            result = repository.save(sample_configuration, master_password)
            results.append(result)
            time.sleep(0.1)
        
        def load_config():
            try:
                config = repository.load(master_password)
                results.append(config is not None)
            except:
                results.append(False)
        
        # 첫 번째 저장을 먼저 실행
        repository.save(sample_configuration, master_password)
        
        # 동시 실행
        threads = []
        for _ in range(5):
            t1 = threading.Thread(target=save_config)
            t2 = threading.Thread(target=load_config)
            threads.extend([t1, t2])
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 결과 검증 - 모든 작업이 성공해야 함
        assert len(results) == 10
        assert all(results)  # 모든 결과가 True여야 함
