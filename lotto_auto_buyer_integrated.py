#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean Architecture 통합 로또 자동구매 시스템
기존 lotto_auto_buyer.py를 Clean Architecture와 통합한 버전
"""

import sys
import os
import json
import time
import logging
import random
import argparse
from datetime import datetime
from collections import Counter
from pathlib import Path
import numpy as np

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 현재 디렉토리를 Python path에 추가 (import 문제 해결)
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Clean Architecture imports (optional)
CLEAN_ARCHITECTURE_AVAILABLE = False
try:
    from src.config.dependency_injection import DIContainer
    from src.application.usecases.configuration_usecase import ConfigurationUseCase
    from src.domain.entities.configuration import Configuration
    CLEAN_ARCHITECTURE_AVAILABLE = True
    print("✅ Clean Architecture 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ Clean Architecture 모듈 로드 실패: {e}")
    print("기존 JSON 설정 방식을 사용합니다.")

# AutoRecharger import (with fallback)
AutoRecharger = None
try:
    from auto_recharge import AutoRecharger
    print("✅ AutoRecharger 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ AutoRecharger 모듈 로드 실패: {e}")
    print("자동충전 기능이 비활성화됩니다.")

# CredentialManager import (with fallback)
CredentialManager = None
try:
    from credential_manager import CredentialManager, UserCredentials
    print("✅ CredentialManager 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ CredentialManager 모듈 로드 실패: {e}")
    print("인증정보 암호화 기능이 비활성화됩니다.")

# Discord Notifier import (with fallback)
NotificationManager = None
try:
    from discord_notifier import NotificationManager, run_notification
    print("✅ Discord 알림 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ Discord 알림 모듈 로드 실패: {e}")
    print("Discord 알림 기능이 비활성화됩니다.")

class ConfigurationManager:
    """설정 관리자 - Clean Architecture와 JSON 설정을 통합"""
    
    def __init__(self):
        self.config = None
        self.config_usecase = None
        self.credential_manager = None
        
        # 암호화 인증정보 관리자 초기화
        if CredentialManager:
            try:
                credentials_file = "credentials.enc"
                # config에서 파일 경로 확인
                if hasattr(self, 'config') and self.config:
                    security_config = self.config.get('security', {})
                    credentials_file = security_config.get('credentials_file', credentials_file)
                
                self.credential_manager = CredentialManager(credentials_file)
                print(f"✅ 암호화 인증정보 관리자 초기화: {credentials_file}")
            except Exception as e:
                print(f"⚠️ 암호화 인증정보 관리자 초기화 실패: {e}")
                self.credential_manager = None
        
    def load_configuration(self):
        """설정 로드 (Clean Architecture 우선, fallback to JSON)"""
        if CLEAN_ARCHITECTURE_AVAILABLE:
            try:
                container = DIContainer()
                self.config_usecase = container.get_configuration_usecase()
                config_entity = self.config_usecase.get_current_configuration()
                if config_entity:
                    self.config = config_entity.to_dict_compatible()  # 호훈성 메서드 사용
                    print("✅ Clean Architecture 설정 로드 성공")
                    return self.config
                else:
                    print("⚠️ Clean Architecture 설정 비어있음 - JSON fallback 사용")
                    raise Exception("Configuration is None")
            except Exception as e:
                print(f"⚠️ Clean Architecture 설정 로드 실패: {e}")
        
        # JSON fallback
        try:
            with open('lotto_config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                print("✅ JSON 설정 파일 로드")
                return self.config
        except Exception as e:
            print(f"⚠️ JSON 설정 로드 실패: {e}")
            self.config = self._create_default_config()
            return self.config
    
    def _create_default_config(self):
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
    
    def get_user_credentials(self, force_input=False):
        """사용자 인증정보 반환 (암호화 우선, JSON fallback)"""
        
        # 1. 암호화된 인증정보 시도 (우선)
        if self.credential_manager and not force_input:
            try:
                if self.credential_manager.has_credentials():
                    credentials = self.credential_manager.load_credentials()
                    if credentials:
                        print("✅ 암호화된 인증정보 로드 성공")
                        return {
                            'user_id': credentials.user_id,
                            'password': credentials.password,
                            'recharge_password': credentials.recharge_password
                        }
                    else:
                        print("⚠️ 암호화된 인증정보 로드 실패 - JSON fallback 사용")
                else:
                    print("📝 암호화된 인증정보 파일이 없음 - 설정 필요")
            except Exception as e:
                print(f"⚠️ 인증정보 로드 오류: {e}")
        
        # 2. JSON 설정 fallback
        if 'user_credentials' in self.config:
            creds = self.config['user_credentials']
            print("ℹ️ JSON 설정에서 인증정보 로드")
            return creds
        elif 'login' in self.config:
            creds = {
                'user_id': self.config['login'].get('user_id', ''),
                'password': self.config['login'].get('password', ''),
                'recharge_password': ''
            }
            print("ℹ️ JSON 레거시 설정에서 인증정보 로드")
            return creds
        else:
            print("❌ 인증정보가 없음 - 설정 필요")
            return {'user_id': '', 'password': '', 'recharge_password': ''}
    
    def get_purchase_settings(self):
        """구매 설정 반환 (기존/신규 구조 모두 지원)"""
        # 새로운 구조 시도
        if 'purchase_settings' in self.config:
            return self.config['purchase_settings']
        # 기존 구조 fallback
        elif 'purchase' in self.config:
            purchase = self.config['purchase']
            return {
                'games_per_purchase': purchase.get('count', 5),
                'max_amount_per_game': 1000,  # 기본값
                'purchase_method': 'auto',
                'number_selection_method': 'mixed',
                'lotto_list': purchase.get('lotto_list', [])
            }
        else:
            return {
                'games_per_purchase': 5,
                'max_amount_per_game': 5000,
                'purchase_method': 'auto',
                'number_selection_method': 'mixed'
            }
    
    def get_payment_settings(self):
        """결제 설정 반환"""
        return self.config.get('payment', {})
    
    def setup_credentials(self, force_new=False):
        """인증정보 설정 (암호화 저장)"""
        if not self.credential_manager:
            print("❌ CredentialManager가 사용할 수 없습니다.")
            return False
    
    def buy_lotto_games(self, purchase_count):
        """로또 구매 실행 - 기존 작동 로직"""
        try:
            self.logger.info(f"🎯 로또 구매 시작 ({purchase_count}게임)...")
            
            # 설정 파일에서 lotto_list 가져오기
            purchase_settings = self.config_manager.get_purchase_settings()
            lotto_list = purchase_settings.get('lotto_list', [{'type': '자동', 'numbers': []}])
            self.logger.info(f"📋 설정 파일 lotto_list: {lotto_list}")
            
            success_count = 0
            
            for i in range(purchase_count):
                try:
                    # 설정 파일의 해당 인덱스 구매 정보 가져오기
                    if i < len(lotto_list):
                        purchase_info = lotto_list[i]
                    else:
                        # 설정보다 많이 구매하는 경우 마지막 설정 반복
                        purchase_info = lotto_list[-1] if lotto_list else {'type': '자동', 'numbers': []}
                    
                    p_type = purchase_info['type']
                    numbers = self.get_purchase_numbers(purchase_info)
                    
                    self.logger.info(f"")
                    self.logger.info(f"🎮 [{i+1}/{purchase_count}] {p_type} 구매 시작...")
                    self.logger.info(f"📋 사용할 번호: {numbers}")
                    
                    if not self.setup_purchase_page(1):
                        continue
                    
                    # 구매 방식에 따른 처리
                    if p_type == '자동':
                        if self.select_auto_numbers():
                            self.logger.info(f"    ✅ 자동 번호 선택 완료")
                        else:
                            continue
                            
                    elif p_type == '반자동':
                        if self.select_semi_auto_numbers(numbers):
                            self.logger.info(f"    ✅ 반자동 번호 선택 완료: {numbers}")
                        else:
                            continue
                            
                    elif '수동' in p_type:
                        if self.select_manual_numbers(numbers):
                            self.logger.info(f"    ✅ 수동 번호 선택 완료: {numbers}")
                        else:
                            continue
                    
                    # 구매 완료
                    if self.complete_purchase():
                        success_count += 1
                        self.logger.info(f"    🎉 [{i+1}] {p_type} 구매 성공!")
                        
                        # 스크린샷 저장
                        screenshot_enabled = self.config.get('options', {}).get('save_screenshot', True)
                        if screenshot_enabled:
                            self.take_screenshot(f"purchase_{i+1}_{p_type}")
                        
                        time.sleep(3)
                    else:
                        self.logger.warning(f"    ❌ [{i+1}] {p_type} 구매 실패")
                        
                except Exception as e:
                    self.logger.error(f"[{i+1}] 구매 중 오류: {e}")
                    continue
            
            return success_count
            
        except Exception as e:
            self.logger.error(f"로또 구매 실패: {e}")
            return 0
    
    def get_purchase_numbers(self, purchase_info):
        """설정 파일에서 번호 가져오기 또는 생성"""
        p_type = purchase_info['type']
        config_numbers = purchase_info.get('numbers', [])
        
        self.logger.info(f"📋 설정 파일 확인 - {p_type}: {config_numbers}")
        
        # 설정 파일에 번호가 있으면 그것을 사용
        if config_numbers:
            if p_type == '반자동' and len(config_numbers) == 3:
                self.logger.info(f"✅ 설정 파일의 반자동 번호 사용: {config_numbers}")
                return config_numbers
            elif p_type.startswith('수동') and len(config_numbers) == 6:
                self.logger.info(f"✅ 설정 파일의 수동 번호 사용: {config_numbers}")
                return config_numbers
            else:
                self.logger.warning(f"⚠️ 설정 파일 번호 개수 오류 ({len(config_numbers)}개), 자동 생성으로 전환")
        
        # 설정 파일에 번호가 없거나 잘못된 경우 자동 생성
        if p_type == '자동':
            return []
        elif p_type == '반자동':
            numbers = sorted(random.sample(range(1, 46), 3))
            self.logger.info(f"🎲 반자동 번호 자동 생성: {numbers}")
            return numbers
        elif p_type == '수동(랜덤)':
            numbers = sorted(random.sample(range(1, 46), 6))
            self.logger.info(f"🎲 수동(랜덤) 번호 자동 생성: {numbers}")
            return numbers
        elif p_type == '수동(AI추천)':
            numbers = self.statistics.get_ai_recommended_numbers()
            self.logger.info(f"🤖 AI 추천 번호 생성: {numbers}")
            return numbers
        elif p_type == '수동(통계분석)':
            numbers = self.statistics.get_most_frequent_numbers(6)
            self.logger.info(f"📊 통계 분석 번호 생성: {numbers}")
            return numbers
        else:
            return []
        
        try:
            credentials = self.credential_manager.setup_credentials(force_new)
            if credentials:
                print("✅ 인증정보 설정 완료")
                return True
            else:
                print("❌ 인증정보 설정 실패")
                return False
        except Exception as e:
            print(f"❌ 인증정보 설정 중 오류: {e}")
            return False
        
        try:
            credentials = self.credential_manager.setup_credentials(force_new)
            if credentials:
                print("✅ 인증정보 설정 완료")
                return True
            else:
                print("❌ 인증정보 설정 실패")
                return False
        except Exception as e:
            print(f"❌ 인증정보 설정 중 오류: {e}")
            return False
    
    def test_credentials(self):
        """인증정보 테스트"""
        if not self.credential_manager:
            print("❌ CredentialManager가 사용할 수 없습니다.")
            return False
        
        return self.credential_manager.test_credentials_file()

class LottoStatistics:
    """로또 통계 분석 클래스 (기존 코드 유지)"""
    
    def __init__(self):
        self.winning_numbers_file = "winning_numbers.json"
        self.winning_numbers = self.load_winning_numbers()
        
    def load_winning_numbers(self):
        """저장된 당첨번호 불러오기"""
        try:
            with open(self.winning_numbers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.create_sample_winning_numbers()
            
    def create_sample_winning_numbers(self):
        """샘플 당첨번호 생성"""
        sample_data = []
        for i in range(50):
            numbers = sorted(random.sample(range(1, 46), 6))
            sample_data.append({
                'round': 1000 + i,
                'numbers': numbers,
                'date': f"2024-{(i%12)+1:02d}-{(i%28)+1:02d}"
            })
        
        with open(self.winning_numbers_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        
        return sample_data
            
    def get_most_frequent_numbers(self, count=6):
        """가장 자주 나온 번호들"""
        all_numbers = []
        for data in self.winning_numbers:
            all_numbers.extend(data['numbers'])
        
        counter = Counter(all_numbers)
        return [num for num, _ in counter.most_common(count)]
    
    def get_least_frequent_numbers(self, count=6):
        """가장 적게 나온 번호들"""
        all_numbers = []
        for data in self.winning_numbers:
            all_numbers.extend(data['numbers'])
        
        counter = Counter(all_numbers)
        return [num for num, _ in counter.most_common()[-count:]]
    
    def get_hot_numbers(self, recent_count=10):
        """최근 자주 나온 번호들"""
        recent_numbers = []
        for data in self.winning_numbers[-recent_count:]:
            recent_numbers.extend(data['numbers'])
        
        counter = Counter(recent_numbers)
        return [num for num, _ in counter.most_common(6)]

class IntegratedLottoBuyer:
    """통합 로또 자동구매 클래스"""
    
    def __init__(self):
        self.config_manager = ConfigurationManager()
        self.config = self.config_manager.load_configuration()
        self.statistics = LottoStatistics()
        self.auto_recharger = None
        self.notification_manager = None
        
        # NotificationManager 초기화
        if NotificationManager:
            try:
                self.notification_manager = NotificationManager(self.config)
                print("✅ Discord 알림 서비스 초기화 완료")
            except Exception as e:
                print(f"⚠️ Discord 알림 서비스 초기화 실패: {e}")
                self.notification_manager = None
        
        # AutoRecharger 초기화
        if AutoRecharger and self.config.get('payment', {}).get('auto_recharge'):
            try:
                self.auto_recharger = AutoRecharger(self.config)
                print("✅ 자동충전 기능 활성화")
            except Exception as e:
                print(f"⚠️ 자동충전 초기화 실패: {e}")
        
        self.setup_logging()
        self.driver = None
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('lotto_auto_buyer.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            options = Options()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("✅ Chrome 드라이버 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 드라이버 초기화 실패: {e}")
            return False
    
    def login(self):
        """로그인 (빠른 속도 최적화)"""
        try:
            credentials = self.config_manager.get_user_credentials()
            user_id = credentials.get('user_id')
            password = credentials.get('password')
            
            if not user_id or not password:
                self.logger.error("❌ 사용자 ID 또는 비밀번호가 설정되지 않았습니다")
                return False
            
            # 로그인 시작 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_login_start(user_id))
            
            self.logger.info("🔐 로그인 시작")
            self.driver.get("https://www.dhlottery.co.kr/user.do?method=login")
            time.sleep(1)  # 3초 → 1초
            
            # 로그인 입력 필드 찾기 (여러 방법 시도)
            id_input = None
            pw_input = None
            
            # 1. 기본 ID 선택자들 시도
            id_selectors = [
                (By.ID, "userId"),
                (By.NAME, "userId"),
                (By.CSS_SELECTOR, "input[name='userId']"),
                (By.CSS_SELECTOR, "input[id='userId']"),
                (By.XPATH, "//input[@placeholder='아이디' or @placeholder='ID' or contains(@class, 'user') or contains(@class, 'id')]"),
                (By.CSS_SELECTOR, "input[type='text']:first-of-type")
            ]
            
            for selector_type, selector in id_selectors:
                try:
                    id_input = WebDriverWait(self.driver, 3).until(  # 5초 → 3초
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    self.logger.info(f"✅ ID 입력 필드 발견: {selector_type.name}='{selector}'")
                    break
                except:
                    continue
            
            if not id_input:
                self.logger.error("❌ ID 입력 필드를 찾을 수 없습니다")
                return False
            
            # 2. 비밀번호 선택자들 시도
            pw_selectors = [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[name='password']"),
                (By.CSS_SELECTOR, "input[id='password']"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@placeholder='비밀번호' or @placeholder='password' or @placeholder='Password' or contains(@class, 'password') or contains(@class, 'pass')]"),
            ]
            
            for selector_type, selector in pw_selectors:
                try:
                    pw_input = WebDriverWait(self.driver, 3).until(  # 5초 → 3초
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    self.logger.info(f"✅ 비밀번호 입력 필드 발견: {selector_type.name}='{selector}'")
                    break
                except:
                    continue
            
            if not pw_input:
                self.logger.error("❌ 비밀번호 입력 필드를 찾을 수 없습니다")
                return False
            
            # 3. 로그인 정보 빠른 입력
            id_input.clear()
            id_input.send_keys(user_id)
            self.logger.info("✅ 사용자 ID 입력 완료")
            
            pw_input.clear()
            pw_input.send_keys(password)
            self.logger.info("✅ 비밀번호 입력 완료")
            
            # time.sleep(1) 제거
            
            # 4. 로그인 버튼 찾기 및 클릭
            login_selectors = [
                (By.CSS_SELECTOR, "input[type='submit'][value='로그인']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.XPATH, "//button[contains(text(), '로그인') or contains(text(), 'login') or contains(text(), 'Login')]"),
                (By.XPATH, "//input[@value='로그인' or @value='login' or @value='Login']"),
                (By.CSS_SELECTOR, ".btn_login, .login-btn, .login_btn")
            ]
            
            login_success = False
            for selector_type, selector in login_selectors:
                try:
                    login_btn = WebDriverWait(self.driver, 3).until(  # 5초 → 3초
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    login_btn.click()
                    self.logger.info(f"✅ 로그인 버튼 클릭: {selector_type.name}='{selector}'")
                    login_success = True
                    break
                except:
                    continue
            
            if not login_success:
                # Enter 키로 대체
                try:
                    pw_input.send_keys(Keys.ENTER)
                    self.logger.info("✅ Enter 키로 로그인 시도")
                    login_success = True
                except:
                    self.logger.error("❌ 로그인 버튼을 찾을 수 없습니다")
                    return False
            
            time.sleep(2)  # 5초 → 2초
            
            # 5. 로그인 성공 확인
            success_indicators = [
                "마이페이지",
                "로그아웃",
                "myPage",
                "logout",
                "로또구매",
                "main"
            ]
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            for indicator in success_indicators:
                if indicator in current_url or indicator in page_source:
                    self.logger.info("✅ 로그인 성공!")
                    
                    # 로그인 성공 알림
                    if self.notification_manager:
                        run_notification(self.notification_manager.notify_login_success(user_id))
                    
                    return True
            
            # 추가 확인: 오류 메시지 체크
            error_indicators = [
                "아이디나 비밀번호",
                "로그인 실패",
                "error",
                "잘못된"
            ]
            
            for error in error_indicators:
                if error in page_source:
                    self.logger.error(f"❌ 로그인 오류: {error} 감지")
                    
                    # 로그인 실패 알림
                    if self.notification_manager:
                        run_notification(self.notification_manager.notify_login_failure(user_id, error))
                    
                    return False
            
            self.logger.warning("⚠️ 로그인 상태를 확인할 수 없습니다")
            self.logger.info(f"현재 URL: {current_url}")
            return False
                
        except Exception as e:
            self.logger.error(f"❌ 로그인 오류: {e}")
            
            # 로그인 실패 알림 (예외)
            if self.notification_manager:
                credentials = self.config_manager.get_user_credentials()
                user_id = credentials.get('user_id', 'unknown')
                run_notification(self.notification_manager.notify_login_failure(user_id, str(e)))
            
            return False
    
    def check_balance(self):
        """잔액 확인 (개선된 버전)"""
        try:
            self.driver.get("https://www.dhlottery.co.kr/myPage.do?method=myPage")
            time.sleep(3)  # 2초 → 3초 (페이지 로딩 대기)
            
            # 다양한 예치금 선택자 시도 (우선순위 순서)
            balance_selectors = [
                # 1. "예치금" 텍스트와 가장 가까운 금액 찾기 (가장 정확)
                (By.XPATH, "//td[contains(text(), '예치금')]/following-sibling::td[contains(text(), '원')]"),
                (By.XPATH, "//th[contains(text(), '예치금')]/following-sibling::td[contains(text(), '원')]"),
                (By.XPATH, "//td[contains(text(), '예치금')]/following::td[contains(text(), '원')][1]"),
                (By.XPATH, "//span[contains(text(), '예치금')]/following::*[contains(text(), '원')][1]"),
                
                # 2. ta_right 클래스를 가진 td 중에서 첫 번째 (10,750원을 찾기 위해)
                (By.XPATH, "//td[@class='ta_right' and contains(text(), '원') and not(contains(text(), '0 원'))]"),
                
                # 3. strong 태그로 강조된 금액 (가장 확실한 예치금)
                (By.XPATH, "//strong[contains(text(), '원') and contains(text(), ',')]"),
                (By.CSS_SELECTOR, "strong.total_new"),
                (By.XPATH, "//strong[contains(text(), '원')]"),
                
                # 4. 금액 관련 클래스명으로 찾기
                (By.CSS_SELECTOR, ".deposit_amt, .balance_amt, .money_amt"),
                (By.CSS_SELECTOR, ".total_amt, .current_amt"),
                
                # 5. 마이페이지 특정 구조
                (By.XPATH, "//div[@class='my_box']//td[contains(text(), '원')]"),
                (By.XPATH, "//div[contains(@class, 'deposit')]//td[contains(text(), '원')]"),
                
                # 6. span 태그의 금액 (콤마 포함된 것 우선)
                (By.XPATH, "//span[contains(text(), '원') and contains(text(), ',')]"),
                (By.XPATH, "//span[contains(text(), '원') and string-length(translate(text(), '0123456789,', '')) < 3]"),
            ]
            
            for i, (selector_type, selector) in enumerate(balance_selectors):
                try:
                    elements = self.driver.find_elements(selector_type, selector)
                    self.logger.info(f"🔍 [{i+1}/{len(balance_selectors)}] {len(elements)}개 요소 발견: {selector_type if isinstance(selector_type, str) else selector_type.name}='{selector}'")
                    
                    for j, element in enumerate(elements):
                        text = element.text.strip()
                        self.logger.info(f"    ➤ 요소[{j+1}]: '{text}'")
                        
                        # 금액 추출 (숫자와 콤마만 남기기)
                        clean_text = ''.join(c for c in text if c.isdigit() or c == ',')
                        clean_text = clean_text.replace(',', '')
                        
                        self.logger.info(f"    ➤ 정리된 숫자: '{clean_text}'")
                        
                        # 유효한 숫자이고 3자리 이상이면 예치금으로 간주
                        if clean_text.isdigit() and len(clean_text) >= 3:
                            balance = int(clean_text)
                            
                            self.logger.info(f"    ➤ 변환된 금액: {balance:,}원")
                            
                            # 0원은 제외 (예치금이 0원일 리 없음)
                            if balance == 0:
                                self.logger.info(f"    ⚠️ 0원 제외")
                                continue
                            
                            # 너무 큰 금액은 제외 (1억 원 이상)
                            if balance > 100000000:
                                self.logger.info(f"    ⚠️ 너무 큰 금액 제외: {balance:,}원")
                                continue
                            
                            # 너무 작은 금액도 제외 (100원 미만)
                            if balance < 100:
                                self.logger.info(f"    ⚠️ 너무 작은 금액 제외: {balance:,}원")
                                continue
                                
                            self.logger.info(f"    ✅ 예치금 발견: {balance:,}원 (선택자 {i+1}번)")
                            
                            # 예치금 확인 알림
                            if self.notification_manager:
                                run_notification(self.notification_manager.notify_balance_check(balance))
                            
                            return balance  # 예치금을 찾으면 즉시 반환
                        else:
                            self.logger.info(f"    ❌ 유효하지 않은 금액: '{clean_text}' (3자리 미만 또는 숫자 아님)")
                        
                except Exception as e:
                    self.logger.info(f"    ⚠️ 선택자 [{i+1}] 시도 실패: {str(e)}")
                    continue
            
            # 모든 선택자 실패 시 디버깅 정보 수집
            self.logger.warning("⚠️ 예치금 정보를 찾을 수 없습니다. 디버깅 정보 수집 중...")
            
            # 디버깅: 페이지 정보 저장
            try:
                    current_url = self.driver.current_url
                    page_title = self.driver.title
                    
                    self.logger.info(f"현재 URL: {current_url}")
                    self.logger.info(f"페이지 제목: {page_title}")
                    
                    # 페이지 소스 일부 저장
                    page_source = self.driver.page_source
                    with open('debug_balance_page.html', 'w', encoding='utf-8') as f:
                        f.write(page_source)
                    self.logger.info("🛠️ 디버깅용 페이지 소스 저장: debug_balance_page.html")
                    
                    # 모든 원 포함 요소 찾기
                    all_won_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '원')]")
                    self.logger.info(f"🔍 '원' 포함 요소 {len(all_won_elements)}개 발견:")
                    
                    for i, elem in enumerate(all_won_elements[:10]):  # 처음 10개만 로깅
                        try:
                            text = elem.text.strip()
                            tag_name = elem.tag_name
                            class_name = elem.get_attribute('class') or 'no-class'
                            self.logger.info(f"  [{i+1}] <{tag_name} class='{class_name}'>{text}</{tag_name}>")
                        except Exception:
                            pass
                    
                except Exception as debug_error:
                    self.logger.error(f"디버깅 정보 수집 실패: {debug_error}")
                
                return 0
            
        except Exception as e:
            self.logger.error(f"❌ 잔액 확인 실패: {e}")
            return 0
    
    def generate_numbers(self, method="mixed"):
        """번호 생성"""
        settings = self.config_manager.get_purchase_settings()
        selection_method = settings.get('number_selection_method', method)
        
        if selection_method == "random":
            return sorted(random.sample(range(1, 46), 6))
        elif selection_method == "hot":
            hot_numbers = self.statistics.get_hot_numbers()
            return hot_numbers[:6]
        elif selection_method == "cold":
            cold_numbers = self.statistics.get_least_frequent_numbers()
            return cold_numbers[:6]
        else:  # mixed
            hot = self.statistics.get_hot_numbers()[:3]
            cold = self.statistics.get_least_frequent_numbers()[:2]
            random_num = random.sample([i for i in range(1, 46) if i not in hot + cold], 1)
            return sorted(hot + cold + random_num)
    
    def purchase_lotto(self):
        """로또 구매 - 기존 작동 로직 적용"""
        try:
            settings = self.config_manager.get_purchase_settings()
            games_count = settings.get('games_per_purchase', 5)
            
            self.logger.info(f"🎰 로또 구매 시작 - {games_count}게임")
            
            # 로또 구매 시작 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_purchase_start(games_count))
            
            # buy_lotto_games 메서드 호출 (실제 구매 로직)
            success_count = self.buy_lotto_games(games_count)
            
            if success_count > 0:
                self.logger.info(f"✅ 로또 구매 완료: {success_count}/{games_count}게임 성공")
                
                # 로또 구매 성공 알림
                if self.notification_manager:
                    run_notification(self.notification_manager.notify_purchase_success(success_count, success_count * 1000))
                
                # 구매 내역 저장
                self.save_purchase_history(success_count, games_count)
                
                return True
            else:
                self.logger.error("❌ 구매된 게임이 없습니다.")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ 로또 구매 실패: {e}")
            
            # 로또 구매 실패 알림
            if self.notification_manager:
                settings = self.config_manager.get_purchase_settings()
                games_count = settings.get('games_per_purchase', 5)
                run_notification(self.notification_manager.notify_purchase_failure(games_count, str(e)))
            
            return False
    
    def run(self, immediate=False):
        """메인 실행"""
        try:
            self.logger.info("🚀 통합 로또 자동구매 시스템 시작")
            
            # 프로그램 시작 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_program_start())
            
            # 드라이버 설정
            if not self.setup_driver():
                return False
            
            # 로그인
            if not self.login():
                return False
            
            # 잔액 확인
            balance = self.check_balance()
            
            # 자동충전 처리
            payment_settings = self.config_manager.get_payment_settings()
            min_balance = payment_settings.get('min_balance', 5000)
            
            self.logger.info(f"💰 현재 잔액: {balance:,}원, 최소 잔액: {min_balance:,}원")
            
            if balance < min_balance and self.auto_recharger:
                self.logger.info(f"💳 잔액이 {min_balance:,}원 이하입니다. 자동충전을 시도합니다.")
                if payment_settings.get('auto_recharge', False):
                    # 충전 시작 알림
                    recharge_amount = payment_settings.get('recharge_amount', 10000)
                    if self.notification_manager:
                        run_notification(self.notification_manager.notify_recharge_start(recharge_amount))
                    
                    if self.auto_recharger.auto_recharge(self.driver, balance):
                        self.logger.info("💳 자동충전 완료! 잔액 재확인 중...")
                        new_balance = self.check_balance()  # 충전 후 잔액 재확인
                        self.logger.info(f"💰 충전 후 잔액: {new_balance:,}원")
                        
                        # 충전 성공 알림
                        if self.notification_manager:
                            run_notification(self.notification_manager.notify_recharge_success(recharge_amount, new_balance))
                    else:
                        self.logger.error("❌ 자동충전 실패. 수동으로 충전 후 다시 실행해주세요.")
                        
                        # 충전 실패 알림
                        if self.notification_manager:
                            run_notification(self.notification_manager.notify_recharge_failure(recharge_amount, "자동충전 실패"))
                        
                        return False
                else:
                    self.logger.warning("⚠️ 자동충전이 비활성화되어 있습니다.")
                    self.logger.info("💳 설정 파일에서 'auto_recharge'를 true로 변경해주세요.")
                    if balance < 1000:  # 1게임도 구매할 수 없을 때
                        self.logger.error("❌ 잔액 부족으로 구매할 수 없습니다.")
                        return False
            elif balance < min_balance:
                self.logger.warning(f"⚠️ 자동충전 기능이 비활성화되어 있습니다 (잔액: {balance:,}원)")
            
            # 로또 구매
            if immediate or datetime.now().weekday() in [0, 3]:  # 월, 목요일 또는 즉시 실행
                self.purchase_lotto()
            
            self.logger.info("✅ 시스템 실행 완료")
            
            # 프로그램 완료 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_program_complete())
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 시스템 실행 실패: {e}")
            
            # 시스템 실행 실패 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_critical("시스템 실행 실패", f"예상치 못한 오류가 발생했습니다: {str(e)}"))
            
            return False
        finally:
            if self.driver:
                self.driver.quit()
            
            # 알림 매니저 정리
            if self.notification_manager:
                try:
                    run_notification(self.notification_manager.cleanup())
                except Exception as cleanup_error:
                    print(f"⚠️ 알림 매니저 정리 실패: {cleanup_error}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='통합 로또 자동구매 시스템')
    parser.add_argument('--now', action='store_true', help='즉시 구매 실행')
    parser.add_argument('--config', action='store_true', help='설정 확인')
    parser.add_argument('--credentials', action='store_true', help='인증정보 설정/업데이트')
    parser.add_argument('--test-credentials', action='store_true', help='인증정보 테스트')
    parser.add_argument('--master-password', help='마스터 패스워드 (자동화용)')
    parser.add_argument('--headless', action='store_true', help='헤드리스 모드 강제 활성화')
    
    args = parser.parse_args()
    
    # 마스터 패스워드 설정 (환경변수 > CLI 옵션 > 수동입력)
    if args.master_password:
        os.environ['LOTTO_MASTER_PASSWORD'] = args.master_password
        print("✅ CLI 옵션에서 마스터 패스워드 설정")
    elif os.getenv('LOTTO_MASTER_PASSWORD'):
        print("✅ 환경변수에서 마스터 패스워드 확인")
    elif not args.credentials and not args.test_credentials and not args.config:
        # 자동화 모드에서 마스터 패스워드가 없으면 안내
        print("⚠️ 자동화 모드에서는 마스터 패스워드가 필요합니다.")
        print("💡 사용 방법:")
        print("   1. 환경변수: export LOTTO_MASTER_PASSWORD='your_password'")
        print("   2. CLI 옵션: --master-password 'your_password'")
        print("   3. Docker secrets: /run/secrets/master_password 파일")
    
    # ConfigurationManager 초기화
    config_mgr = ConfigurationManager()
    config = config_mgr.load_configuration()
    
    # 헤드리스 모드 오버라이드
    if args.headless:
        if 'options' not in config:
            config['options'] = {}
        config['options']['headless'] = True
        print("✅ 헤드리스 모드 활성화")
    
    if args.config:
        # 설정 확인
        print("📋 현재 설정:")
        # 마스터 패스워드는 보안상 숨김
        safe_config = json.loads(json.dumps(config))
        if 'LOTTO_MASTER_PASSWORD' in os.environ:
            safe_config['_master_password_source'] = '환경변수'
        print(json.dumps(safe_config, indent=2, ensure_ascii=False))
        return
    
    if args.credentials:
        # 인증정보 설정
        print("🔐 인증정보 설정 모드")
        success = config_mgr.setup_credentials(force_new=True)
        if success:
            print("✅ 인증정보 설정이 완료되었습니다.")
        else:
            print("❌ 인증정보 설정에 실패했습니다.")
            sys.exit(1)
        return
    
    if args.test_credentials:
        # 인증정보 테스트
        print("🧪 인증정보 테스트 모드")
        success = config_mgr.test_credentials()
        if success:
            print("✅ 인증정보 테스트 통과")
        else:
            print("❌ 인증정보 테스트 실패")
            sys.exit(1)
        return
    
    # 인증정보 확인
    print("🔍 인증정보 확인 중...")
    credentials = config_mgr.get_user_credentials()
    
    if not credentials.get('user_id') or not credentials.get('password'):
        print("❌ 인증정보가 설정되지 않았습니다.")
        print("💡 다음 명령어로 인증정보를 설정하세요:")
        print(f"    python {os.path.basename(__file__)} --credentials")
        sys.exit(1)
    
    # 로또 구매 실행
    buyer = IntegratedLottoBuyer()
    success = buyer.run(immediate=args.now)
    
    if success:
        print("✅ 시스템 실행 성공")
    else:
        print("❌ 시스템 실행 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()
