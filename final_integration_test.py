#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 통합 테스트 스크립트
"""

import sys
import os

def test_import_fixes():
    """Import 수정 사항 테스트"""
    print("🧪 Import 수정 사항 테스트 시작")
    print("=" * 50)
    
    # 현재 디렉토리를 Python path에 추가
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print(f"✅ Python path에 현재 디렉토리 추가: {current_dir}")
    
    # 1. auto_recharge 모듈 테스트
    print("\n1️⃣ auto_recharge 모듈 테스트:")
    try:
        import auto_recharge
        print("  ✅ auto_recharge 모듈 import 성공")
        
        from auto_recharge import AutoRecharger
        print("  ✅ AutoRecharger 클래스 import 성공")
        
        # 테스트 설정으로 인스턴스 생성
        test_config = {
            'payment': {
                'auto_recharge': True,
                'recharge_amount': 50000,
                'min_balance': 5000,
                'recharge_method': 'account_transfer'
            }
        }
        
        recharger = AutoRecharger(test_config)
        print("  ✅ AutoRecharger 인스턴스 생성 성공")
        
    except Exception as e:
        print(f"  ❌ auto_recharge 테스트 실패: {e}")
        return False
    
    # 2. lotto_auto_buyer 모듈 테스트
    print("\n2️⃣ lotto_auto_buyer 모듈 테스트:")
    try:
        # 기존 모듈을 다시 로드
        if 'lotto_auto_buyer' in sys.modules:
            del sys.modules['lotto_auto_buyer']
        
        import lotto_auto_buyer
        print("  ✅ lotto_auto_buyer 모듈 import 성공")
        
        # LottoAutoBuyer 클래스 테스트
        buyer = lotto_auto_buyer.LottoAutoBuyer()
        print("  ✅ LottoAutoBuyer 인스턴스 생성 성공")
        
        # recharger 상태 확인
        if hasattr(buyer, 'recharger'):
            if buyer.recharger is not None:
                print("  ✅ 자동충전 기능 활성화됨")
            else:
                print("  ℹ️ 자동충전 기능 비활성화됨 (정상 - 설정에 따라)")
        
    except Exception as e:
        print(f"  ❌ lotto_auto_buyer 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ 모든 import 테스트 통과!")
    return True

def test_command_line():
    """명령행 실행 테스트"""
    print("\n3️⃣ 명령행 실행 테스트:")
    try:
        import lotto_auto_buyer
        
        # --now 없이 실행 (도움말만 출력)
        import sys
        original_argv = sys.argv[:]
        sys.argv = ['lotto_auto_buyer.py']
        
        # main() 함수 실행해보기
        try:
            lotto_auto_buyer.main()
            print("  ✅ 도움말 출력 성공")
        except SystemExit:
            print("  ✅ 도움말 출력 성공 (SystemExit)")
        finally:
            sys.argv = original_argv
        
        return True
        
    except Exception as e:
        print(f"  ❌ 명령행 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 로또 시스템 최종 통합 테스트")
    print("=" * 60)
    
    all_passed = True
    
    # Import 테스트
    if not test_import_fixes():
        all_passed = False
    
    # 명령행 테스트
    if not test_command_line():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 모든 테스트 통과!")
        print("\n📋 다음 단계:")
        print("1. python lotto_auto_buyer.py --now")
        print("2. 실제 로또 구매 테스트")
        print("3. 설정 파일 확인 및 수정")
    else:
        print("❌ 일부 테스트 실패")
        print("문제를 해결한 후 다시 시도해주세요.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
