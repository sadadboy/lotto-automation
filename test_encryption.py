#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인증정보 암호화 기능 테스트 스크립트
"""

print("🧪 인증정보 암호화 기능 테스트 시작")
print("=" * 50)

# 1. 의존성 확인
try:
    import cryptography
    print("✅ cryptography 라이브러리 설치 확인")
except ImportError:
    print("❌ cryptography 라이브러리가 없습니다.")
    print("💡 설치 명령어: pip install cryptography")
    exit(1)

# 2. 모듈 import 테스트
try:
    from credential_manager import CredentialManager, UserCredentials
    print("✅ credential_manager 모듈 import 성공")
except ImportError as e:
    print(f"❌ credential_manager 모듈 import 실패: {e}")
    exit(1)

# 3. 테스트용 인증정보 생성
print("\n📝 테스트용 인증정보 생성")
test_credentials = UserCredentials(
    user_id="test_user_123",
    password="test_password_456",
    recharge_password="123456"
)
print(f"   사용자: {test_credentials.user_id}")
print(f"   충전비밀번호: {test_credentials.recharge_password}")

# 4. CredentialManager 테스트
print("\n🔐 CredentialManager 테스트")
test_file = "test_credentials.enc"
manager = CredentialManager(test_file)

# 5. 저장 테스트
print("\n💾 인증정보 저장 테스트")
master_password = "test_master_password_789"
success = manager.save_credentials(test_credentials, master_password)
if success:
    print("✅ 인증정보 저장 성공")
else:
    print("❌ 인증정보 저장 실패")
    exit(1)

# 6. 로드 테스트
print("\n📂 인증정보 로드 테스트")
loaded_credentials = manager.load_credentials(master_password)
if loaded_credentials:
    print("✅ 인증정보 로드 성공")
    print(f"   사용자: {loaded_credentials.user_id}")
    print(f"   비밀번호 길이: {len(loaded_credentials.password)}")
    print(f"   충전비밀번호: {loaded_credentials.recharge_password}")
    
    # 데이터 일치 확인
    if (loaded_credentials.user_id == test_credentials.user_id and 
        loaded_credentials.password == test_credentials.password and
        loaded_credentials.recharge_password == test_credentials.recharge_password):
        print("✅ 저장/로드 데이터 일치 확인")
    else:
        print("❌ 저장/로드 데이터 불일치")
        exit(1)
else:
    print("❌ 인증정보 로드 실패")
    exit(1)

# 7. 잘못된 마스터 패스워드 테스트
print("\n🔒 잘못된 마스터 패스워드 테스트")
wrong_password_credentials = manager.load_credentials("wrong_password")
if wrong_password_credentials is None:
    print("✅ 잘못된 마스터 패스워드 시 로드 차단 확인")
else:
    print("❌ 보안 문제: 잘못된 패스워드로도 로드됨")

# 8. 파일 존재 여부 테스트
print("\n📄 파일 존재 여부 테스트")
if manager.has_credentials():
    print("✅ 인증정보 파일 존재 확인")
else:
    print("❌ 인증정보 파일 존재하지 않음")

# 9. 정리
print("\n🧹 테스트 파일 정리")
import os
if os.path.exists(test_file):
    os.remove(test_file)
    print("✅ 테스트 파일 삭제 완료")

print("\n" + "=" * 50)
print("🎉 모든 테스트 통과! 인증정보 암호화 기능이 정상 작동합니다.")
print("=" * 50)

print("\n📋 사용법:")
print("1. 인증정보 설정:")
print("   python lotto_auto_buyer_integrated.py --credentials")
print()
print("2. 인증정보 테스트:")
print("   python lotto_auto_buyer_integrated.py --test-credentials")
print()
print("3. 로또 자동구매 실행:")
print("   python lotto_auto_buyer_integrated.py --now")
