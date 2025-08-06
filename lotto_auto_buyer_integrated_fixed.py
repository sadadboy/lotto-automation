#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 로또 자동구매 시스템 - 수정 버전
기존 lotto_auto_buyer.py의 작동하는 구매 로직을 포함
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

# 현재 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

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

class LottoStatistics:
    """로또 통계 분석 클래스"""
    
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
        if not self.winning_numbers:
            return random.sample(range(1, 46), 6)
            
        all_numbers = []
        for draw in self.winning_numbers:
            if 'numbers' in draw:
                all_numbers.extend(draw['numbers'])
                
        counter = Counter(all_numbers)
        most_common = counter.most_common(count)
        return [num for num, freq in most_common]
        
    def get_ai_recommended_numbers(self):
        """AI 추천 번호"""
        if not self.winning_numbers:
            return random.sample(range(1, 46), 6)
            
        recent_numbers = []
        recent_draws = self.winning_numbers[-10:] if len(self.winning_numbers) >= 10 else self.winning_numbers
        
        for i, draw in enumerate(recent_draws):
            if 'numbers' in draw:
                weight = (i + 1) * 0.1
                recent_numbers.extend(draw['numbers'] * int(weight * 10))
                
        counter = Counter(recent_numbers)
        numbers = list(range(1, 46))
        weights = []
        
        for num in numbers:
            freq = counter.get(num, 0)
            if freq == 0:
                weight = 0.5
            elif freq <= 3:
                weight = 1.5
            elif freq <= 6:
                weight = 1.0
            else:
                weight = 0.3
            weights.append(weight)
            
        selected = np.random.choice(numbers, size=6, replace=False, p=np.array(weights)/sum(weights))
        return sorted(selected.tolist())
    
    def get_random_numbers(self):
        """완전 랜덤 번호"""
        return sorted(random.sample(range(1, 46), 6))
    
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
        self.config = self.load_config()
        self.statistics = LottoStatistics()
        self.auto_recharger = None
        self.notification_manager = None
        self.screenshot_dir = "screenshots"
        
        # 디렉토리 생성
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
        
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
    
    def load_config(self):
        """설정 파일 로드"""
        # 인증정보 로드
        credentials = self.get_user_credentials()
        
        try:
            with open('lotto_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 기존 구조와 호환성 유지
                if 'login' not in config:
                    config['login'] = {
                        'user_id': credentials.get('user_id', ''),
                        'password': credentials.get('password', '')
                    }
                return config
        except Exception as e:
            print(f"⚠️ JSON 설정 로드 실패: {e}")
            return self._create_default_config()
    
    def get_user_credentials(self):
        """사용자 인증정보 반환"""
        # 1. 암호화된 인증정보 시도
        if CredentialManager:
            try:
                credential_manager = CredentialManager("credentials.enc")
                if credential_manager.has_credentials():
                    credentials = credential_manager.load_credentials()
                    if credentials:
                        print("✅ 암호화된 인증정보 로드 성공")
                        return {
                            'user_id': credentials.user_id,
                            'password': credentials.password,
                            'recharge_password': credentials.recharge_password
                        }
            except Exception as e:
                print(f"⚠️ 인증정보 로드 오류: {e}")
        
        # 2. 환경변수에서 시도
        if os.getenv('LOTTO_USER_ID') and os.getenv('LOTTO_PASSWORD'):
            print("✅ 환경변수에서 인증정보 로드")
            return {
                'user_id': os.getenv('LOTTO_USER_ID'),
                'password': os.getenv('LOTTO_PASSWORD'),
                'recharge_password': os.getenv('LOTTO_RECHARGE_PASSWORD', '')
            }
        
        # 3. 기본값 반환
        print("❌ 인증정보가 없음 - 기본값 사용")
        return {'user_id': '', 'password': '', 'recharge_password': ''}
    
    def _create_default_config(self):
        """기본 설정 생성"""
        return {
            "login": {
                "user_id": "",
                "password": ""
            },
            "purchase": {
                "count": 5,
                "lotto_list": [
                    {"type": "자동", "numbers": []},
                    {"type": "반자동", "numbers": []},
                    {"type": "수동(랜덤)", "numbers": []},
                    {"type": "수동(AI추천)", "numbers": []},
                    {"type": "수동(통계분석)", "numbers": []}
                ]
            },
            "payment": {
                "auto_recharge": False,
                "recharge_amount": 50000,
                "min_balance": 5000,
                "recharge_method": "account_transfer"
            },
            "options": {
                "save_screenshot": True,
                "headless": False
            }
        }
    
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
            
            # 헤드리스 모드 설정
            if self.config.get('options', {}).get('headless', False) or os.environ.get('DOCKER_ENV'):
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("✅ Chrome 드라이버 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 드라이버 초기화 실패: {e}")
            return False
    
    def login(self):
        """로그인"""
        try:
            user_id = self.config['login']['user_id']
            password = self.config['login']['password']
            
            if not user_id or not password:
                self.logger.error("❌ 사용자 ID 또는 비밀번호가 설정되지 않았습니다")
                return False
            
            # 로그인 시작 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_login_start(user_id))
            
            self.logger.info("🔐 로그인 시작")
            self.driver.get("https://www.dhlottery.co.kr/user.do?method=login")
            time.sleep(1)
            
            # ID 입력
            id_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "userId"))
            )
            id_input.clear()
            id_input.send_keys(user_id)
            
            # 비밀번호 입력
            pw_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            pw_input.clear()
            pw_input.send_keys(password)
            
            # 로그인 버튼 클릭
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='로그인']"))
            )
            login_btn.click()
            
            time.sleep(2)
            
            # 로그인 성공 확인
            if "마이페이지" in self.driver.page_source or "로그아웃" in self.driver.page_source:
                self.logger.info("✅ 로그인 성공!")
                
                if self.notification_manager:
                    run_notification(self.notification_manager.notify_login_success(user_id))
                
                return True
            else:
                self.logger.error("❌ 로그인 실패")
                
                if self.notification_manager:
                    run_notification(self.notification_manager.notify_login_failure(user_id, "로그인 실패"))
                
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 로그인 오류: {e}")
            return False
    
    def check_balance(self):
        """잔액 확인"""
        try:
            self.driver.get("https://www.dhlottery.co.kr/myPage.do?method=myPage")
            time.sleep(3)
            
            # 예치금 찾기 (여러 방법 시도)
            balance_selectors = [
                (By.XPATH, "//td[contains(text(), '예치금')]/following-sibling::td[contains(text(), '원')]"),
                (By.XPATH, "//strong[contains(text(), '원') and contains(text(), ',')]"),
                (By.XPATH, "//td[@class='ta_right' and contains(text(), '원') and not(contains(text(), '0 원'))]"),
            ]
            
            for i, (selector_type, selector) in enumerate(balance_selectors):
                try:
                    elements = self.driver.find_elements(selector_type, selector)
                    for element in elements:
                        text = element.text.strip()
                        clean_text = ''.join(c for c in text if c.isdigit() or c == ',')
                        clean_text = clean_text.replace(',', '')
                        
                        if clean_text.isdigit() and len(clean_text) >= 3:
                            balance = int(clean_text)
                            if 0 < balance <= 1000000:
                                self.logger.info(f"✅ 예치금 발견: {balance:,}원")
                                
                                if self.notification_manager:
                                    run_notification(self.notification_manager.notify_balance_check(balance))
                                
                                return balance
                except Exception:
                    continue
            
            self.logger.warning("⚠️ 예치금을 찾을 수 없습니다")
            return 0
            
        except Exception as e:
            self.logger.error(f"❌ 잔액 확인 실패: {e}")
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
            numbers = self.statistics.get_random_numbers()
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

    def setup_purchase_page(self, purchase_count=1):
        """구매 페이지 초기 설정"""
        try:
            self.logger.info("🎯 로또 구매 페이지 설정...")
            self.driver.get("https://ol.dhlottery.co.kr/olotto/game/game645.do")
            time.sleep(3)
            
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "amoundApply"))
            )
            
            try:
                self.driver.execute_script("selectWayTab(0);")
                time.sleep(1)
                self.logger.info("✅ 혼합선택 탭 활성화")
            except Exception as e:
                self.logger.warning(f"혼합선택 탭 활성화 실패: {e}")
            
            try:
                amount_select = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "amoundApply"))
                )
                select_obj = Select(amount_select)
                select_obj.select_by_value(str(purchase_count))
                self.logger.info(f"✅ 적용수량 {purchase_count}로 설정")
                time.sleep(1)
                return True
                    
            except Exception as e:
                self.logger.error(f"적용수량 설정 실패: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"구매 페이지 설정 실패: {e}")
            return False

    def click_number_enhanced(self, number):
        """강화된 번호 클릭 방법"""
        try:
            self.logger.info(f"🎯 번호 {number} 클릭 시도...")
            
            # 방법 1: 체크박스 직접 클릭
            try:
                checkbox = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, f"check645num{number}"))
                )
                
                if checkbox.is_displayed() and checkbox.is_enabled():
                    if not checkbox.is_selected():
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        self.logger.info(f"  ✅ 체크박스 직접 클릭 성공 ({number})")
                        time.sleep(0.3)
                        return True
                    else:
                        self.logger.info(f"  ℹ️ 번호 {number} 이미 선택됨")
                        return True
                        
            except Exception as e:
                self.logger.debug(f"  체크박스 직접 클릭 실패: {e}")
            
            # 방법 2: 라벨 클릭
            try:
                label = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"label[for='check645num{number}']"))
                )
                self.driver.execute_script("arguments[0].click();", label)
                self.logger.info(f"  ✅ 라벨 클릭 성공 ({number})")
                time.sleep(0.3)
                return True
                
            except Exception as e:
                self.logger.debug(f"  라벨 클릭 실패: {e}")
            
            self.logger.warning(f"  ❌ 번호 {number} 클릭 모든 방법 실패")
            return False
            
        except Exception as e:
            self.logger.error(f"번호 {number} 클릭 중 오류: {e}")
            return False

    def select_auto_numbers(self):
        """자동 번호 선택"""
        try:
            # 자동선택 체크박스 클릭
            auto_checkbox = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "checkAutoSelect"))
            )
            
            if not auto_checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", auto_checkbox)
                self.logger.info("자동선택 체크박스 클릭")
            
            time.sleep(1)
            
            # 확인 버튼 클릭
            confirm_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnSelectNum"))
            )
            self.driver.execute_script("arguments[0].click();", confirm_btn)
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"자동 번호 선택 실패: {e}")
            return False

    def select_semi_auto_numbers(self, numbers):
        """반자동 번호 선택"""
        try:
            self.logger.info(f"반자동 번호 선택: {numbers}")
            
            # 번호 클릭
            for num in numbers:
                self.click_number_enhanced(num)
                time.sleep(0.5)
            
            # 자동선택 체크박스 클릭
            auto_checkbox = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "checkAutoSelect"))
            )
            if not auto_checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", auto_checkbox)
                self.logger.info("반자동용 자동선택 체크박스 클릭")
            
            time.sleep(1)
            
            # 확인 버튼 클릭
            confirm_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnSelectNum"))
            )
            self.driver.execute_script("arguments[0].click();", confirm_btn)
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"반자동 번호 선택 실패: {e}")
            return False

    def select_manual_numbers(self, numbers):
        """수동 번호 선택"""
        try:
            self.logger.info(f"수동 번호 선택: {numbers}")
            
            # 번호 클릭
            for num in numbers:
                self.click_number_enhanced(num)
                time.sleep(0.5)
            
            time.sleep(1)
            
            # 확인 버튼 클릭
            confirm_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnSelectNum"))
            )
            self.driver.execute_script("arguments[0].click();", confirm_btn)
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"수동 번호 선택 실패: {e}")
            return False

    def complete_purchase(self):
        """구매 완료 처리"""
        try:
            # 구매하기 버튼 클릭
            buy_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnBuy"))
            )
            self.driver.execute_script("arguments[0].click();", buy_btn)
            self.logger.info("구매하기 버튼 클릭")
            time.sleep(3)
            
            # 구매 확인 처리
            try:
                self.driver.execute_script("closepopupLayerConfirm(true);")
                self.logger.info("✅ JavaScript 함수 직접 호출 성공")
                confirmation_found = True
            except Exception:
                confirmation_found = False
            
            if not confirmation_found:
                # 확인 버튼 찾기
                confirm_selectors = [
                    "//input[@value='확인' and contains(@onclick, 'closepopupLayerConfirm(true)')]",
                    "//input[@value='확인']",
                    "//button[contains(text(), '확인')]"
                ]
                
                for selector in confirm_selectors:
                    try:
                        confirm_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        self.driver.execute_script("arguments[0].click();", confirm_btn)
                        self.logger.info("✅ 구매 확인 버튼 클릭")
                        confirmation_found = True
                        break
                    except:
                        continue
            
            time.sleep(3)
            return confirmation_found
            
        except Exception as e:
            self.logger.error(f"구매 완료 처리 실패: {e}")
            return False

    def take_screenshot(self, filename_prefix="purchase"):
        """스크린샷 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            self.driver.save_screenshot(filepath)
            self.logger.info(f"📸 스크린샷 저장: {filename}")
            return filepath
        except Exception as e:
            self.logger.error(f"스크린샷 저장 실패: {e}")
            return None

    def save_purchase_history(self, success_count, purchase_count):
        """구매 내역 저장"""
        try:
            history_file = "purchase_history.json"
            
            # 기존 내역 불러오기
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except FileNotFoundError:
                history = []
            
            # 새로운 구매 내역 추가
            new_record = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success_count': success_count,
                'total_count': purchase_count,
                'amount': success_count * 1000
            }
            
            history.append(new_record)
            
            # 저장
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            self.logger.info("📝 구매 내역 저장 완료")
            
        except Exception as e:
            self.logger.error(f"구매 내역 저장 실패: {e}")

    def buy_lotto_games(self, purchase_count):
        """로또 구매 실행 - 핵심 구매 로직"""
        try:
            self.logger.info(f"🎯 로또 구매 시작 ({purchase_count}게임)...")
            
            # 설정 파일에서 lotto_list 가져오기
            lotto_list = self.config['purchase']['lotto_list']
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
                    
                    self.logger.info("")
                    self.logger.info(f"🎮 [{i+1}/{purchase_count}] {p_type} 구매 시작...")
                    self.logger.info(f"📋 사용할 번호: {numbers}")
                    
                    if not self.setup_purchase_page(1):
                        continue
                    
                    # 구매 방식에 따른 처리
                    if p_type == '자동':
                        if self.select_auto_numbers():
                            self.logger.info("    ✅ 자동 번호 선택 완료")
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
                        if self.config['options'].get('save_screenshot', True):
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

    def purchase_lotto(self):
        """로또 구매 - 실제 구매 실행"""
        try:
            purchase_count = self.config['purchase']['count']
            
            self.logger.info(f"🎰 로또 구매 시작 - {purchase_count}게임")
            
            # 로또 구매 시작 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_purchase_start(purchase_count))
            
            # 실제 구매 실행
            success_count = self.buy_lotto_games(purchase_count)
            
            if success_count > 0:
                self.logger.info(f"✅ 로또 구매 완료: {success_count}/{purchase_count}게임 성공")
                
                # 로또 구매 성공 알림
                if self.notification_manager:
                    run_notification(self.notification_manager.notify_purchase_success(success_count, success_count * 1000))
                
                # 구매 내역 저장
                self.save_purchase_history(success_count, purchase_count)
                
                return True
            else:
                self.logger.error("❌ 구매된 게임이 없습니다.")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ 로또 구매 실패: {e}")
            
            # 로또 구매 실패 알림
            if self.notification_manager:
                purchase_count = self.config['purchase']['count']
                run_notification(self.notification_manager.notify_purchase_failure(purchase_count, str(e)))
            
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
            min_balance = self.config['payment'].get('min_balance', 5000)
            
            self.logger.info(f"💰 현재 잔액: {balance:,}원, 최소 잔액: {min_balance:,}원")
            
            if balance < min_balance and self.auto_recharger:
                self.logger.info(f"💳 잔액이 {min_balance:,}원 이하입니다. 자동충전을 시도합니다.")
                if self.config['payment'].get('auto_recharge', False):
                    recharge_amount = self.config['payment'].get('recharge_amount', 10000)
                    if self.notification_manager:
                        run_notification(self.notification_manager.notify_recharge_start(recharge_amount))
                    
                    if self.auto_recharger.auto_recharge(self.driver, balance):
                        self.logger.info("💳 자동충전 완료! 잔액 재확인 중...")
                        new_balance = self.check_balance()
                        self.logger.info(f"💰 충전 후 잔액: {new_balance:,}원")
                        
                        if self.notification_manager:
                            run_notification(self.notification_manager.notify_recharge_success(recharge_amount, new_balance))
                    else:
                        self.logger.error("❌ 자동충전 실패.")
                        if self.notification_manager:
                            run_notification(self.notification_manager.notify_recharge_failure(recharge_amount, "자동충전 실패"))
                        return False
                else:
                    self.logger.warning("⚠️ 자동충전이 비활성화되어 있습니다.")
                    if balance < 1000:
                        self.logger.error("❌ 잔액 부족으로 구매할 수 없습니다.")
                        return False
            
            # 로또 구매
            if immediate or datetime.now().weekday() in [0, 3]:  # 월, 목요일 또는 즉시 실행
                success = self.purchase_lotto()
                if not success:
                    return False
            
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

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='통합 로또 자동구매 시스템')
    parser.add_argument('--now', action='store_true', help='즉시 구매 실행')
    parser.add_argument('--config', action='store_true', help='설정 확인')
    parser.add_argument('--headless', action='store_true', help='헤드리스 모드 강제 활성화')
    
    args = parser.parse_args()
    
    if args.config:
        # 설정 확인
        buyer = IntegratedLottoBuyer()
        print("📋 현재 설정:")
        safe_config = json.loads(json.dumps(buyer.config))
        # 패스워드 숨김
        if 'login' in safe_config:
            safe_config['login']['password'] = '***'
        print(json.dumps(safe_config, indent=2, ensure_ascii=False))
        return
    
    # 헤드리스 모드 환경변수 설정
    if args.headless:
        os.environ['DOCKER_ENV'] = 'true'
        print("✅ 헤드리스 모드 활성화")
    
    # 로또 구매 실행
    buyer = IntegratedLottoBuyer()
    
    # 인증정보 확인
    if not buyer.config['login']['user_id'] or not buyer.config['login']['password']:
        print("❌ 인증정보가 설정되지 않았습니다.")
        print("💡 다음과 같이 환경변수를 설정하거나 암호화된 인증정보를 생성하세요:")
        print("   export LOTTO_USER_ID='your_id'")
        print("   export LOTTO_PASSWORD='your_password'")
        return
    
    success = buyer.run(immediate=args.now)
    
    if success:
        print("✅ 시스템 실행 성공")
    else:
        print("❌ 시스템 실행 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()
