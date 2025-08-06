# src/config/configuration_cli.py
"""설정 관리 CLI 도구

콘솔에서 로또 시스템 설정을 관리할 수 있는 명령행 인터페이스입니다.
"""

import argparse
import sys
import getpass
import json
from typing import Dict, Any
from pathlib import Path

from .dependency_injection import get_configuration_usecase
from ..domain.entities.user_credentials import UserCredentials


class ConfigurationCLI:
    """설정 관리 CLI 클래스"""
    
    def __init__(self, config_file_path: str = "config/lotto_config.json"):
        """CLI 초기화
        
        Args:
            config_file_path: 설정 파일 경로
        """
        self.config_file_path = config_file_path
        self.usecase = get_configuration_usecase(config_file_path)
    
    def run(self, args: list = None):
        """CLI 실행
        
        Args:
            args: 명령행 인수 (테스트용, None이면 sys.argv 사용)
        """
        parser = self._create_parser()
        
        if args is None:
            args = sys.argv[1:]
        
        if not args:
            parser.print_help()
            return
        
        parsed_args = parser.parse_args(args)
        
        try:
            # 서브명령 실행
            parsed_args.func(parsed_args)
        except AttributeError:
            parser.print_help()
        except Exception as e:
            print(f"❌ 오류: {e}")
            sys.exit(1)
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """명령행 파서 생성"""
        parser = argparse.ArgumentParser(
            description="로또 자동구매 시스템 설정 관리 도구",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
사용 예제:
  %(prog)s init                    # 최초 설정 생성
  %(prog)s status                  # 설정 상태 확인
  %(prog)s show                    # 설정 내용 표시
  %(prog)s update-purchase         # 구매 설정 수정
  %(prog)s update-recharge         # 충전 설정 수정
  %(prog)s update-discord          # 디스코드 설정 수정
  %(prog)s backup                  # 설정 백업
  %(prog)s reset                   # 설정 초기화
  %(prog)s validate-password       # 마스터 비밀번호 검증
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령들')
        
        # init 명령
        init_parser = subparsers.add_parser('init', help='최초 설정 생성')
        init_parser.add_argument('--user-id', help='동행복권 사용자 ID')
        init_parser.add_argument('--password', help='동행복권 비밀번호')
        init_parser.add_argument('--master-password', help='마스터 비밀번호')
        init_parser.add_argument('--schedule-time', default='14:00', help='구매 시간 (기본값: 14:00)')
        init_parser.add_argument('--purchase-count', type=int, default=1, help='구매 수량 (기본값: 1)')
        init_parser.add_argument('--discord-webhook', help='디스코드 웹훅 URL')
        init_parser.set_defaults(func=self._init_configuration)
        
        # status 명령
        status_parser = subparsers.add_parser('status', help='설정 상태 확인')
        status_parser.set_defaults(func=self._show_status)
        
        # show 명령
        show_parser = subparsers.add_parser('show', help='설정 내용 표시')
        show_parser.add_argument('--master-password', help='마스터 비밀번호')
        show_parser.set_defaults(func=self._show_configuration)
        
        # update-purchase 명령
        update_purchase_parser = subparsers.add_parser('update-purchase', help='구매 설정 수정')
        update_purchase_parser.add_argument('--master-password', help='마스터 비밀번호')
        update_purchase_parser.add_argument('--schedule-time', help='구매 시간 (HH:MM 형식)')
        update_purchase_parser.add_argument('--purchase-count', type=int, help='구매 수량 (1-5)')
        update_purchase_parser.set_defaults(func=self._update_purchase)
        
        # update-recharge 명령
        update_recharge_parser = subparsers.add_parser('update-recharge', help='충전 설정 수정')
        update_recharge_parser.add_argument('--master-password', help='마스터 비밀번호')
        update_recharge_parser.add_argument('--auto-recharge', choices=['true', 'false'], help='자동충전 사용')
        update_recharge_parser.add_argument('--minimum-balance', type=int, help='최소 잔액')
        update_recharge_parser.add_argument('--recharge-amount', type=int, help='충전 금액')
        update_recharge_parser.set_defaults(func=self._update_recharge)
        
        # update-discord 명령
        update_discord_parser = subparsers.add_parser('update-discord', help='디스코드 설정 수정')
        update_discord_parser.add_argument('--master-password', help='마스터 비밀번호')
        update_discord_parser.add_argument('--webhook-url', help='디스코드 웹훅 URL')
        update_discord_parser.add_argument('--enable-notifications', choices=['true', 'false'], help='알림 사용')
        update_discord_parser.set_defaults(func=self._update_discord)
        
        # backup 명령
        backup_parser = subparsers.add_parser('backup', help='설정 백업')
        backup_parser.add_argument('--name', help='백업 이름')
        backup_parser.set_defaults(func=self._backup_configuration)
        
        # reset 명령
        reset_parser = subparsers.add_parser('reset', help='설정 초기화')
        reset_parser.add_argument('--no-backup', action='store_true', help='백업 생성 안함')
        reset_parser.add_argument('--force', action='store_true', help='확인 없이 강제 실행')
        reset_parser.set_defaults(func=self._reset_configuration)
        
        # validate-password 명령
        validate_parser = subparsers.add_parser('validate-password', help='마스터 비밀번호 검증')
        validate_parser.add_argument('--master-password', help='마스터 비밀번호')
        validate_parser.set_defaults(func=self._validate_password)
        
        return parser
    
    def _init_configuration(self, args):
        """최초 설정 생성"""
        print("🚀 로또 자동구매 시스템 최초 설정")
        print("=" * 50)
        
        # 기존 설정 확인
        status = self.usecase.get_configuration_status()
        if status["exists"]:
            print("⚠️  이미 설정이 존재합니다.")
            if not self._confirm("기존 설정을 삭제하고 새로 만드시겠습니까?"):
                return
            
            self.usecase.reset_configuration(create_backup=True)
            print("✅ 기존 설정 삭제 완료")
        
        # 사용자 입력 받기
        user_id = args.user_id or input("동행복권 사용자 ID: ").strip()
        password = args.password or getpass.getpass("동행복권 비밀번호: ").strip()
        master_password = args.master_password or getpass.getpass("마스터 비밀번호 (6자 이상): ").strip()
        
        if not all([user_id, password, master_password]):
            raise ValueError("모든 필수 정보를 입력해야 합니다.")
        
        # 설정 데이터 구성
        setup_data = {
            "user_id": user_id,
            "password": password,
            "master_password": master_password,
            "schedule_time": args.schedule_time,
            "purchase_count": args.purchase_count
        }
        
        if args.discord_webhook:
            setup_data["discord_webhook"] = args.discord_webhook
        
        # 설정 생성
        result = self.usecase.setup_initial_configuration(setup_data)
        
        if result["success"]:
            print("\n✅ 최초 설정이 성공적으로 생성되었습니다!")
            print(f"📁 설정 파일: {self.config_file_path}")
            print(f"👤 사용자: {result['data']['user_id_masked']}")
            print(f"⏰ 구매 시간: {result['data']['schedule_time']}")
            print(f"🎯 구매 수량: {result['data']['purchase_count']}게임")
        else:
            raise Exception(result["error"])
    
    def _show_status(self, args):
        """설정 상태 표시"""
        print("📊 설정 상태")
        print("=" * 30)
        
        status = self.usecase.get_configuration_status()
        
        print(f"📁 설정파일: {self.config_file_path}")
        print(f"✅ 존재여부: {'예' if status['exists'] else '아니오'}")
        print(f"🔒 무결성: {'정상' if status['integrity_valid'] else '손상됨'}")
        print(f"🟢 상태: {status['status']}")
        
        if status["exists"]:
            file_path = Path(self.config_file_path)
            if file_path.exists():
                file_size = file_path.stat().st_size
                modified_time = file_path.stat().st_mtime
                from datetime import datetime
                modified_str = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"📦 파일크기: {file_size} bytes")
                print(f"📅 수정시간: {modified_str}")
    
    def _show_configuration(self, args):
        """설정 내용 표시"""
        master_password = args.master_password or getpass.getpass("마스터 비밀번호: ").strip()
        
        dashboard_data = self.usecase.get_configuration_dashboard_data(master_password)
        
        if not dashboard_data["success"]:
            raise Exception(dashboard_data["error"])
        
        data = dashboard_data["data"]
        
        print("⚙️  현재 설정")
        print("=" * 40)
        print(f"👤 사용자: {data['user_id_masked']}")
        print(f"⏰ 구매시간: {data['purchase_schedule']}")
        print(f"🎯 구매수량: {data['purchase_count']}게임")
        print(f"💳 자동충전: {'사용' if data['auto_recharge_enabled'] else '미사용'}")
        print(f"💰 최소잔액: {data['minimum_balance']:,}원")
        print(f"💸 충전금액: {data['recharge_amount']:,}원")
        print(f"📢 디스코드: {'사용' if data['discord_notifications'] else '미사용'}")
        print(f"✅ 설정상태: {'정상' if data['configuration_valid'] else '오류'}")
    
    def _update_purchase(self, args):
        """구매 설정 수정"""
        master_password = args.master_password or getpass.getpass("마스터 비밀번호: ").strip()
        
        update_data = {}
        if args.schedule_time:
            update_data["schedule_time"] = args.schedule_time
        if args.purchase_count:
            update_data["purchase_count"] = args.purchase_count
        
        if not update_data:
            print("수정할 설정이 없습니다.")
            return
        
        result = self.usecase.update_purchase_configuration(update_data, master_password)
        
        if result["success"]:
            print("✅ 구매 설정이 성공적으로 업데이트되었습니다.")
        else:
            raise Exception(result["error"])
    
    def _update_recharge(self, args):
        """충전 설정 수정"""
        master_password = args.master_password or getpass.getpass("마스터 비밀번호: ").strip()
        
        update_data = {}
        if args.auto_recharge:
            update_data["auto_recharge"] = args.auto_recharge.lower() == 'true'
        if args.minimum_balance:
            update_data["minimum_balance"] = args.minimum_balance
        if args.recharge_amount:
            update_data["recharge_amount"] = args.recharge_amount
        
        if not update_data:
            print("수정할 설정이 없습니다.")
            return
        
        result = self.usecase.update_recharge_configuration(update_data, master_password)
        
        if result["success"]:
            print("✅ 충전 설정이 성공적으로 업데이트되었습니다.")
        else:
            raise Exception(result["error"])
    
    def _update_discord(self, args):
        """디스코드 설정 수정"""
        master_password = args.master_password or getpass.getpass("마스터 비밀번호: ").strip()
        
        update_data = {}
        if args.webhook_url:
            update_data["webhook_url"] = args.webhook_url
        if args.enable_notifications:
            update_data["enable_notifications"] = args.enable_notifications.lower() == 'true'
        
        if not update_data:
            print("수정할 설정이 없습니다.")
            return
        
        result = self.usecase.update_discord_configuration(update_data, master_password)
        
        if result["success"]:
            print("✅ 디스코드 설정이 성공적으로 업데이트되었습니다.")
        else:
            raise Exception(result["error"])
    
    def _backup_configuration(self, args):
        """설정 백업"""
        result = self.usecase.backup_configuration(args.name)
        
        if result["success"]:
            print(f"✅ 설정이 성공적으로 백업되었습니다.")
            print(f"📁 백업파일: {result['backup_path']}")
        else:
            raise Exception(result["error"])
    
    def _reset_configuration(self, args):
        """설정 초기화"""
        if not args.force:
            if not self._confirm("정말로 모든 설정을 초기화하시겠습니까?"):
                return
        
        create_backup = not args.no_backup
        result = self.usecase.reset_configuration(create_backup)
        
        if result["success"]:
            print("✅ 설정이 성공적으로 초기화되었습니다.")
            if "backup_created" in result:
                print(f"📁 백업파일: {result['backup_created']}")
        else:
            raise Exception(result["error"])
    
    def _validate_password(self, args):
        """마스터 비밀번호 검증"""
        master_password = args.master_password or getpass.getpass("마스터 비밀번호: ").strip()
        
        result = self.usecase.validate_master_password(master_password)
        
        if result["valid"]:
            print("✅ 유효한 마스터 비밀번호입니다.")
        else:
            print("❌ 잘못된 마스터 비밀번호입니다.")
            sys.exit(1)
    
    def _confirm(self, message: str) -> bool:
        """사용자 확인"""
        while True:
            response = input(f"{message} (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print("y 또는 n을 입력해주세요.")


def main():
    """CLI 메인 함수"""
    cli = ConfigurationCLI()
    cli.run()


if __name__ == "__main__":
    main()
