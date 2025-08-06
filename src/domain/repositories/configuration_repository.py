# src/domain/repositories/configuration_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from ..entities.configuration import Configuration


class ConfigurationRepository(ABC):
    """Configuration Repository 인터페이스
    
    설정 데이터의 영속성을 담당하는 Repository 패턴의 추상 인터페이스입니다.
    Clean Architecture의 원칙에 따라 Domain layer에 위치하며,
    Infrastructure layer에서 구체적인 구현체를 제공합니다.
    """

    @abstractmethod
    def save(self, configuration: Configuration, master_password: str) -> bool:
        """설정을 저장합니다.
        
        Args:
            configuration: 저장할 설정 객체
            master_password: 암호화에 사용할 마스터 비밀번호
            
        Returns:
            bool: 저장 성공 여부
            
        Raises:
            ValueError: 잘못된 설정 또는 비밀번호
            PermissionError: 파일 저장 권한 없음
        """
        pass

    @abstractmethod
    def load(self, master_password: str) -> Configuration:
        """설정을 로드합니다.
        
        Args:
            master_password: 복호화에 사용할 마스터 비밀번호
            
        Returns:
            Configuration: 로드된 설정 객체
            
        Raises:
            FileNotFoundError: 설정 파일이 존재하지 않음
            ValueError: 잘못된 비밀번호 또는 손상된 파일
            PermissionError: 파일 접근 권한 없음
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """설정 파일의 존재 여부를 확인합니다.
        
        Returns:
            bool: 설정 파일 존재 여부
        """
        pass

    @abstractmethod
    def delete(self) -> bool:
        """설정 파일을 삭제합니다.
        
        Returns:
            bool: 삭제 성공 여부
        """
        pass

    @abstractmethod
    def backup(self, backup_suffix: Optional[str] = None) -> Optional[str]:
        """설정 파일을 백업합니다.
        
        Args:
            backup_suffix: 백업 파일 접미사 (기본값: timestamp)
            
        Returns:
            Optional[str]: 백업 파일 경로 (실패시 None)
        """
        pass

    @abstractmethod
    def get_file_path(self) -> str:
        """설정 파일 경로를 반환합니다.
        
        Returns:
            str: 설정 파일의 전체 경로
        """
        pass

    @abstractmethod
    def validate_file_integrity(self) -> bool:
        """설정 파일의 무결성을 검증합니다.
        
        Returns:
            bool: 파일 무결성 여부
        """
        pass
