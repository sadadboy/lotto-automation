#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전체 시스템 최종 테스트 및 문제 해결
"""

import subprocess
import sys
import os
import json

def install_cryptography():
    """cryptography 설치"""
    print("🔧 cryptography 패키지 설치 중...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'cryptography==41.0.7'])
        print("✅ cryptography 설치 완료")
        return True
    except Exception as e:
        print(f"❌ cryptography 설치 실패: {e}")
        return False

def check_config_file():
    """설정 파일 확인"""
    config_file = "lotto_config.json"
    print(f"\n📋 설정 파일 확인: {config_file}")
    
    if not os.path.exists(config_file):
        print(f"❌ 설정 파일이 없습니다: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 필수 설정 확인
        checks = [
            ("login.user_id", config.get('login', {}).get('user_id')),
            ("login.password", config.get('login', {}).get('password')),
            ("payment.auto_recharge", config.get('payment', {}).get('auto_recharge')),
            ("payment.min_balance", config.get('payment', {}).get('min_balance')),
            ("purchase.count", config.get('purchase', {}).get('count'))
        ]
        
        print("📋 설정 항목 확인:")
        all_ok = True
        for key, value in checks:
            if value is not None and value != "":
                print(f"  ✅ {key}: {value}")
            else:
                print(f"  ❌ {key}: 누락됨")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"❌ 설정 파일 읽기 실패: {e}")
        return False

def test_imports():
    """모듈 import 테스트"""
    print("\n🧪 모듈 Import 테스트:")
    
    # 1. auto_recharge 테스트
    try:
        from auto_recharge import AutoRecharger
        print("  ✅ AutoRecharger import 성공")
        
        # 테스트 인스턴스 생성
        test_config = {'payment': {'auto_recharge': True}}
        recharger = AutoRecharger(test_config)
        print("  ✅ AutoRecharger 인스턴스 생성 성공")
        
    except Exception as e:
        print(f"  ❌ AutoRecharger 테스트 실패: {e}")
        return False
    
    # 2. lotto_auto_buyer 테스트
    try:
        # 기존 모듈 리로드
        if 'lotto_auto_buyer' in sys.modules:
            del sys.modules['lotto_auto_buyer']
        
        import lotto_auto_buyer
        print("  ✅ lotto_auto_buyer import 성공")
        
        # LottoAutoBuyer 인스턴스 생성 (실제 설정 파일 사용)
        if os.path.exists('lotto_config.json'):
            buyer = lotto_auto_buyer.LottoAutoBuyer()
            print("  ✅ LottoAutoBuyer 인스턴스 생성 성공")
            
            # recharger 상태 확인
            if hasattr(buyer, 'recharger') and buyer.recharger:
                print("  ✅ AutoRecharger 초기화 성공")
            else:
                print("  ⚠️ AutoRecharger 초기화 실패 (설정 확인 필요)")
        else:
            print("  ⚠️ 설정 파일이 없어 기본 인스턴스로 테스트")
            
    except Exception as e:
        print(f"  ❌ lotto_auto_buyer 테스트 실패: {e}")
        return False
    
    # 3. 통합 버전 테스트
    try:
        if 'lotto_auto_buyer_integrated' in sys.modules:
            del sys.modules['lotto_auto_buyer_integrated']
            
        import lotto_auto_buyer_integrated
        print("  ✅ lotto_auto_buyer_integrated import 성공")
        
        # ConfigurationManager 테스트
        config_mgr = lotto_auto_buyer_integrated.ConfigurationManager()
        config = config_mgr.load_configuration()
        print("  ✅ ConfigurationManager 테스트 성공")
        
        # 호환성 확인
        credentials = config_mgr.get_user_credentials()
        if credentials.get('user_id') and credentials.get('password'):
            print("  ✅ 사용자 인증정보 호환성 확인")
        else:
            print("  ❌ 사용자 인증정보 누락")
        
    except Exception as e:
        print(f"  ❌ 통합 버전 테스트 실패: {e}")
        return False
    
    return True

def run_quick_tests():
    """빠른 실행 테스트"""
    print("\n🚀 빠른 실행 테스트:")
    
    tests = [
        ("원래 버전 도움말", ["python", "lotto_auto_buyer.py"]),
        ("통합 버전 설정 확인", ["python", "lotto_auto_buyer_integrated.py", "--config"]),
    ]
    
    for test_name, command in tests:
        print(f"\n📍 {test_name}:")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✅ 성공")
                if "사용법" in result.stdout or "설정" in result.stdout:
                    print(f"  📄 출력 확인됨")
            else:
                print(f"  ❌ 실패 (코드: {result.returncode})")
                if result.stderr:
                    print(f"  오류: {result.stderr[:200]}...")
        except subprocess.TimeoutExpired:
            print(f"  ⏰ 시간 초과")
        except Exception as e:
            print(f"  ❌ 실행 실패: {e}")

def main():
    """메인 실행"""
    print("🚀 로또 시스템 최종 점검 및 문제 해결")
    print("=" * 60)
    
    # 1. cryptography 설치 확인
    try:
        import cryptography
        print("✅ cryptography 이미 설치됨")
    except ImportError:
        print("❌ cryptography 없음 - 설치 시도")
        if not install_cryptography():
            print("⚠️ cryptography 설치 실패했지만 계속 진행")
    
    # 2. 설정 파일 확인
    config_ok = check_config_file()
    
    # 3. Import 테스트
    import_ok = test_imports()
    
    # 4. 빠른 실행 테스트
    run_quick_tests()
    
    # 결과 종합
    print("\n" + "=" * 60)
    print("🏁 최종 점검 결과:")
    print(f"  📋 설정 파일: {'✅ OK' if config_ok else '❌ 문제 있음'}")
    print(f"  🧪 모듈 Import: {'✅ OK' if import_ok else '❌ 문제 있음'}")
    
    if config_ok and import_ok:
        print("\n🎉 모든 검사 통과! 이제 실제 실행 가능합니다.")
        print("\n📋 다음 단계:")
        print("1. 원래 버전: python lotto_auto_buyer.py --now")
        print("2. 통합 버전: python lotto_auto_buyer_integrated.py --now")
        print("\n💡 팁:")
        print("- 자동충전 로그를 자세히 확인하세요")
        print("- 첫 실행시 테스트 계정으로 시도해보세요")
    else:
        print("\n❌ 문제가 있습니다. 위의 오류를 해결한 후 다시 시도하세요.")
    
    return config_ok and import_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
