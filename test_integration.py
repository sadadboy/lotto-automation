#!/usr/bin/env python3
"""
통합 로또 자동구매 시스템 테스트 스크립트
"""

import sys
import os
import json
from pathlib import Path

def test_file_structure():
    """파일 구조 테스트"""
    print("=== 파일 구조 테스트 ===")
    
    files_to_check = [
        'lotto_auto_buyer.py',  # 기존 파일
        'lotto_auto_buyer_integrated_fixed.py',  # 새 파일
        'lotto_config.json',  # 설정 파일
        'auto_recharge.py',  # 자동충전
        'discord_notifier.py',  # 알림
        'credential_manager.py'  # 인증정보
    ]
    
    missing_files = []
    for file in files_to_check:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - 없음")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_method_coverage():
    """메서드 포함 여부 테스트"""
    print("\n=== 핵심 메서드 포함 테스트 ===")
    
    try:
        with open('lotto_auto_buyer_integrated_fixed.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_methods = [
            'buy_lotto_games',
            'get_purchase_numbers', 
            'setup_purchase_page',
            'click_number_enhanced',
            'select_auto_numbers',
            'select_semi_auto_numbers', 
            'select_manual_numbers',
            'complete_purchase',
            'take_screenshot',
            'save_purchase_history',
            'login',
            'check_balance'
        ]
        
        missing_methods = []
        for method in required_methods:
            if f'def {method}(' in content:
                print(f"  ✅ {method}() - 포함됨")
            else:
                print(f"  ❌ {method}() - 누락됨")
                missing_methods.append(method)
        
        return len(missing_methods) == 0
        
    except Exception as e:
        print(f"  ❌ 파일 읽기 실패: {e}")
        return False

def test_config_compatibility():
    """설정 파일 호환성 테스트"""
    print("\n=== 설정 파일 호환성 테스트 ===")
    
    try:
        with open('lotto_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_sections = ['purchase', 'payment', 'options']
        missing_sections = []
        
        for section in required_sections:
            if section in config:
                print(f"  ✅ {section} 섹션 - 존재")
            else:
                print(f"  ❌ {section} 섹션 - 누락")
                missing_sections.append(section)
        
        # purchase 섹션 상세 확인
        if 'purchase' in config:
            if 'lotto_list' in config['purchase']:
                lotto_list = config['purchase']['lotto_list']
                print(f"  ✅ lotto_list 설정 - {len(lotto_list)}개 항목")
                
                for i, item in enumerate(lotto_list):
                    if 'type' in item:
                        print(f"    - [{i+1}] {item['type']}: {item.get('numbers', [])}")
                    else:
                        print(f"    - [{i+1}] 타입 누락")
            else:
                print("  ❌ lotto_list 누락")
                missing_sections.append('lotto_list')
        
        return len(missing_sections) == 0
        
    except Exception as e:
        print(f"  ❌ 설정 파일 읽기 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 통합 로또 자동구매 시스템 테스트 시작\n")
    
    # 테스트 실행
    file_test = test_file_structure()
    method_test = test_method_coverage()
    config_test = test_config_compatibility()
    
    # 결과 종합
    print("\n" + "="*50)
    print("📊 테스트 결과 종합")
    print("="*50)
    
    tests = [
        ("파일 구조", file_test),
        ("메서드 포함", method_test),
        ("설정 호환성", config_test)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 총 {passed}/{len(tests)} 테스트 통과")
    
    if passed == len(tests):
        print("\n🎉 모든 테스트 통과! 1단계 완료 확인됨")
        print("💡 이제 실제 구매 테스트를 진행할 수 있습니다.")
        print("💡 사용법: python lotto_auto_buyer_integrated_fixed.py --config")
    else:
        print("\n⚠️ 일부 테스트 실패. 문제를 해결해야 합니다.")
    
    return passed == len(tests)

if __name__ == "__main__":
    main()
