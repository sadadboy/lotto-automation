# check_project_status.py - 프로젝트 상태 확인 스크립트
"""
로또 자동구매 시스템 - 설정 관리 프로젝트 상태 확인

현재 구현된 모든 기능의 상태를 확인하고 보고서를 생성합니다.
"""

import os
import sys
import importlib
import subprocess
from pathlib import Path
from typing import List, Dict, Any


def main():
    """메인 실행 함수"""
    print("🔍 로또 자동구매 시스템 - 프로젝트 상태 확인")
    print("=" * 60)
    
    # 현재 디렉토리 설정
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"📁 프로젝트 루트: {project_root}")
    print()
    
    # 전체 검사 결과
    all_checks = []
    
    # 1. 파일 구조 확인
    print("1️⃣ 파일 구조 확인")
    print("-" * 40)
    file_structure_result = check_file_structure()
    all_checks.append(("파일 구조", file_structure_result))
    print()
    
    # 2. 의존성 확인
    print("2️⃣ 의존성 확인")
    print("-" * 40)
    dependencies_result = check_dependencies()
    all_checks.append(("의존성", dependencies_result))
    print()
    
    # 3. 모듈 임포트 확인
    print("3️⃣ 모듈 임포트 확인")
    print("-" * 40)
    import_result = check_module_imports()
    all_checks.append(("모듈 임포트", import_result))
    print()
    
    # 4. 테스트 실행
    print("4️⃣ 테스트 실행")
    print("-" * 40)
    test_result = run_tests()
    all_checks.append(("테스트", test_result))
    print()
    
    # 5. 예제 실행
    print("5️⃣ 예제 실행")
    print("-" * 40)
    example_result = run_example()
    all_checks.append(("예제 실행", example_result))
    print()
    
    # 6. CLI 도구 확인
    print("6️⃣ CLI 도구 확인")
    print("-" * 40)
    cli_result = check_cli_tools()
    all_checks.append(("CLI 도구", cli_result))
    print()
    
    # 전체 결과 요약
    print_summary(all_checks)


def check_file_structure() -> Dict[str, Any]:
    """파일 구조 확인"""
    
    required_files = [
        # 소스 코드
        "src/domain/entities/configuration.py",
        "src/domain/entities/user_credentials.py", 
        "src/domain/entities/purchase_settings.py",
        "src/domain/entities/recharge_settings.py",
        "src/domain/repositories/configuration_repository.py",
        "src/domain/services/configuration_service.py",
        "src/application/usecases/configuration_usecase.py",
        "src/infrastructure/repositories/file_configuration_repository.py",
        "src/config/dependency_injection.py",
        "src/config/configuration_cli.py",
        
        # 테스트
        "tests/unit/test_configuration.py",
        "tests/unit/test_configuration_repository.py",
        "tests/unit/test_configuration_service.py", 
        "tests/unit/test_configuration_usecase.py",
        "tests/integration/test_configuration_integration.py",
        
        # 설정 및 스크립트
        "conftest.py",
        "pytest.ini",
        "requirements.txt",
        "setup_configuration.py",
        "run_tests.py",
        "example_usage.py",
        "CONFIGURATION_SYSTEM_README.md"
    ]
    
    missing_files = []
    existing_files = []
    total_size = 0
    
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            existing_files.append(file_path)
            total_size += full_path.stat().st_size
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    # 디렉토리 구조 확인
    required_dirs = [
        "src/domain/entities",
        "src/domain/repositories", 
        "src/domain/services",
        "src/application/usecases",
        "src/infrastructure/repositories",
        "src/config",
        "tests/unit",
        "tests/integration",
        "tests/fixtures"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    # 결과 요약
    success_rate = len(existing_files) / len(required_files) * 100
    
    print(f"\n📊 파일 구조 결과:")
    print(f"   존재하는 파일: {len(existing_files)}/{len(required_files)} ({success_rate:.1f}%)")
    print(f"   총 파일 크기: {total_size:,} bytes")
    
    if missing_files:
        print(f"   누락된 파일: {len(missing_files)}개")
    
    if missing_dirs:
        print(f"   누락된 디렉토리: {len(missing_dirs)}개")
    
    return {
        "success": len(missing_files) == 0 and len(missing_dirs) == 0,
        "existing_files": len(existing_files),
        "total_files": len(required_files),
        "success_rate": success_rate,
        "missing_files": missing_files,
        "missing_dirs": missing_dirs,
        "total_size": total_size
    }


def check_dependencies() -> Dict[str, Any]:
    """의존성 확인"""
    
    required_packages = [
        "cryptography",
        "pytest", 
        "pytest-mock"
    ]
    
    installed_packages = []
    missing_packages = []
    
    for package in required_packages:
        try:
            result = subprocess.run([
                sys.executable, "-c", f"import {package.replace('-', '_')}"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                installed_packages.append(package)
                print(f"✅ {package}")
            else:
                missing_packages.append(package)
                print(f"❌ {package}")
                
        except Exception:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    # Python 버전 확인
    python_version = sys.version_info
    python_ok = python_version >= (3, 8)
    
    print(f"\n🐍 Python 버전: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"   버전 요구사항: {'✅ 만족' if python_ok else '❌ 미만족 (3.8+ 필요)'}")
    
    return {
        "success": len(missing_packages) == 0 and python_ok,
        "installed_packages": installed_packages,
        "missing_packages": missing_packages,
        "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
        "python_ok": python_ok
    }


def check_module_imports() -> Dict[str, Any]:
    """모듈 임포트 확인"""
    
    # Python 패스에 src 추가
    src_path = Path(__file__).parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    modules_to_test = [
        "src.domain.entities.configuration",
        "src.domain.entities.user_credentials",
        "src.domain.entities.purchase_settings", 
        "src.domain.entities.recharge_settings",
        "src.domain.repositories.configuration_repository",
        "src.domain.services.configuration_service",
        "src.application.usecases.configuration_usecase",
        "src.infrastructure.repositories.file_configuration_repository",
        "src.config.dependency_injection",
        "src.config.configuration_cli"
    ]
    
    successful_imports = []
    failed_imports = []
    
    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            successful_imports.append(module_name)
            print(f"✅ {module_name}")
        except Exception as e:
            failed_imports.append((module_name, str(e)))
            print(f"❌ {module_name}: {e}")
    
    success_rate = len(successful_imports) / len(modules_to_test) * 100
    
    print(f"\n📦 모듈 임포트 결과:")
    print(f"   성공: {len(successful_imports)}/{len(modules_to_test)} ({success_rate:.1f}%)")
    
    return {
        "success": len(failed_imports) == 0,
        "successful_imports": len(successful_imports),
        "total_modules": len(modules_to_test),
        "success_rate": success_rate,
        "failed_imports": failed_imports
    }


def run_tests() -> Dict[str, Any]:
    """테스트 실행"""
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent / "src")
    
    try:
        # 간단한 테스트 실행 (출력 최소화)
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "--tb=no", 
            "-q"
        ], capture_output=True, text=True, env=env, timeout=60)
        
        success = result.returncode == 0
        
        if success:
            print("✅ 모든 테스트 통과")
        else:
            print("❌ 일부 테스트 실패")
        
        # 출력에서 테스트 결과 파싱
        lines = result.stdout.split('\n')
        test_summary = "결과를 파싱할 수 없음"
        
        for line in lines:
            if "passed" in line or "failed" in line or "error" in line:
                test_summary = line.strip()
                break
        
        print(f"   {test_summary}")
        
        return {
            "success": success,
            "output": result.stdout,
            "error": result.stderr,
            "summary": test_summary
        }
    
    except subprocess.TimeoutExpired:
        print("❌ 테스트 실행 시간 초과 (60초)")
        return {
            "success": False,
            "output": "",
            "error": "Timeout",
            "summary": "시간 초과"
        }
    
    except Exception as e:
        print(f"❌ 테스트 실행 실패: {e}")
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "summary": "실행 실패"
        }


def run_example() -> Dict[str, Any]:
    """예제 실행"""
    
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent / "src")
        
        result = subprocess.run([
            sys.executable, "example_usage.py"
        ], capture_output=True, text=True, env=env, timeout=30)
        
        success = result.returncode == 0 and "🎉 모든 예제가 성공적으로 완료되었습니다!" in result.stdout
        
        if success:
            print("✅ 예제 실행 성공")
        else:
            print("❌ 예제 실행 실패")
            if result.stderr:
                print(f"   오류: {result.stderr[:100]}...")
        
        return {
            "success": success,
            "output": result.stdout,
            "error": result.stderr
        }
    
    except subprocess.TimeoutExpired:
        print("❌ 예제 실행 시간 초과")
        return {"success": False, "error": "Timeout"}
    
    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        return {"success": False, "error": str(e)}


def check_cli_tools() -> Dict[str, Any]:
    """CLI 도구 확인"""
    
    cli_commands = [
        (["python", "-m", "src.config.configuration_cli", "--help"], "CLI 도움말"),
        (["python", "setup_configuration.py", "--help"], "설정 스크립트 도움말")
    ]
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent / "src")
    
    successful_commands = []
    failed_commands = []
    
    for command, description in cli_commands:
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                env=env, 
                timeout=10
            )
            
            # 도움말 명령은 exit code가 0이거나 usage 텍스트가 있으면 성공
            success = (result.returncode == 0 or 
                      "usage:" in result.stdout.lower() or 
                      "도움말" in result.stdout or
                      "help" in result.stdout.lower())
            
            if success:
                successful_commands.append(description)
                print(f"✅ {description}")
            else:
                failed_commands.append((description, result.stderr))
                print(f"❌ {description}")
                
        except Exception as e:
            failed_commands.append((description, str(e)))
            print(f"❌ {description}: {e}")
    
    return {
        "success": len(failed_commands) == 0,
        "successful_commands": len(successful_commands),
        "failed_commands": failed_commands
    }


def print_summary(all_checks: List[tuple]) -> None:
    """전체 결과 요약"""
    
    print("📊 전체 결과 요약")
    print("=" * 50)
    
    successful_checks = 0
    total_checks = len(all_checks)
    
    for check_name, result in all_checks:
        status = "✅ 통과" if result["success"] else "❌ 실패"
        print(f"{check_name:15s}: {status}")
        
        if result["success"]:
            successful_checks += 1
    
    success_rate = successful_checks / total_checks * 100
    
    print()
    print(f"🎯 전체 성공률: {successful_checks}/{total_checks} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print()
        print("🎉 축하합니다! 모든 검사를 통과했습니다!")
        print("✨ 설정 관리 시스템이 완벽하게 구현되었습니다.")
        print()
        print("💡 다음 단계:")
        print("   1. python setup_configuration.py    # 설정 관리 도구 실행")
        print("   2. python example_usage.py          # 사용 예제 확인")
        print("   3. 웹 대시보드 구현 시작")
        print("   4. AI 예측 모델 구현")
        
    elif success_rate >= 80:
        print()
        print("👍 대부분의 기능이 정상 작동합니다!")
        print("⚠️  일부 개선이 필요한 부분이 있습니다.")
        
    else:
        print()
        print("⚠️  여러 문제가 발견되었습니다.")
        print("🔧 문제를 해결한 후 다시 확인해주세요.")
    
    print()
    print("📝 상세 보고서는 위의 개별 검사 결과를 참고하세요.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 검사가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 검사 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
