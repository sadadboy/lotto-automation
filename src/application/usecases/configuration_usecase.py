# src/application/usecases/configuration_usecase.py
from typing import Dict, Any, Optional
import logging

from ...domain.services.configuration_service import ConfigurationService


class ConfigurationUseCase:
    """설정 관리 유스케이스
    
    사용자의 설정 관리와 관련된 구체적인 시나리오를 처리하는 UseCase입니다.
    Clean Architecture의 Application layer에 위치하며,
    사용자 인터페이스와 도메인 로직 사이의 중재자 역할을 합니다.
    """

    def __init__(self, configuration_service: ConfigurationService):
        """UseCase 초기화
        
        Args:
            configuration_service: Configuration Service 인스턴스
        """
        self.service = configuration_service
        self.logger = logging.getLogger(__name__)

    def setup_initial_configuration(self, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """최초 설정 구성 시나리오
        
        사용자가 처음 시스템을 사용할 때 필요한 모든 설정을 구성합니다.
        
        Args:
            setup_data: 설정 데이터
                - user_id: 동행복권 사용자 ID
                - password: 동행복권 비밀번호  
                - master_password: 마스터 비밀번호
                - schedule_time: 구매 시간 (선택, 기본값: 14:00)
                - purchase_count: 구매 수량 (선택, 기본값: 1)
                - auto_recharge: 자동충전 사용 (선택, 기본값: True)
                - minimum_balance: 최소 잔액 (선택, 기본값: 5000)
                - recharge_amount: 충전 금액 (선택, 기본값: 50000)
                - discord_webhook: 디스코드 웹훅 URL (선택)
                
        Returns:
            Dict[str, Any]: 처리 결과
                - success: 성공 여부
                - message: 성공 메시지 또는 오류 메시지
                - data: 추가 데이터 (선택)
        """
        try:
            # 필수 필드 검증
            required_fields = ["user_id", "password", "master_password"]
            missing_fields = [field for field in required_fields if not setup_data.get(field)]
            
            if missing_fields:
                return {
                    "success": False,
                    "error": f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}"
                }
            
            # 이미 설정이 존재하는지 확인
            if self.service.configuration_exists():
                return {
                    "success": False,
                    "error": "이미 설정이 존재합니다. 기존 설정을 삭제한 후 다시 시도하세요."
                }
            
            # 기본값 설정
            user_id = setup_data["user_id"]
            password = setup_data["password"]
            master_password = setup_data["master_password"]
            schedule_time = setup_data.get("schedule_time", "14:00")
            purchase_count = setup_data.get("purchase_count", 1)
            
            # 최초 설정 생성
            success = self.service.create_initial_configuration(
                user_id=user_id,
                password=password,
                master_password=master_password,
                schedule_time=schedule_time,
                purchase_count=purchase_count
            )
            
            if not success:
                return {
                    "success": False,
                    "error": "설정 생성에 실패했습니다."
                }
            
            # 추가 설정 업데이트 (충전 설정)
            if any(key in setup_data for key in ["auto_recharge", "minimum_balance", "recharge_amount"]):
                self.service.update_recharge_settings(
                    master_password=master_password,
                    auto_recharge=setup_data.get("auto_recharge"),
                    minimum_balance=setup_data.get("minimum_balance"),
                    recharge_amount=setup_data.get("recharge_amount")
                )
            
            # 디스코드 설정 업데이트
            if "discord_webhook" in setup_data:
                self.service.update_discord_settings(
                    master_password=master_password,
                    webhook_url=setup_data["discord_webhook"],
                    enable_notifications=True
                )
            
            self.logger.info(f"최초 설정 구성 완료: {user_id[:2]}***")
            
            return {
                "success": True,
                "message": "최초 설정이 성공적으로 구성되었습니다.",
                "data": {
                    "user_id_masked": f"{user_id[:2]}{'*' * (len(user_id) - 2)}",
                    "schedule_time": schedule_time,
                    "purchase_count": purchase_count
                }
            }
            
        except Exception as e:
            self.logger.error(f"최초 설정 구성 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_configuration_dashboard_data(self, master_password: str) -> Dict[str, Any]:
        """대시보드용 설정 데이터 조회 시나리오
        
        웹 대시보드에서 표시할 설정 정보를 조회합니다.
        
        Args:
            master_password: 마스터 비밀번호
            
        Returns:
            Dict[str, Any]: 대시보드 데이터
        """
        try:
            # 설정 상태 확인
            exists = self.service.configuration_exists()
            integrity_valid = self.service.validate_configuration_integrity()
            
            if not exists:
                return {
                    "success": False,
                    "error": "설정이 존재하지 않습니다.",
                    "exists": False,
                    "integrity_valid": False
                }
            
            # 설정 요약 정보 조회
            summary = self.service.get_configuration_summary(master_password)
            
            return {
                "success": True,
                "data": summary,
                "exists": exists,
                "integrity_valid": integrity_valid
            }
            
        except Exception as e:
            self.logger.error(f"대시보드 데이터 조회 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "exists": False,
                "integrity_valid": False
            }

    def update_purchase_configuration(self, update_data: Dict[str, Any], master_password: str) -> Dict[str, Any]:
        """구매 설정 업데이트 시나리오
        
        Args:
            update_data: 업데이트할 구매 설정 데이터
            master_password: 마스터 비밀번호
            
        Returns:
            Dict[str, Any]: 처리 결과
        """
        try:
            success = self.service.update_purchase_settings(
                master_password=master_password,
                schedule_time=update_data.get("schedule_time"),
                purchase_count=update_data.get("purchase_count"),
                lotto_list=update_data.get("lotto_list")
            )
            
            if success:
                self.logger.info("구매 설정 업데이트 완료")
                return {
                    "success": True,
                    "message": "구매 설정이 성공적으로 업데이트되었습니다."
                }
            else:
                return {
                    "success": False,
                    "error": "구매 설정 업데이트에 실패했습니다."
                }
                
        except Exception as e:
            self.logger.error(f"구매 설정 업데이트 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_recharge_configuration(self, update_data: Dict[str, Any], master_password: str) -> Dict[str, Any]:
        """충전 설정 업데이트 시나리오
        
        Args:
            update_data: 업데이트할 충전 설정 데이터
            master_password: 마스터 비밀번호
            
        Returns:
            Dict[str, Any]: 처리 결과
        """
        try:
            success = self.service.update_recharge_settings(
                master_password=master_password,
                auto_recharge=update_data.get("auto_recharge"),
                minimum_balance=update_data.get("minimum_balance"),
                recharge_amount=update_data.get("recharge_amount")
            )
            
            if success:
                self.logger.info("충전 설정 업데이트 완료")
                return {
                    "success": True,
                    "message": "충전 설정이 성공적으로 업데이트되었습니다."
                }
            else:
                return {
                    "success": False,
                    "error": "충전 설정 업데이트에 실패했습니다."
                }
                
        except Exception as e:
            self.logger.error(f"충전 설정 업데이트 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_discord_configuration(self, update_data: Dict[str, Any], master_password: str) -> Dict[str, Any]:
        """디스코드 설정 업데이트 시나리오
        
        Args:
            update_data: 업데이트할 디스코드 설정 데이터
            master_password: 마스터 비밀번호
            
        Returns:
            Dict[str, Any]: 처리 결과
        """
        try:
            success = self.service.update_discord_settings(
                master_password=master_password,
                webhook_url=update_data.get("webhook_url"),
                enable_notifications=update_data.get("enable_notifications")
            )
            
            if success:
                self.logger.info("디스코드 설정 업데이트 완료")
                return {
                    "success": True,
                    "message": "디스코드 설정이 성공적으로 업데이트되었습니다."
                }
            else:
                return {
                    "success": False,
                    "error": "디스코드 설정 업데이트에 실패했습니다."
                }
                
        except Exception as e:
            self.logger.error(f"디스코드 설정 업데이트 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def validate_master_password(self, master_password: str) -> Dict[str, Any]:
        """마스터 비밀번호 검증 시나리오
        
        Args:
            master_password: 검증할 마스터 비밀번호
            
        Returns:
            Dict[str, Any]: 검증 결과
        """
        try:
            is_valid = self.service.validate_master_password(master_password)
            
            return {
                "valid": is_valid,
                "message": "유효한 비밀번호입니다." if is_valid else "잘못된 비밀번호입니다."
            }
            
        except Exception as e:
            self.logger.error(f"마스터 비밀번호 검증 실패: {e}")
            return {
                "valid": False,
                "message": "비밀번호 검증 중 오류가 발생했습니다."
            }

    def backup_configuration(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """설정 백업 시나리오
        
        Args:
            backup_name: 백업 파일 이름 (선택)
            
        Returns:
            Dict[str, Any]: 백업 결과
        """
        try:
            backup_path = self.service.backup_configuration(backup_name)
            
            if backup_path:
                self.logger.info(f"설정 백업 완료: {backup_path}")
                return {
                    "success": True,
                    "message": "설정이 성공적으로 백업되었습니다.",
                    "backup_path": backup_path
                }
            else:
                return {
                    "success": False,
                    "error": "설정 백업에 실패했습니다."
                }
                
        except Exception as e:
            self.logger.error(f"설정 백업 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def reset_configuration(self, create_backup: bool = True) -> Dict[str, Any]:
        """설정 초기화 시나리오
        
        Args:
            create_backup: 백업 생성 여부
            
        Returns:
            Dict[str, Any]: 초기화 결과
        """
        try:
            result = {"success": True, "message": "설정이 성공적으로 초기화되었습니다."}
            
            # 백업 생성 (선택)
            if create_backup:
                backup_path = self.service.backup_configuration("before_reset")
                if backup_path:
                    result["backup_created"] = backup_path
                    self.logger.info(f"초기화 전 백업 생성: {backup_path}")
            
            # 설정 삭제
            success = self.service.delete_configuration()
            
            if not success:
                return {
                    "success": False,
                    "error": "설정 삭제에 실패했습니다."
                }
            
            self.logger.info("설정 초기화 완료")
            return result
            
        except Exception as e:
            self.logger.error(f"설정 초기화 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_configuration_status(self) -> Dict[str, Any]:
        """설정 상태 조회 시나리오
        
        Returns:
            Dict[str, Any]: 설정 상태 정보
        """
        try:
            exists = self.service.configuration_exists()
            integrity_valid = self.service.validate_configuration_integrity()
            
            return {
                "exists": exists,
                "integrity_valid": integrity_valid,
                "status": "healthy" if exists and integrity_valid else "needs_attention"
            }
            
        except Exception as e:
            self.logger.error(f"설정 상태 조회 실패: {e}")
            return {
                "exists": False,
                "integrity_valid": False,
                "status": "error"
            }

    def get_current_configuration(self, master_password: str = None) -> Optional['Configuration']:
        """현재 설정 조회 시나리오
        
        Args:
            master_password: 마스터 비밀번호 (선택)
            
        Returns:
            Configuration: 설정 객체 또는 None
        """
        try:
            from ...domain.entities.configuration import Configuration
            
            # 설정 존재 여부 확인
            if not self.service.configuration_exists():
                return None
            
            # 설정 요약 정보 조회
            if master_password:
                try:
                    summary = self.service.get_configuration_summary(master_password)
                    if not summary.get("configuration_valid", False):
                        return None
                        
                    # Configuration 객체 생성 (새로운 메서드 사용)
                    return Configuration.from_dict_simple(summary)
                except Exception:
                    # fallback: 기본 설정 반환
                    return Configuration.create_default()
            else:
                # 비밀번호 없이 기본 정보만 반환
                return Configuration.create_default()
                
        except Exception as e:
            self.logger.error(f"현재 설정 조회 실패: {e}")
            return None

    def get_configuration_health_check(self, master_password: str) -> Dict[str, Any]:
        """설정 상태 체크 시나리오
        
        Args:
            master_password: 마스터 비밀번호
            
        Returns:
            Dict[str, Any]: 상태 체크 결과
        """
        try:
            # 기본 상태 확인
            exists = self.service.configuration_exists()
            integrity_valid = self.service.validate_configuration_integrity()
            
            if not exists or not integrity_valid:
                return {
                    "healthy": False,
                    "exists": exists,
                    "integrity_valid": integrity_valid,
                    "configuration_valid": False,
                    "issues": ["Configuration file missing or corrupted"]
                }
            
            # 설정 내용 검증
            try:
                summary = self.service.get_configuration_summary(master_password)
                configuration_valid = summary.get("configuration_valid", False)
            except:
                configuration_valid = False
            
            healthy = exists and integrity_valid and configuration_valid
            
            return {
                "healthy": healthy,
                "exists": exists,
                "integrity_valid": integrity_valid,
                "configuration_valid": configuration_valid,
                "issues": [] if healthy else ["Configuration validation failed"]
            }
            
        except Exception as e:
            self.logger.error(f"설정 상태 체크 실패: {e}")
            return {
                "healthy": False,
                "exists": False,
                "integrity_valid": False,
                "configuration_valid": False,
                "issues": [str(e)]
            }
