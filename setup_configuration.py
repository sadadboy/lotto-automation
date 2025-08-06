# setup_configuration.py - 설정 관리 스크립트
"""
로또 자동구매 시스템 설정 관리 스크립트

이 스크립트는 최초 실행시 설정을 생성하거나,
기존 설정을 관리할 수 있는 간단한 인터페이스를 제공합니다.
"""

import os
import sys
import json
from pathlib import Path

# src 디렉토리를 Python 패스에 추가
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from src.config.dependency_injection import get_configuration_usecase
from src.config.configuration_cli import ConfigurationCLI


def main():
    """메인 함수"""
    print("🎲 로또 자동구매 시스템 설정 관리")
    print("=" * 50)
    
    # 설정 파일 경로 확인
    config_file = "config/lotto_config.json"
    config_path = Path(config_file)
    
    print(f"📁 설정 파일: {config_path.absolute()}")
    
    # UseCase 인스턴스 생성
    usecase = get_configuration_usecase(config_file)
    
    # 설정 상태 확인
    status = usecase.get_configuration_status()
    
    if status["exists"]:
        print("✅ 기존 설정이 발견되었습니다.")
        print(f"🔒 무결성: {'정상' if status['integrity_valid'] else '손상됨'}")
        print()
        
        show_main_menu(usecase, config_file)
    else:
        print("⚠️  설정이 존재하지 않습니다.")
        print()
        
        setup_initial_configuration(usecase)


def show_main_menu(usecase, config_file):
    """메인 메뉴 표시"""
    while True:
        print("\n📋 설정 관리 메뉴")
        print("-" * 30)
        print("1. 설정 상태 확인")
        print("2. 설정 내용 보기")
        print("3. 구매 설정 수정")
        print("4. 충전 설정 수정")
        print("5. 디스코드 설정 수정")
        print("6. 설정 백업")
        print("7. 설정 초기화")
        print("8. CLI 모드")
        print("0. 종료")
        
        choice = input("\n선택 (0-8): ").strip()
        
        try:
            if choice == "0":
                print("👋 프로그램을 종료합니다.")
                break
            elif choice == "1":
                show_status(usecase)
            elif choice == "2":
                show_configuration(usecase)
            elif choice == "3":
                update_purchase_settings(usecase)
            elif choice == "4":
                update_recharge_settings(usecase)
            elif choice == "5":
                update_discord_settings(usecase)
            elif choice == "6":
                backup_configuration(usecase)
            elif choice == "7":
                reset_configuration(usecase)
            elif choice == "8":
                run_cli_mode(config_file)
            else:
                print("❌ 잘못된 선택입니다.")
        
        except KeyboardInterrupt:
            print("\n\n👋 프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류: {e}")
            input("Enter 키를 눌러 계속...")


def setup_initial_configuration(usecase):
    """최초 설정 생성"""
    print("🚀 최초 설정을 생성합니다.")
    print()
    
    try:
        # 사용자 입력
        user_id = input("동행복권 사용자 ID: ").strip()
        
        import getpass
        password = getpass.getpass("동행복권 비밀번호: ").strip()
        master_password = getpass.getpass("마스터 비밀번호 (6자 이상): ").strip()
        master_password_confirm = getpass.getpass("마스터 비밀번호 확인: ").strip()
        
        if master_password != master_password_confirm:
            raise ValueError("마스터 비밀번호가 일치하지 않습니다.")
        
        # 추가 설정
        print("\n⚙️  추가 설정 (Enter로 기본값 사용)")
        schedule_time = input("구매 시간 [14:00]: ").strip() or "14:00"
        purchase_count = input("구매 수량 [1]: ").strip() or "1"
        discord_webhook = input("디스코드 웹훅 URL (선택): ").strip()
        
        # 설정 데이터 구성
        setup_data = {
            "user_id": user_id,
            "password": password,
            "master_password": master_password,
            "schedule_time": schedule_time,
            "purchase_count": int(purchase_count)
        }
        
        if discord_webhook:
            setup_data["discord_webhook"] = discord_webhook
        
        # 설정 생성
        result = usecase.setup_initial_configuration(setup_data)
        
        if result["success"]:
            print("\n✅ 최초 설정이 성공적으로 생성되었습니다!")
            print(f"👤 사용자: {result['data']['user_id_masked']}")
            print(f"⏰ 구매 시간: {result['data']['schedule_time']}")
            print(f"🎯 구매 수량: {result['data']['purchase_count']}게임")
        else:
            raise Exception(result["error"])
    
    except Exception as e:
        print(f"❌ 설정 생성 실패: {e}")
        input("Enter 키를 눌러 계속...")


def show_status(usecase):
    """설정 상태 표시"""
    print("\n📊 설정 상태")
    print("-" * 30)
    
    status = usecase.get_configuration_status()
    
    print(f"✅ 존재여부: {'예' if status['exists'] else '아니오'}")
    print(f"🔒 무결성: {'정상' if status['integrity_valid'] else '손상됨'}")
    print(f"🟢 상태: {status['status']}")
    
    input("\nEnter 키를 눌러 계속...")


def show_configuration(usecase):
    """설정 내용 표시"""
    print("\n⚙️  현재 설정")
    print("-" * 30)
    
    try:
        import getpass
        master_password = getpass.getpass("마스터 비밀번호: ").strip()
        
        dashboard_data = usecase.get_configuration_dashboard_data(master_password)
        
        if dashboard_data["success"]:
            data = dashboard_data["data"]
            
            print(f"👤 사용자: {data['user_id_masked']}")
            print(f"⏰ 구매시간: {data['purchase_schedule']}")
            print(f"🎯 구매수량: {data['purchase_count']}게임")
            print(f"💳 자동충전: {'사용' if data['auto_recharge_enabled'] else '미사용'}")
            print(f"💰 최소잔액: {data['minimum_balance']:,}원")
            print(f"💸 충전금액: {data['recharge_amount']:,}원")
            print(f"📢 디스코드: {'사용' if data['discord_notifications'] else '미사용'}")
            print(f"✅ 설정상태: {'정상' if data['configuration_valid'] else '오류'}")
        else:
            print(f"❌ 오류: {dashboard_data['error']}")
    
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    input("\nEnter 키를 눌러 계속...")


def update_purchase_settings(usecase):
    """구매 설정 수정"""
    print("\n🎯 구매 설정 수정")
    print("-" * 30)
    
    try:
        import getpass
        master_password = getpass.getpass("마스터 비밀번호: ").strip()
        
        print("새로운 값을 입력하세요 (Enter로 건너뛰기):")
        schedule_time = input("구매 시간 (HH:MM): ").strip()
        purchase_count_str = input("구매 수량 (1-5): ").strip()
        
        update_data = {}
        if schedule_time:
            update_data["schedule_time"] = schedule_time
        if purchase_count_str:
            update_data["purchase_count"] = int(purchase_count_str)
        
        if update_data:
            result = usecase.update_purchase_configuration(update_data, master_password)
            if result["success"]:
                print("✅ 구매 설정이 성공적으로 업데이트되었습니다.")
            else:
                print(f"❌ 오류: {result['error']}")
        else:
            print("변경사항이 없습니다.")
    
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    input("\nEnter 키를 눌러 계속...")


def update_recharge_settings(usecase):
    """충전 설정 수정"""
    print("\n💳 충전 설정 수정")
    print("-" * 30)
    
    try:
        import getpass
        master_password = getpass.getpass("마스터 비밀번호: ").strip()
        
        print("새로운 값을 입력하세요 (Enter로 건너뛰기):")
        auto_recharge = input("자동충전 사용 (true/false): ").strip().lower()
        minimum_balance_str = input("최소 잔액 (원): ").strip()
        recharge_amount_str = input("충전 금액 (원): ").strip()
        
        update_data = {}
        if auto_recharge in ['true', 'false']:
            update_data["auto_recharge"] = auto_recharge == 'true'
        if minimum_balance_str:
            update_data["minimum_balance"] = int(minimum_balance_str)
        if recharge_amount_str:
            update_data["recharge_amount"] = int(recharge_amount_str)
        
        if update_data:
            result = usecase.update_recharge_configuration(update_data, master_password)
            if result["success"]:
                print("✅ 충전 설정이 성공적으로 업데이트되었습니다.")
            else:
                print(f"❌ 오류: {result['error']}")
        else:
            print("변경사항이 없습니다.")
    
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    input("\nEnter 키를 눌러 계속...")


def update_discord_settings(usecase):
    """디스코드 설정 수정"""
    print("\n📢 디스코드 설정 수정")
    print("-" * 30)
    
    try:
        import getpass
        master_password = getpass.getpass("마스터 비밀번호: ").strip()
        
        print("새로운 값을 입력하세요 (Enter로 건너뛰기):")
        webhook_url = input("웹훅 URL: ").strip()
        enable_notifications = input("알림 사용 (true/false): ").strip().lower()
        
        update_data = {}
        if webhook_url:
            update_data["webhook_url"] = webhook_url
        if enable_notifications in ['true', 'false']:
            update_data["enable_notifications"] = enable_notifications == 'true'
        
        if update_data:
            result = usecase.update_discord_configuration(update_data, master_password)
            if result["success"]:
                print("✅ 디스코드 설정이 성공적으로 업데이트되었습니다.")
            else:
                print(f"❌ 오류: {result['error']}")
        else:
            print("변경사항이 없습니다.")
    
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    input("\nEnter 키를 눌러 계속...")


def backup_configuration(usecase):
    """설정 백업"""
    print("\n💾 설정 백업")
    print("-" * 30)
    
    try:
        backup_name = input("백업 이름 (Enter로 자동): ").strip() or None
        
        result = usecase.backup_configuration(backup_name)
        
        if result["success"]:
            print(f"✅ 설정이 성공적으로 백업되었습니다.")
            print(f"📁 백업파일: {result['backup_path']}")
        else:
            print(f"❌ 오류: {result['error']}")
    
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    input("\nEnter 키를 눌러 계속...")


def reset_configuration(usecase):
    """설정 초기화"""
    print("\n🔄 설정 초기화")
    print("-" * 30)
    
    try:
        confirm = input("정말로 모든 설정을 초기화하시겠습니까? (y/N): ").strip().lower()
        
        if confirm == 'y':
            create_backup = input("초기화 전 백업을 생성하시겠습니까? (Y/n): ").strip().lower()
            create_backup = create_backup != 'n'
            
            result = usecase.reset_configuration(create_backup)
            
            if result["success"]:
                print("✅ 설정이 성공적으로 초기화되었습니다.")
                if "backup_created" in result:
                    print(f"📁 백업파일: {result['backup_created']}")
            else:
                print(f"❌ 오류: {result['error']}")
        else:
            print("초기화를 취소했습니다.")
    
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    input("\nEnter 키를 눌러 계속...")


def run_cli_mode(config_file):
    """CLI 모드 실행"""
    print("\n🖥️  CLI 모드")
    print("-" * 30)
    print("사용 가능한 명령어:")
    print("  init, status, show, update-purchase, update-recharge")
    print("  update-discord, backup, reset, validate-password")
    print()
    
    cli = ConfigurationCLI(config_file)
    
    while True:
        try:
            command = input("lotto-config> ").strip()
            
            if not command:
                continue
            
            if command in ['exit', 'quit', 'q']:
                break
            
            if command == 'help':
                print("사용 가능한 명령어:")
                print("  init, status, show, update-purchase, update-recharge")
                print("  update-discord, backup, reset, validate-password")
                print("  help, exit, quit, q")
                continue
            
            cli.run(command.split())
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ 오류: {e}")
    
    print("CLI 모드를 종료합니다.")


if __name__ == "__main__":
    main()
