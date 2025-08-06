#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로또 시스템 문제 해결 및 통합 스크립트
"""

import os
import sys
import shutil
import subprocess

def fix_import_issues():
    """Import 문제 해결"""
    print("🔧 Import 문제 해결 중...")
    
    # 1. __pycache__ 폴더 삭제
    cache_dirs = ['__pycache__', 'src/__pycache__']
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ {cache_dir} 삭제 완료")
            except Exception as e:
                print(f"⚠️ {cache_dir} 삭제 실패: {e}")
    
    # 2. 현재 디렉토리를 Python path에 추가
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print(f"✅ Python path에 {current_dir} 추가")
    
    # 3. auto_recharge 모듈 테스트
    try:
        import auto_recharge
        from auto_recharge import AutoRecharger
        print("✅ auto_recharge 모듈 import 성공")
        return True
    except Exception as e:
        print(f"❌ auto_recharge import 실패: {e}")
        return False

def create_integration_script():
    """Clean Architecture와 기존 코드 통합 스크립트"""
    print("🔄 Clean Architecture 통합 스크립트 생성 중...")
    
    integration_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean Architecture 통합 로또 시스템
"""

import sys
import os
import json
import logging
from pathlib import Path

# 현재 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Clean Architecture imports
try:
    from src.config.dependency_injection import DIContainer
    from src.application.usecases.configuration_usecase import ConfigurationUseCase
    from src.domain.entities.configuration import Configuration
    print("✅ Clean Architecture 모듈 import 성공")
    CLEAN_ARCHITECTURE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Clean Architecture 모듈 import 실패: {e}")
    print("기존 JSON 설정 방식을 사용합니다.")
    CLEAN_ARCHITECTURE_AVAILABLE = False

# 기존 모듈 imports
try:
    from auto_recharge import AutoRecharger
    print("✅ AutoRecharger import 성공")
except ImportError as e:
    print(f"❌ AutoRecharger import 실패: {e}")
    AutoRecharger = None

def load_configuration():
    """설정 로드 (Clean Architecture 우선, fallback to JSON)"""
    if CLEAN_ARCHITECTURE_AVAILABLE:
        try:
            # Clean Architecture 방식
            container = DIContainer()
            config_usecase = container.get_configuration_usecase()
            config = config_usecase.get_current_configuration()
            print("✅ Clean Architecture 설정 로드 성공")
            return config.to_dict()  # Configuration 객체를 dict로 변환
        except Exception as e:
            print(f"⚠️ Clean Architecture 설정 로드 실패: {e}")
    
    # JSON fallback 방식
    try:
        with open('lotto_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            print("✅ JSON 설정 로드 성공")
            return config
    except Exception as e:
        print(f"❌ 설정 로드 실패: {e}")
        return create_default_config()

def create_default_config():
    """기본 설정 생성"""
    return {
        "user_credentials": {
            "user_id": "",
            "password": ""
        },
        "purchase_settings": {
            "games_per_purchase": 5,
            "max_amount_per_game": 5000,
            "purchase_method": "auto",
            "number_selection_method": "mixed"
        },
        "payment": {
            "auto_recharge": False,
            "recharge_amount": 50000,
            "min_balance": 5000,
            "recharge_method": "account_transfer"
        }
    }

def main():
    """메인 실행 함수"""
    print("🚀 통합 로또 시스템 시작")
    
    # 설정 로드
    config = load_configuration()
    print(f"📋 설정 로드 완료")
    
    # AutoRecharger 테스트
    if AutoRecharger and config.get('payment', {}).get('auto_recharge'):
        try:
            recharger = AutoRecharger(config)
            print("✅ AutoRecharger 초기화 성공")
        except Exception as e:
            print(f"⚠️ AutoRecharger 초기화 실패: {e}")
    
    print("✅ 시스템 통합 완료!")
    return True

if __name__ == "__main__":
    # Import 문제 해결
    if not fix_import_issues():
        print("❌ Import 문제 해결 실패")
        sys.exit(1)
    
    # 메인 실행
    main()
'''
    
    with open('integrated_lotto_system.py', 'w', encoding='utf-8') as f:
        f.write(integration_code)
    
    print("✅ 통합 스크립트 생성 완료: integrated_lotto_system.py")

def main():
    """메인 실행"""
    print("🔧 로또 시스템 문제 해결 및 통합 시작")
    
    # 1. Import 문제 해결
    if fix_import_issues():
        print("✅ Import 문제 해결 완료")
    else:
        print("⚠️ Import 문제가 있지만 계속 진행합니다")
    
    # 2. 통합 스크립트 생성
    create_integration_script()
    
    print("\n🎉 문제 해결 및 통합 완료!")
    print("\n📋 다음 단계:")
    print("1. python integrated_lotto_system.py 실행해서 테스트")
    print("2. python lotto_auto_buyer.py --now 다시 시도")
    print("3. 문제 지속시 가상환경 재설정 필요")

if __name__ == "__main__":
    main()
