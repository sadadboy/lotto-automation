# conftest.py - pytest 설정 및 픽스처
import sys
import os
import pytest

# src 디렉토리를 Python 패스에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

@pytest.fixture
def sample_user_credentials():
    """테스트용 사용자 인증 정보"""
    from src.domain.entities.user_credentials import UserCredentials
    return UserCredentials(user_id="test_user", password="test_password")

@pytest.fixture  
def sample_purchase_settings():
    """테스트용 구매 설정"""
    from src.domain.entities.purchase_settings import PurchaseSettings
    return PurchaseSettings(
        schedule_time="14:00",
        purchase_count=3,
        lotto_list=[
            {"type": "자동", "numbers": []},
            {"type": "수동", "numbers": [1, 2, 3, 4, 5, 6]},
            {"type": "반자동", "numbers": [7, 8, 9]}
        ]
    )

@pytest.fixture
def sample_recharge_settings():
    """테스트용 충전 설정"""
    from src.domain.entities.recharge_settings import RechargeSettings
    return RechargeSettings(
        auto_recharge=True,
        minimum_balance=5000,
        recharge_amount=50000
    )
