#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
필수 패키지 설치 및 환경 설정 스크립트
"""

import subprocess
import sys
import os

def install_cryptography():
    """cryptography 패키지 설치"""
    print("🔧 cryptography 패키지 설치 중...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'cryptography==41.0.7'])
        print("✅ cryptography 설치 완료")
        return True
    except Exception as e:
        print(f"❌ cryptography 설치 실패: {e}")
        return False

def test_cryptography():
    """cryptography 테스트"""
    try:
        from cryptography.fernet import Fernet
        print("✅ cryptography 모듈 동작 확인")
        return True
    except ImportError:
        print("❌ cryptography 모듈 import 실패")
        return False

def install_all_requirements():
    """전체 requirements.txt 설치"""
    print("📦 전체 패키지 설치 중...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ 전체 패키지 설치 완료")
        return True
    except Exception as e:
        print(f"❌ 패키지 설치 실패: {e}")
        return False

def main():
    """메인 실행"""
    print("🚀 환경 설정 스크립트 시작")
    print("=" * 50)
    
    # 1. cryptography 설치 시도
    if not test_cryptography():
        print("cryptography가 설치되지 않았습니다. 설치를 시도합니다...")
        if install_cryptography():
            if test_cryptography():
                print("✅ cryptography 설치 및 테스트 완료")
            else:
                print("⚠️ cryptography 설치됐지만 테스트 실패")
        else:
            print("❌ cryptography 설치 실패")
            print("수동으로 설치해주세요: pip install cryptography")
    else:
        print("✅ cryptography 이미 설치됨")
    
    # 2. 전체 requirements 설치
    if os.path.exists('requirements.txt'):
        print("\n📦 requirements.txt 기반 패키지 설치...")
        install_all_requirements()
    
    print("\n✅ 환경 설정 완료!")
    print("\n📋 다음 단계:")
    print("1. python lotto_auto_buyer_integrated.py --config")
    print("2. python lotto_auto_buyer_integrated.py --now")

if __name__ == "__main__":
    main()
