#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import 테스트 스크립트
"""

import sys
import os

print("=== Import 테스트 시작 ===")
print(f"Python 버전: {sys.version}")
print(f"현재 디렉토리: {os.getcwd()}")
print(f"Python 경로: {sys.path}")

# 파일 존재 확인
auto_recharge_path = "auto_recharge.py"
print(f"\n파일 존재 확인: {auto_recharge_path}")
print(f"파일 존재: {os.path.exists(auto_recharge_path)}")

if os.path.exists(auto_recharge_path):
    with open(auto_recharge_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"파일 크기: {len(content)} characters")
        print("AutoRecharger 클래스 존재:", "class AutoRecharger:" in content)

# Import 테스트
print("\n=== Import 테스트 ===")
try:
    print("1. auto_recharge 모듈 import 시도...")
    import auto_recharge
    print("✅ auto_recharge 모듈 import 성공")
    
    print("2. AutoRecharger 클래스 import 시도...")
    from auto_recharge import AutoRecharger
    print("✅ AutoRecharger 클래스 import 성공")
    
    print("3. AutoRecharger 클래스 인스턴스 생성 시도...")
    test_config = {'payment': {'auto_recharge': True}}
    recharger = AutoRecharger(test_config)
    print("✅ AutoRecharger 인스턴스 생성 성공")
    
except ImportError as e:
    print(f"❌ Import 에러: {e}")
except Exception as e:
    print(f"❌ 기타 에러: {e}")

print("\n=== 테스트 완료 ===")
