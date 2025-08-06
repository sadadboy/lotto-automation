#!/usr/bin/env python3
"""
완전 자동화 로또 구매 시스템 - 통합 테스트 및 검증 스크립트
사용자 입력 없이 모든 설정이 올바른지 확인
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

class AutomationValidator:
    """자동화 시스템 검증 클래스"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.successes = []
        
    def log_success(self, message):
        """성공 로그"""
        print(f"✅ {message}")
        self.successes.append(message)
        
    def log_warning(self, message):
        """경고 로그"""
        print(f"⚠️  {message}")
        self.warnings.append(message)
        
    def log_error(self, message):
        """에러 로그"""
        print(f"❌ {message}")
        self.errors.append(message)
        
    def check_files(self):
        """필수 파일 존재 확인"""
        print("\n🔍 필수 파일 확인 중...")
        
        required_files = [
            'lotto_automated.py',          # 메인 자동화 스크립트
            'docker-compose.automated.yml', # 도커 컴포즈 설정
            'Dockerfile.optimized',        # 최적화된 도커파일
            '.env.automated',              # 환경변수 템플릿
            'run_automated.sh',            # 리눅스/맥 실행 스크립트
            'run_automated.bat',           # 윈도우 실행 스크립트
            'auto_recharge.py',            # 자동충전 모듈
            'discord_notifier.py',         # 알림 모듈
            'credential_manager.py',       # 인증정보 관리
            'lotto_config.json'            # 기본 설정
        ]
        
        for file in required_files:
            if os.path.exists(file):
                self.log_success(f"{file} 존재")
            else:
                self.log_error(f"{file} 누락")
    
    def check_docker_environment(self):
        """도커 환경 확인"""
        print("\n🐳 도커 환경 확인 중...")
        
        try:
            # Docker 설치 확인
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log_success(f"Docker 설치됨: {result.stdout.strip()}")
            else:
                self.log_error("Docker가 설치되지 않음")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log_error("Docker 명령어 실행 실패")
        
        try:
            # Docker Compose 확인
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log_success(f"Docker Compose 설치됨: {result.stdout.strip()}")
            else:
                self.log_error("Docker Compose가 설치되지 않음")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log_error("Docker Compose 명령어 실행 실패")
    
    def check_environment_variables(self):
        """환경변수 설정 확인"""
        print("\n🔧 환경변수 설정 확인 중...")
        
        # .env 파일 확인
        if os.path.exists('.env'):
            self.log_success(".env 파일 존재")
            
            # 환경변수 파싱
            env_vars = {}
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
                
                # 필수 환경변수 확인
                required_vars = ['LOTTO_USER_ID', 'LOTTO_PASSWORD']
                for var in required_vars:
                    if var in env_vars and env_vars[var] and env_vars[var] != f'your_lotto_{var.lower().split("_")[1]}':
                        self.log_success(f"{var} 설정됨")
                    else:
                        self.log_error(f"{var} 설정되지 않음 또는 기본값")
                
                # 선택적 환경변수 확인
                optional_vars = {
                    'LOTTO_PURCHASE_COUNT': '5',
                    'LOTTO_AUTO_RECHARGE': 'true',
                    'LOTTO_HEADLESS': 'true'
                }
                
                for var, default in optional_vars.items():
                    value = env_vars.get(var, default)
                    self.log_success(f"{var}: {value}")
                    
            except Exception as e:
                self.log_error(f".env 파일 파싱 실패: {e}")
        else:
            self.log_warning(".env 파일 없음 (.env.automated를 복사하세요)")
    
    def check_configuration(self):
        """설정 파일 확인"""
        print("\n⚙️ 설정 파일 확인 중...")
        
        if os.path.exists('lotto_config.json'):
            try:
                with open('lotto_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.log_success("설정 파일 로드 성공")
                
                # 필수 섹션 확인
                required_sections = ['purchase', 'payment', 'options']
                for section in required_sections:
                    if section in config:
                        self.log_success(f"'{section}' 섹션 존재")
                    else:
                        self.log_error(f"'{section}' 섹션 누락")
                
                # 구매 설정 확인
                if 'purchase' in config:
                    purchase = config['purchase']
                    if 'lotto_list' in purchase and isinstance(purchase['lotto_list'], list):
                        self.log_success(f"구매 설정: {len(purchase['lotto_list'])}개 게임")
                        
                        for i, game in enumerate(purchase['lotto_list']):
                            if 'type' in game:
                                game_type = game['type']
                                numbers = game.get('numbers', [])
                                self.log_success(f"  게임 {i+1}: {game_type} ({len(numbers)}개 번호)")
                            else:
                                self.log_error(f"  게임 {i+1}: 타입 누락")
                    else:
                        self.log_error("lotto_list 설정 오류")
                
            except json.JSONDecodeError as e:
                self.log_error(f"설정 파일 JSON 파싱 실패: {e}")
            except Exception as e:
                self.log_error(f"설정 파일 읽기 실패: {e}")
        else:
            self.log_error("lotto_config.json 파일 없음")
    
    def check_python_dependencies(self):
        """Python 의존성 확인"""
        print("\n🐍 Python 의존성 확인 중...")
        
        required_modules = [
            'selenium',
            'requests', 
            'numpy',
            'cryptography'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                self.log_success(f"{module} 설치됨")
            except ImportError:
                self.log_warning(f"{module} 미설치 (도커에서 자동 설치됨)")
    
    def check_automated_script(self):
        """자동화 스크립트 구문 확인"""
        print("\n📝 자동화 스크립트 확인 중...")
        
        try:
            # Python 구문 검사
            with open('lotto_automated.py', 'r', encoding='utf-8') as f:
                code = f.read()
            
            compile(code, 'lotto_automated.py', 'exec')
            self.log_success("자동화 스크립트 구문 검사 통과")
            
            # 핵심 클래스 확인
            if 'class AutomatedLottoBuyer' in code:
                self.log_success("AutomatedLottoBuyer 클래스 존재")
            else:
                self.log_error("AutomatedLottoBuyer 클래스 누락")
            
            # 핵심 메서드 확인
            required_methods = [
                'def buy_lotto_games',
                'def login', 
                'def check_balance',
                'def run'
            ]
            
            for method in required_methods:
                if method in code:
                    self.log_success(f"{method.split()[1]} 메서드 존재")
                else:
                    self.log_error(f"{method.split()[1]} 메서드 누락")
                    
        except SyntaxError as e:
            self.log_error(f"구문 오류: {e}")
        except Exception as e:
            self.log_error(f"스크립트 검사 실패: {e}")
    
    def check_docker_build(self):
        """도커 빌드 테스트"""
        print("\n🔨 도커 빌드 테스트 중...")
        
        try:
            # 도커 이미지 빌드 테스트 (실제 빌드는 하지 않고 Dockerfile만 검사)
            if os.path.exists('Dockerfile.optimized'):
                self.log_success("최적화된 Dockerfile 존재")
                
                # Dockerfile 내용 간단 검사
                with open('Dockerfile.optimized', 'r') as f:
                    dockerfile_content = f.read()
                
                if 'FROM python:3.11-slim' in dockerfile_content:
                    self.log_success("베이스 이미지 설정 확인")
                else:
                    self.log_warning("베이스 이미지 설정 확인 필요")
                
                if 'ENTRYPOINT' in dockerfile_content:
                    self.log_success("엔트리포인트 설정됨")
                else:
                    self.log_warning("엔트리포인트 설정 확인 필요")
            else:
                self.log_error("Dockerfile.optimized 없음")
                
        except Exception as e:
            self.log_error(f"도커 빌드 테스트 실패: {e}")
    
    def validate_automation_readiness(self):
        """완전 자동화 준비 상태 검증"""
        print("\n🤖 완전 자동화 준비 상태 검증 중...")
        
        # 사용자 입력이 필요한 코드 패턴 검사
        problematic_patterns = [
            'input(',
            'getpass.getpass',
            'raw_input',
            'sys.stdin.read'
        ]
        
        files_to_check = ['lotto_automated.py']
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                found_issues = []
                for pattern in problematic_patterns:
                    if pattern in content:
                        found_issues.append(pattern)
                
                if found_issues:
                    self.log_error(f"{file_path}에서 사용자 입력 코드 발견: {', '.join(found_issues)}")
                else:
                    self.log_success(f"{file_path} 완전 자동화 호환")
    
    def generate_report(self):
        """최종 보고서 생성"""
        print("\n" + "="*60)
        print("📊 완전 자동화 시스템 검증 보고서")
        print("="*60)
        
        print(f"✅ 성공: {len(self.successes)}개")
        print(f"⚠️  경고: {len(self.warnings)}개")
        print(f"❌ 오류: {len(self.errors)}개")
        
        if self.errors:
            print("\n🚨 오류 목록:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️ 경고 목록:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # 자동화 준비 상태 판정
        if not self.errors:
            print("\n🎉 완전 자동화 준비 완료!")
            print("💡 다음 명령어로 실행할 수 있습니다:")
            print("   Linux/Mac: ./run_automated.sh now")
            print("   Windows:   run_automated.bat now")
            print("   Docker:    docker-compose -f docker-compose.automated.yml --profile immediate up")
            return True
        else:
            print("\n🔧 오류를 수정한 후 다시 실행하세요.")
            return False
    
    def run_full_validation(self):
        """전체 검증 실행"""
        print("🔍 완전 자동화 로또 구매 시스템 검증 시작")
        print("=" * 60)
        
        self.check_files()
        self.check_docker_environment() 
        self.check_environment_variables()
        self.check_configuration()
        self.check_python_dependencies()
        self.check_automated_script()
        self.check_docker_build()
        self.validate_automation_readiness()
        
        return self.generate_report()

def main():
    """메인 함수"""
    validator = AutomationValidator()
    success = validator.run_full_validation()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
