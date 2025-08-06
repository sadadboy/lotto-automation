# src/config/dependency_injection.py
"""의존성 주입 컨테이너

Clean Architecture의 의존성 역전 원칙을 적용하여
각 레이어 간의 의존성을 관리하는 컨테이너입니다.
"""

from typing import Dict, Any, Optional
import logging
from pathlib import Path

from ..domain.repositories.configuration_repository import ConfigurationRepository
from ..domain.services.configuration_service import ConfigurationService
from ..application.usecases.configuration_usecase import ConfigurationUseCase
from ..infrastructure.repositories.file_configuration_repository import FileConfigurationRepository


class DIContainer:
    """의존성 주입 컨테이너
    
    애플리케이션의 모든 의존성을 관리하고,
    Clean Architecture 레이어 간의 의존성을 제공합니다.
    """
    
    def __init__(self, config_file_path: Optional[str] = None):
        """DI 컨테이너 초기화
        
        Args:
            config_file_path: 설정 파일 경로 (기본값: config/lotto_config.json)
        """
        self._instances: Dict[str, Any] = {}
        self._config_file_path = config_file_path or "config/lotto_config.json"
        self.logger = logging.getLogger(__name__)
        
        # 기본 설정 디렉토리 생성
        Path(self._config_file_path).parent.mkdir(parents=True, exist_ok=True)
    
    def get_configuration_repository(self) -> ConfigurationRepository:
        """Configuration Repository 인스턴스 반환"""
        if 'configuration_repository' not in self._instances:
            self._instances['configuration_repository'] = FileConfigurationRepository(
                self._config_file_path
            )
            self.logger.debug(f"Configuration Repository 생성: {self._config_file_path}")
        
        return self._instances['configuration_repository']
    
    def get_configuration_service(self) -> ConfigurationService:
        """Configuration Service 인스턴스 반환"""
        if 'configuration_service' not in self._instances:
            repository = self.get_configuration_repository()
            self._instances['configuration_service'] = ConfigurationService(repository)
            self.logger.debug("Configuration Service 생성")
        
        return self._instances['configuration_service']
    
    def get_configuration_usecase(self) -> ConfigurationUseCase:
        """Configuration UseCase 인스턴스 반환"""
        if 'configuration_usecase' not in self._instances:
            service = self.get_configuration_service()
            self._instances['configuration_usecase'] = ConfigurationUseCase(service)
            self.logger.debug("Configuration UseCase 생성")
        
        return self._instances['configuration_usecase']
    
    def reset_instances(self):
        """모든 인스턴스 초기화 (테스트용)"""
        self._instances.clear()
        self.logger.debug("DI Container 인스턴스 초기화")
    
    def get_instance_info(self) -> Dict[str, str]:
        """현재 생성된 인스턴스 정보 반환"""
        return {
            key: str(type(value).__name__) 
            for key, value in self._instances.items()
        }


# 전역 DI 컨테이너 인스턴스 (싱글톤 패턴)
_container: Optional[DIContainer] = None


def get_container(config_file_path: Optional[str] = None) -> DIContainer:
    """전역 DI 컨테이너 인스턴스 반환
    
    Args:
        config_file_path: 설정 파일 경로 (최초 호출시에만 적용)
        
    Returns:
        DIContainer: DI 컨테이너 인스턴스
    """
    global _container
    
    if _container is None:
        _container = DIContainer(config_file_path)
    
    return _container


def reset_container():
    """전역 DI 컨테이너 초기화 (테스트용)"""
    global _container
    _container = None


# 편의 함수들
def get_configuration_usecase(config_file_path: Optional[str] = None) -> ConfigurationUseCase:
    """Configuration UseCase 인스턴스 반환"""
    return get_container(config_file_path).get_configuration_usecase()


def get_configuration_service(config_file_path: Optional[str] = None) -> ConfigurationService:
    """Configuration Service 인스턴스 반환"""
    return get_container(config_file_path).get_configuration_service()


def get_configuration_repository(config_file_path: Optional[str] = None) -> ConfigurationRepository:
    """Configuration Repository 인스턴스 반환"""
    return get_container(config_file_path).get_configuration_repository()
