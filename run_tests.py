# run_tests.py - 테스트 실행 스크립트
"""
설정 관리 시스템 테스트 실행 스크립트

작성된 모든 테스트를 실행하고 결과를 확인합니다.
"""

import sys
import subprocess
import os
from pathlib import Path

def main():
    """메인 함수"""
    print("🧪 로또 자동구매 시스템 - 설정 관리 테스트")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    current_dir = Path(__file__).parent
    os.chdir(current_dir)
    
    print(f"📁 작업 디렉토리: {current_dir}")
    print()
    
    # Python 경로 설정
    env = os.environ.copy()
    env["PYTHONPATH"] = str(current_dir / "src")
    
    try:
        # 1. pytest 설치 확인
        print("1️⃣ pytest 설치 확인...")
        result = subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                              capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
            print("❌ pytest가 설치되지 않았습니다.")
            print("다음 명령으로 설치하세요: pip install pytest pytest-mock")
            return
        
        print(f"✅ {result.stdout.strip()}")
        print()
        
        # 2. 단위 테스트 실행
        print("2️⃣ 단위 테스트 실행...")
        print("-" * 40)
        
        unit_result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/unit/", 
            "-v", 
            "--tb=short",
            "-m", "unit"
        ], env=env)
        
        print()
        
        # 3. 통합 테스트 실행
        print("3️⃣ 통합 테스트 실행...")
        print("-" * 40)
        
        integration_result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/integration/", 
            "-v", 
            "--tb=short",
            "-m", "integration"
        ], env=env)
        
        print()
        
        # 4. 전체 테스트 커버리지 (선택)
        print("4️⃣ 전체 테스트 요약...")
        print("-" * 40)
        
        summary_result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "--tb=no", 
            "-q"
        ], env=env)
        
        print()
        
        # 5. 결과 요약
        print("📊 테스트 결과 요약")
        print("=" * 40)
        
        if unit_result.returncode == 0:
            print("✅ 단위 테스트: 통과")
        else:
            print("❌ 단위 테스트: 실패")
        
        if integration_result.returncode == 0:
            print("✅ 통합 테스트: 통과")
        else:
            print("❌ 통합 테스트: 실패")
        
        if summary_result.returncode == 0:
            print("✅ 전체 테스트: 통과")
        else:
            print("❌ 전체 테스트: 실패")
            
        print()
        
        # 6. 추가 정보
        if unit_result.returncode == 0 and integration_result.returncode == 0:
            print("🎉 모든 테스트가 성공적으로 통과했습니다!")
            print("✨ 설정 관리 시스템이 올바르게 구현되었습니다.")
            
            # 예제 실행 제안
            print()
            print("💡 다음 단계:")
            print("   python setup_configuration.py  # 설정 관리 실행")
            print("   python example_usage.py        # 사용 예제 실행")
        else:
            print("⚠️  일부 테스트가 실패했습니다.")
            print("   로그를 확인하여 문제를 해결해주세요.")
    
    except FileNotFoundError:
        print("❌ Python 또는 pytest를 찾을 수 없습니다.")
        print("   Python과 필요한 패키지가 설치되어 있는지 확인해주세요.")
    
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")


def run_specific_test_file(test_file):
    """특정 테스트 파일 실행"""
    print(f"🧪 {test_file} 실행...")
    print("-" * 50)
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent / "src")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        test_file, 
        "-v", 
        "--tb=short"
    ], env=env)
    
    return result.returncode == 0


def check_test_coverage():
    """테스트 커버리지 확인"""
    print("📊 테스트 커버리지 확인...")
    
    try:
        # pytest-cov 설치 확인
        result = subprocess.run([sys.executable, "-m", "pytest", "--cov", "--help"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("⚠️  pytest-cov가 설치되지 않았습니다.")
            print("   pip install pytest-cov로 설치하면 커버리지를 확인할 수 있습니다.")
            return
        
        # 커버리지 실행
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent / "src")
        
        subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/",
            "--cov=src",
            "--cov-report=term-missing"
        ], env=env)
    
    except Exception as e:
        print(f"커버리지 확인 실패: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "unit":
            # 단위 테스트만 실행
            success = run_specific_test_file("tests/unit/")
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "integration":
            # 통합 테스트만 실행
            success = run_specific_test_file("tests/integration/")
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "coverage":
            # 커버리지 확인
            check_test_coverage()
            sys.exit(0)
        else:
            print("사용법: python run_tests.py [unit|integration|coverage]")
            sys.exit(1)
    else:
        main()
