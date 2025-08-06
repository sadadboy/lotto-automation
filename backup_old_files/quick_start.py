# quick_start.py - 빠른 시작 스크립트
import os
import sys
import json
import subprocess
import platform

def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        print(f"현재 버전: {sys.version}")
        return False
    print(f"✅ Python 버전: {sys.version}")
    return True

def check_chrome():
    """Chrome 설치 확인"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["where", "chrome"], capture_output=True)
        else:
            result = subprocess.run(["which", "google-chrome"], capture_output=True)
        
        if result.returncode == 0:
            print("✅ Chrome 브라우저 설치됨")
            return True
        else:
            print("❌ Chrome 브라우저가 설치되지 않았습니다.")
            print("   https://www.google.com/chrome/ 에서 설치해주세요.")
            return False
    except:
        print("⚠️ Chrome 확인 실패 - 수동으로 확인해주세요.")
        return True

def install_requirements():
    """의존성 설치"""
    print("\n📦 필요한 패키지를 설치합니다...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ 패키지 설치 완료")
        return True
    except subprocess.CalledProcessError:
        print("❌ 패키지 설치 실패")
        return False

def setup_config():
    """설정 파일 설정"""
    print("\n⚙️ 설정 파일을 준비합니다...")
    
    if os.path.exists("lotto_config.json"):
        print("✅ 설정 파일이 이미 존재합니다.")
        response = input("기존 설정을 유지하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            return True
    
    # 설정 파일 복사
    if os.path.exists("lotto_config.json.example"):
        with open("lotto_config.json.example", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        print("\n로그인 정보를 입력해주세요:")
        user_id = input("동행복권 ID: ")
        password = input("동행복권 비밀번호: ")
        
        config["login"]["user_id"] = user_id
        config["login"]["password"] = password
        
        # 자동충전 설정
        auto_recharge = input("\n자동충전을 사용하시겠습니까? (y/n): ")
        config["payment"]["auto_recharge"] = auto_recharge.lower() == 'y'
        
        if config["payment"]["auto_recharge"]:
            amount = input("충전 금액 (기본: 50000): ")
            if amount.isdigit():
                config["payment"]["recharge_amount"] = int(amount)
        
        # 저장
        with open("lotto_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("✅ 설정 파일 생성 완료")
        return True
    else:
        print("❌ 설정 파일 예제를 찾을 수 없습니다.")
        return False

def create_directories():
    """필요한 디렉토리 생성"""
    print("\n📁 필요한 디렉토리를 생성합니다...")
    dirs = ["logs", "screenshots", "data", "backups"]
    
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✅ {dir_name}/ 디렉토리 준비됨")
    
    return True

def run_test():
    """시스템 테스트"""
    print("\n🧪 시스템 테스트를 실행합니다...")
    try:
        result = subprocess.run([sys.executable, "test_system.py"], capture_output=True, text=True)
        print(result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 테스트 실행 실패: {e}")
        return False

def show_menu():
    """메뉴 표시"""
    print("\n" + "="*50)
    print("로또 자동구매 시스템 준비 완료!")
    print("="*50)
    print("\n실행 옵션:")
    print("1. 즉시 로또 구매")
    print("2. GUI 대시보드 실행")
    print("3. 스케줄러 실행")
    print("4. 시스템 테스트")
    print("5. 종료")
    
    choice = input("\n선택하세요 (1-5): ")
    
    if choice == "1":
        print("\n🎲 로또 구매를 시작합니다...")
        subprocess.run([sys.executable, "lotto_auto_buyer.py", "--now"])
    elif choice == "2":
        print("\n🖥️ GUI 대시보드를 시작합니다...")
        print("브라우저에서 http://localhost:5000 으로 접속하세요.")
        subprocess.run([sys.executable, "dashboard.py"])
    elif choice == "3":
        print("\n⏰ 스케줄러를 시작합니다...")
        subprocess.run([sys.executable, "scheduler.py"])
    elif choice == "4":
        run_test()
    elif choice == "5":
        print("\n👋 프로그램을 종료합니다.")
        sys.exit(0)
    else:
        print("\n❌ 잘못된 선택입니다.")

def main():
    """메인 함수"""
    print("🎲 로또 자동구매 시스템 빠른 시작")
    print("="*50)
    
    # 환경 검사
    checks = [
        ("Python 버전 확인", check_python_version),
        ("Chrome 브라우저 확인", check_chrome),
        ("패키지 설치", install_requirements),
        ("설정 파일 준비", setup_config),
        ("디렉토리 생성", create_directories)
    ]
    
    for name, func in checks:
        print(f"\n{name}...")
        if not func():
            print(f"\n❌ {name} 실패. 문제를 해결한 후 다시 실행해주세요.")
            sys.exit(1)
    
    # 테스트 실행 (선택사항)
    response = input("\n시스템 테스트를 실행하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        if not run_test():
            print("\n⚠️ 일부 테스트가 실패했습니다. 계속 진행하시겠습니까? (y/n): ")
            if input().lower() != 'y':
                sys.exit(1)
    
    # 메뉴 표시
    while True:
        show_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)
