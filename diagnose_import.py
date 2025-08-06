#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import 문제 진단 및 해결 스크립트
"""

import sys
import os
import importlib.util
import shutil

def diagnose_import_issue():
    """Import 문제 진단"""
    print("🔍 Import 문제 진단 시작...")
    
    # 1. 기본 환경 정보
    print(f"\n📍 Python 버전: {sys.version}")
    print(f"📍 현재 디렉토리: {os.getcwd()}")
    print(f"📍 Python 실행 경로: {sys.executable}")
    
    # 2. 파일 존재 확인
    auto_recharge_file = "auto_recharge.py"
    print(f"\n📁 파일 존재 확인:")
    print(f"  - auto_recharge.py: {os.path.exists(auto_recharge_file)}")
    print(f"  - lotto_auto_buyer.py: {os.path.exists('lotto_auto_buyer.py')}")
    
    if os.path.exists(auto_recharge_file):
        with open(auto_recharge_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"  - 파일 크기: {len(content)} characters")
            print(f"  - AutoRecharger 클래스: {'class AutoRecharger:' in content}")
    
    # 3. Python path 확인
    print(f"\n🛤️ Python path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    
    # 4. __pycache__ 정리
    cache_dir = "__pycache__"
    if os.path.exists(cache_dir):
        print(f"\n🗑️ {cache_dir} 폴더 삭제 중...")
        try:
            shutil.rmtree(cache_dir)
            print(f"  ✅ {cache_dir} 삭제 성공")
        except Exception as e:
            print(f"  ⚠️ {cache_dir} 삭제 실패: {e}")
    
    # 5. 현재 디렉토리를 Python path에 추가
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print(f"\n➕ Python path에 현재 디렉토리 추가: {current_dir}")
    
    # 6. Import 테스트
    print(f"\n🧪 Import 테스트:")
    
    # 6-1. importlib을 사용한 저수준 테스트
    try:
        spec = importlib.util.spec_from_file_location("auto_recharge", auto_recharge_file)
        if spec is None:
            print("  ❌ importlib.util.spec_from_file_location 실패")
            return False
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print("  ✅ importlib을 통한 모듈 로드 성공")
        
        # AutoRecharger 클래스 확인
        if hasattr(module, 'AutoRecharger'):
            print("  ✅ AutoRecharger 클래스 확인")
        else:
            print("  ❌ AutoRecharger 클래스 없음")
            return False
            
    except Exception as e:
        print(f"  ❌ importlib 테스트 실패: {e}")
        return False
    
    # 6-2. 일반 import 테스트
    try:
        import auto_recharge
        print("  ✅ import auto_recharge 성공")
        
        from auto_recharge import AutoRecharger
        print("  ✅ from auto_recharge import AutoRecharger 성공")
        
        # 인스턴스 생성 테스트
        test_config = {'payment': {'auto_recharge': True}}
        recharger = AutoRecharger(test_config)
        print("  ✅ AutoRecharger 인스턴스 생성 성공")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import 에러: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 기타 에러: {e}")
        return False

def fix_import_issue():
    """Import 문제 해결"""
    print("\n🔧 Import 문제 해결 시도...")
    
    # 1. 권한 확인 및 수정
    auto_recharge_file = "auto_recharge.py"
    if os.path.exists(auto_recharge_file):
        try:
            # 파일 읽기 권한 확인
            with open(auto_recharge_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"  ✅ 파일 읽기 권한 정상")
            
            # 파일 시작에 인코딩 선언 추가 (필요시)
            if not content.startswith('# -*- coding: utf-8 -*-') and not content.startswith('#!/usr/bin/env python'):
                print("  🔧 파일 인코딩 선언 추가")
                new_content = '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n' + content
                with open(auto_recharge_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print("  ✅ 인코딩 선언 추가 완료")
                
        except Exception as e:
            print(f"  ❌ 파일 권한 문제: {e}")
            return False
    
    # 2. __init__.py 파일 생성 (필요시)
    init_file = "__init__.py"
    if not os.path.exists(init_file):
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('# -*- coding: utf-8 -*-\n')
        print(f"  ✅ {init_file} 생성 완료")
    
    return True

def create_test_script():
    """테스트 스크립트 생성"""
    test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Recharge Import 테스트
"""

import sys
import os

# 현재 디렉토리를 Python path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_import():
    """Import 테스트"""
    print("🧪 Auto Recharge Import 테스트 시작")
    
    try:
        print("1. auto_recharge 모듈 import...")
        import auto_recharge
        print("   ✅ 성공")
        
        print("2. AutoRecharger 클래스 import...")
        from auto_recharge import AutoRecharger
        print("   ✅ 성공")
        
        print("3. AutoRecharger 인스턴스 생성...")
        config = {
            'payment': {
                'auto_recharge': True,
                'recharge_amount': 50000,
                'min_balance': 5000,
                'recharge_method': 'account_transfer'
            }
        }
        recharger = AutoRecharger(config)
        print("   ✅ 성공")
        
        print("\\n🎉 모든 테스트 통과!")
        return True
        
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import()
    if success:
        print("\\n✅ auto_recharge 모듈이 정상적으로 작동합니다!")
    else:
        print("\\n❌ auto_recharge 모듈에 문제가 있습니다.")
        sys.exit(1)
'''
    
    with open('test_auto_recharge_import.py', 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    print("\n📝 테스트 스크립트 생성: test_auto_recharge_import.py")

def main():
    """메인 실행"""
    print("🚀 Auto Recharge Import 문제 해결 시작")
    print("=" * 50)
    
    # 1. 문제 진단
    if diagnose_import_issue():
        print("\n✅ Import 문제 없음 - 정상 작동")
    else:
        print("\n⚠️ Import 문제 발견 - 해결 시도")
        
        # 2. 문제 해결
        if fix_import_issue():
            print("\n🔄 문제 해결 후 재테스트...")
            if diagnose_import_issue():
                print("\n✅ 문제 해결 완료!")
            else:
                print("\n❌ 문제 해결 실패")
        else:
            print("\n❌ 문제 해결 실패")
    
    # 3. 테스트 스크립트 생성
    create_test_script()
    
    print("\n" + "=" * 50)
    print("🏁 진단 완료!")
    print("\n📋 다음 단계:")
    print("1. python test_auto_recharge_import.py 실행")
    print("2. python lotto_auto_buyer.py --now 재시도")

if __name__ == "__main__":
    main()
