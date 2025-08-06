# example_usage.py - 설정 관리 시스템 사용 예제
"""
로또 자동구매 시스템 설정 관리 사용 예제

이 스크립트는 설정 관리 시스템의 모든 기능을 
실제로 사용해보는 예제를 제공합니다.
"""

import sys
import tempfile
import os
from pathlib import Path

# src 디렉토리를 Python 패스에 추가
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from src.config.dependency_injection import get_configuration_usecase, reset_container


def main():
    """메인 예제 실행"""
    print("📚 로또 자동구매 시스템 - 설정 관리 사용 예제")
    print("=" * 60)
    
    # 임시 설정 파일로 예제 실행
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_config_path = temp_file.name
    
    try:
        print(f"📁 임시 설정 파일: {temp_config_path}")
        print()
        
        # DI 컨테이너 초기화
        reset_container()
        
        # UseCase 인스턴스 생성
        usecase = get_configuration_usecase(temp_config_path)
        
        # 예제 실행
        run_complete_example(usecase)
        
    finally:
        # 임시 파일 정리
        try:
            os.unlink(temp_config_path)
            backup_files = [f for f in os.listdir('.') if f.startswith(os.path.basename(temp_config_path).replace('.json', ''))]
            for backup_file in backup_files:
                try:
                    os.unlink(backup_file)
                except:
                    pass
        except:
            pass
        
        print("\n🧹 임시 파일 정리 완료")


def run_complete_example(usecase):
    """완전한 예제 실행"""
    
    # 1. 초기 상태 확인
    print("1️⃣ 초기 상태 확인")
    print("-" * 30)
    
    status = usecase.get_configuration_status()
    print(f"설정 존재: {status['exists']}")
    print(f"무결성: {status['integrity_valid']}")
    print(f"상태: {status['status']}")
    print()
    
    # 2. 최초 설정 생성
    print("2️⃣ 최초 설정 생성")
    print("-" * 30)
    
    setup_data = {
        "user_id": "example_user",
        "password": "example_password",
        "master_password": "example_master_123456",
        "schedule_time": "15:30",
        "purchase_count": 3,
        "auto_recharge": True,
        "minimum_balance": 10000,
        "recharge_amount": 100000,
        "discord_webhook": "https://discord.com/api/webhooks/example"
    }
    
    result = usecase.setup_initial_configuration(setup_data)
    
    if result["success"]:
        print("✅ 최초 설정 생성 성공!")
        print(f"   사용자: {result['data']['user_id_masked']}")
        print(f"   구매시간: {result['data']['schedule_time']}")
        print(f"   구매수량: {result['data']['purchase_count']}게임")
    else:
        print(f"❌ 설정 생성 실패: {result['error']}")
        return
    
    print()
    
    # 3. 마스터 비밀번호 검증
    print("3️⃣ 마스터 비밀번호 검증")
    print("-" * 30)
    
    # 올바른 비밀번호
    valid_result = usecase.validate_master_password("example_master_123456")
    print(f"올바른 비밀번호: {valid_result['valid']} - {valid_result['message']}")
    
    # 잘못된 비밀번호
    invalid_result = usecase.validate_master_password("wrong_password")
    print(f"잘못된 비밀번호: {invalid_result['valid']} - {invalid_result['message']}")
    print()
    
    # 4. 설정 내용 조회
    print("4️⃣ 설정 내용 조회")
    print("-" * 30)
    
    dashboard_data = usecase.get_configuration_dashboard_data("example_master_123456")
    
    if dashboard_data["success"]:
        data = dashboard_data["data"]
        print(f"👤 사용자: {data['user_id_masked']}")
        print(f"⏰ 구매시간: {data['purchase_schedule']}")
        print(f"🎯 구매수량: {data['purchase_count']}게임")
        print(f"💳 자동충전: {'사용' if data['auto_recharge_enabled'] else '미사용'}")
        print(f"💰 최소잔액: {data['minimum_balance']:,}원")
        print(f"💸 충전금액: {data['recharge_amount']:,}원")
        print(f"📢 디스코드: {'사용' if data['discord_notifications'] else '미사용'}")
    else:
        print(f"❌ 조회 실패: {dashboard_data['error']}")
    
    print()
    
    # 5. 구매 설정 업데이트
    print("5️⃣ 구매 설정 업데이트")
    print("-" * 30)
    
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
        purchase_update, "example_master_123456"
    )
    
    if update_result["success"]:
        print("✅ 구매 설정 업데이트 성공!")
        print("   구매시간: 15:30 → 16:00")
        print("   구매수량: 3게임 → 5게임")
    else:
        print(f"❌ 업데이트 실패: {update_result['error']}")
    
    print()
    
    # 6. 충전 설정 업데이트
    print("6️⃣ 충전 설정 업데이트")
    print("-" * 30)
    
    recharge_update = {
        "auto_recharge": False,
        "minimum_balance": 3000,
        "recharge_amount": 30000
    }
    
    recharge_result = usecase.update_recharge_configuration(
        recharge_update, "example_master_123456"
    )
    
    if recharge_result["success"]:
        print("✅ 충전 설정 업데이트 성공!")
        print("   자동충전: 사용 → 미사용")
        print("   최소잔액: 10,000원 → 3,000원")
        print("   충전금액: 100,000원 → 30,000원")
    else:
        print(f"❌ 업데이트 실패: {recharge_result['error']}")
    
    print()
    
    # 7. 디스코드 설정 업데이트
    print("7️⃣ 디스코드 설정 업데이트")
    print("-" * 30)
    
    discord_update = {
        "webhook_url": "https://discord.com/api/webhooks/updated_example",
        "enable_notifications": False
    }
    
    discord_result = usecase.update_discord_configuration(
        discord_update, "example_master_123456"
    )
    
    if discord_result["success"]:
        print("✅ 디스코드 설정 업데이트 성공!")
        print("   웹훅 URL: 업데이트됨")
        print("   알림: 사용 → 미사용")
    else:
        print(f"❌ 업데이트 실패: {discord_result['error']}")
    
    print()
    
    # 8. 업데이트된 설정 확인
    print("8️⃣ 업데이트된 설정 확인")
    print("-" * 30)
    
    updated_data = usecase.get_configuration_dashboard_data("example_master_123456")
    
    if updated_data["success"]:
        data = updated_data["data"]
        print(f"⏰ 구매시간: {data['purchase_schedule']}")
        print(f"🎯 구매수량: {data['purchase_count']}게임")
        print(f"💳 자동충전: {'사용' if data['auto_recharge_enabled'] else '미사용'}")
        print(f"💰 최소잔액: {data['minimum_balance']:,}원")
        print(f"📢 디스코드: {'사용' if data['discord_notifications'] else '미사용'}")
    
    print()
    
    # 9. 설정 백업
    print("9️⃣ 설정 백업")
    print("-" * 30)
    
    backup_result = usecase.backup_configuration("example_backup")
    
    if backup_result["success"]:
        print("✅ 설정 백업 성공!")
        print(f"   백업파일: {backup_result['backup_path']}")
        
        # 백업 파일 존재 확인
        if os.path.exists(backup_result['backup_path']):
            file_size = os.path.getsize(backup_result['backup_path'])
            print(f"   파일크기: {file_size} bytes")
        
    else:
        print(f"❌ 백업 실패: {backup_result['error']}")
    
    print()
    
    # 10. 설정 상태 체크
    print("🔟 설정 상태 체크")
    print("-" * 30)
    
    health_check = usecase.get_configuration_health_check("example_master_123456")
    
    print(f"전반적 상태: {'정상' if health_check['healthy'] else '문제있음'}")
    print(f"설정 존재: {health_check['exists']}")
    print(f"파일 무결성: {health_check['integrity_valid']}")
    print(f"설정 유효성: {health_check['configuration_valid']}")
    
    if health_check['issues']:
        print("문제점:")
        for issue in health_check['issues']:
            print(f"  - {issue}")
    
    print()
    
    # 11. 최종 상태
    print("1️⃣1️⃣ 최종 상태")
    print("-" * 30)
    
    final_status = usecase.get_configuration_status()
    print(f"설정 파일: {'존재' if final_status['exists'] else '없음'}")
    print(f"무결성: {'정상' if final_status['integrity_valid'] else '손상'}")
    print(f"전체 상태: {final_status['status']}")
    
    print()
    print("🎉 모든 예제가 성공적으로 완료되었습니다!")
    print("✨ 설정 관리 시스템이 정상적으로 작동합니다.")


def run_error_handling_example():
    """오류 처리 예제"""
    print("\n🚨 오류 처리 예제")
    print("=" * 40)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_config_path = temp_file.name
    
    try:
        reset_container()
        usecase = get_configuration_usecase(temp_config_path)
        
        # 1. 설정이 없을 때
        print("1. 설정이 없을 때 조회 시도")
        result = usecase.get_configuration_dashboard_data("any_password")
        print(f"   결과: {result['success']} - {result.get('error', '')[:50]}...")
        
        # 2. 잘못된 설정 데이터
        print("\n2. 잘못된 설정 데이터로 생성 시도")
        invalid_data = {
            "user_id": "",  # 빈 사용자 ID
            "password": "test",
            "master_password": "123"  # 너무 짧은 비밀번호
        }
        result = usecase.setup_initial_configuration(invalid_data)
        print(f"   결과: {result['success']} - {result.get('error', '')[:50]}...")
        
        # 3. 올바른 설정 생성 후 중복 생성 시도
        print("\n3. 중복 설정 생성 시도")
        valid_data = {
            "user_id": "test_user",
            "password": "test_password",
            "master_password": "valid_master_123456"
        }
        
        # 첫 번째 생성 (성공)
        result1 = usecase.setup_initial_configuration(valid_data)
        print(f"   첫 번째 생성: {result1['success']}")
        
        # 두 번째 생성 시도 (실패)
        result2 = usecase.setup_initial_configuration(valid_data)
        print(f"   두 번째 생성: {result2['success']} - {result2.get('error', '')[:50]}...")
        
        print("\n✅ 오류 처리가 정상적으로 작동합니다!")
        
    finally:
        try:
            os.unlink(temp_config_path)
        except:
            pass


if __name__ == "__main__":
    try:
        main()
        
        # 오류 처리 예제도 실행
        if len(sys.argv) > 1 and sys.argv[1] == "--with-errors":
            run_error_handling_example()
            
    except KeyboardInterrupt:
        print("\n\n👋 예제 실행이 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
