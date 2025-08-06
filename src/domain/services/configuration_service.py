# src/domain/services/configuration_service.py
from typing import Optional, Dict, Any
import logging

from ..entities.configuration import Configuration, DiscordSettings
from ..entities.user_credentials import UserCredentials
from ..entities.purchase_settings import PurchaseSettings
from ..entities.recharge_settings import RechargeSettings
from ..repositories.configuration_repository import ConfigurationRepository


class ConfigurationService:
    """설정 관리 도메인 서비스
    
    설정과 관련된 비즈니스 로직을 담당하는 서비스입니다.
    Repository 패턴을 통해 데이터 영속성을 처리하며,
    설정의 생성, 수정, 검증 등의 업무를 담당합니다.
    """

    def __init__(self, repository: ConfigurationRepository):
        """서비스 초기화
        
        Args:
            repository: Configuration Repository 구현체
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    def create_initial_configuration(
        self, 
        user_id: str, 
        password: str, 
        master_password: str,
        schedule_time: str = "14:00",
        purchase_count: int = 1
    ) -> bool:
        """최초 설정 생성
        
        Args:
            user_id: 동행복권 사용자 ID
            password: 동행복권 비밀번호
            master_password: 설정 암호화용 마스터 비밀번호
            schedule_time: 구매 예약 시간 (기본값: 14:00)
            purchase_count: 구매 게임 수 (기본값: 1)
            
        Returns:
            bool: 생성 성공 여부
            
        Raises:
            ValueError: 잘못된 입력값 또는 이미 설정이 존재함
        """
        try:
            # 입력값 검증
            self._validate_initial_parameters(user_id, password, master_password)
            
            # 이미 설정이 존재하는지 확인
            if self.repository.exists():
                raise ValueError("설정이 이미 존재합니다. 기존 설정을 삭제한 후 다시 시도하세요.")
            
            # 기본 설정 생성
            user_credentials = UserCredentials(user_id=user_id, password=password)
            
            purchase_settings = PurchaseSettings(
                schedule_time=schedule_time,
                purchase_count=purchase_count,
                lotto_list=[{"type": "자동", "numbers": []} for _ in range(purchase_count)]
            )
            
            recharge_settings = RechargeSettings.default()
            discord_settings = DiscordSettings()
            
            configuration = Configuration(
                user_credentials=user_credentials,
                purchase_settings=purchase_settings,
                recharge_settings=recharge_settings,
                discord_settings=discord_settings
            )
            
            # 설정 저장
            success = self.repository.save(configuration, master_password)
            
            if success:
                self.logger.info(f"최초 설정 생성 완료: 사용자={user_id[:2]}***, 구매시간={schedule_time}")
            else:
                self.logger.error("최초 설정 저장 실패")
            
            return success
            
        except Exception as e:
            self.logger.error(f"최초 설정 생성 실패: {e}")
            raise

    def load_configuration(self, master_password: str) -> Configuration:
        """설정 로드
        
        Args:
            master_password: 마스터 비밀번호
            
        Returns:
            Configuration: 로드된 설정 객체
            
        Raises:
            ValueError: 잘못된 비밀번호
            FileNotFoundError: 설정 파일 없음
        """
        try:
            self._validate_master_password(master_password)
            configuration = self.repository.load(master_password)
            
            self.logger.info("설정 로드 완료")
            return configuration
            
        except Exception as e:
            self.logger.error(f"설정 로드 실패: {e}")
            raise

    def save_configuration(self, configuration: Configuration, master_password: str) -> bool:
        """설정 저장
        
        Args:
            configuration: 저장할 설정 객체
            master_password: 마스터 비밀번호
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            self._validate_master_password(master_password)
            
            if not configuration.is_valid():
                raise ValueError("유효하지 않은 설정입니다.")
            
            success = self.repository.save(configuration, master_password)
            
            if success:
                self.logger.info("설정 저장 완료")
            else:
                self.logger.error("설정 저장 실패")
            
            return success
            
        except Exception as e:
            self.logger.error(f"설정 저장 실패: {e}")
            return False

    def update_purchase_settings(
        self,
        master_password: str,
        schedule_time: Optional[str] = None,
        purchase_count: Optional[int] = None,
        lotto_list: Optional[list] = None
    ) -> bool:
        """구매 설정 업데이트
        
        Args:
            master_password: 마스터 비밀번호
            schedule_time: 구매 예약 시간
            purchase_count: 구매 게임 수
            lotto_list: 로또 번호 리스트
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            configuration = self.load_configuration(master_password)
            
            # 구매 설정 업데이트
            current_purchase = configuration.purchase_settings
            
            if schedule_time is not None:
                current_purchase.schedule_time = schedule_time
            
            if purchase_count is not None:
                current_purchase.purchase_count = purchase_count
                
                # 구매 수량이 변경되면 lotto_list도 조정
                if lotto_list is None:
                    # 기본 자동 구매로 설정
                    current_purchase.lotto_list = [
                        {"type": "자동", "numbers": []} for _ in range(purchase_count)
                    ]
                else:
                    current_purchase.lotto_list = lotto_list[:purchase_count]
            elif lotto_list is not None:
                current_purchase.lotto_list = lotto_list
            
            # 업데이트된 설정 저장
            return self.save_configuration(configuration, master_password)
            
        except Exception as e:
            self.logger.error(f"구매 설정 업데이트 실패: {e}")
            return False

    def update_recharge_settings(
        self,
        master_password: str,
        auto_recharge: Optional[bool] = None,
        minimum_balance: Optional[int] = None,
        recharge_amount: Optional[int] = None
    ) -> bool:
        """충전 설정 업데이트
        
        Args:
            master_password: 마스터 비밀번호
            auto_recharge: 자동충전 사용 여부
            minimum_balance: 최소 잔액
            recharge_amount: 충전 금액
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            configuration = self.load_configuration(master_password)
            
            # 충전 설정 업데이트
            current_recharge = configuration.recharge_settings
            
            if auto_recharge is not None:
                current_recharge.auto_recharge = auto_recharge
            
            if minimum_balance is not None:
                current_recharge.minimum_balance = minimum_balance
            
            if recharge_amount is not None:
                current_recharge.recharge_amount = recharge_amount
            
            # 업데이트된 설정 저장
            return self.save_configuration(configuration, master_password)
            
        except Exception as e:
            self.logger.error(f"충전 설정 업데이트 실패: {e}")
            return False

    def update_discord_settings(
        self,
        master_password: str,
        webhook_url: Optional[str] = None,
        enable_notifications: Optional[bool] = None
    ) -> bool:
        """디스코드 설정 업데이트
        
        Args:
            master_password: 마스터 비밀번호
            webhook_url: 디스코드 웹훅 URL
            enable_notifications: 알림 사용 여부
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            configuration = self.load_configuration(master_password)
            
            # 디스코드 설정 업데이트
            current_discord = configuration.discord_settings
            
            if webhook_url is not None:
                current_discord.webhook_url = webhook_url
            
            if enable_notifications is not None:
                current_discord.enable_notifications = enable_notifications
            
            # 업데이트된 설정 저장
            return self.save_configuration(configuration, master_password)
            
        except Exception as e:
            self.logger.error(f"디스코드 설정 업데이트 실패: {e}")
            return False

    def validate_master_password(self, master_password: str) -> bool:
        """마스터 비밀번호 검증
        
        Args:
            master_password: 검증할 마스터 비밀번호
            
        Returns:
            bool: 비밀번호 유효성
        """
        try:
            self.repository.load(master_password)
            return True
        except Exception:
            return False

    def backup_configuration(self, backup_suffix: Optional[str] = None) -> Optional[str]:
        """설정 백업
        
        Args:
            backup_suffix: 백업 파일 접미사
            
        Returns:
            Optional[str]: 백업 파일 경로 (실패시 None)
        """
        try:
            backup_path = self.repository.backup(backup_suffix)
            
            if backup_path:
                self.logger.info(f"설정 백업 완료: {backup_path}")
            else:
                self.logger.error("설정 백업 실패")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"설정 백업 실패: {e}")
            return None

    def delete_configuration(self) -> bool:
        """설정 삭제
        
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            success = self.repository.delete()
            
            if success:
                self.logger.info("설정 삭제 완료")
            else:
                self.logger.error("설정 삭제 실패")
            
            return success
            
        except Exception as e:
            self.logger.error(f"설정 삭제 실패: {e}")
            return False

    def configuration_exists(self) -> bool:
        """설정 존재 여부 확인
        
        Returns:
            bool: 설정 파일 존재 여부
        """
        return self.repository.exists()

    def get_configuration_summary(self, master_password: str) -> Dict[str, Any]:
        """설정 요약 정보 조회
        
        Args:
            master_password: 마스터 비밀번호
            
        Returns:
            Dict[str, Any]: 설정 요약 정보
        """
        try:
            configuration = self.load_configuration(master_password)
            
            return {
                "user_id_masked": configuration.user_credentials.mask_sensitive_data()["user_id"],
                "purchase_schedule": configuration.purchase_settings.schedule_time,
                "purchase_count": configuration.purchase_settings.purchase_count,
                "auto_recharge_enabled": configuration.recharge_settings.auto_recharge,
                "minimum_balance": configuration.recharge_settings.minimum_balance,
                "recharge_amount": configuration.recharge_settings.recharge_amount,
                "discord_notifications": configuration.discord_settings.enable_notifications,
                "file_path": self.repository.get_file_path(),
                "configuration_valid": configuration.is_valid()
            }
            
        except Exception as e:
            self.logger.error(f"설정 요약 조회 실패: {e}")
            return {}

    def validate_configuration_integrity(self) -> bool:
        """설정 무결성 검증
        
        Returns:
            bool: 무결성 검증 결과
        """
        try:
            return self.repository.validate_file_integrity()
        except Exception as e:
            self.logger.error(f"설정 무결성 검증 실패: {e}")
            return False

    def _validate_initial_parameters(self, user_id: str, password: str, master_password: str):
        """최초 설정 매개변수 검증"""
        if not user_id or not user_id.strip():
            raise ValueError("사용자 ID는 필수입니다.")
        
        if not password or not password.strip():
            raise ValueError("비밀번호는 필수입니다.")
        
        self._validate_master_password(master_password)

    def _validate_master_password(self, master_password: str):
        """마스터 비밀번호 검증"""
        if not master_password or len(master_password.strip()) < 6:
            raise ValueError("마스터 비밀번호는 최소 6자 이상이어야 합니다.")
