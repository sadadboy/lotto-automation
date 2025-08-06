#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAB + ENTER 방식 적용 완전 자동화 로또 구매 시스템
검증된 로그인 방식으로 안정적인 자동화 구현
"""

import sys
import os
import json
import time
import logging
import random
import argparse
import signal
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

# 모듈 import (fallback 포함)
def safe_import(module_name, fallback_message):
    """안전한 모듈 import"""
    try:
        if module_name == 'auto_recharge':
            from auto_recharge import AutoRecharger
            return AutoRecharger
        elif module_name == 'credential_manager':
            from credential_manager import CredentialManager
            return CredentialManager
        elif module_name == 'discord_notifier':
            from discord_notifier import NotificationManager, run_notification
            return (NotificationManager, run_notification)
    except ImportError as e:
        print(f"⚠️ {module_name} 로드 실패: {e}")
        print(f"📝 {fallback_message}")
        return None

# 모듈 로드
AutoRecharger = safe_import('auto_recharge', "자동충전 기능이 비활성화됩니다.")
CredentialManager = safe_import('credential_manager', "인증정보 암호화 기능이 비활성화됩니다.")

notification_result = safe_import('discord_notifier', "알림 기능이 비활성화됩니다.")
if notification_result:
    NotificationManager, run_notification = notification_result
else:
    NotificationManager, run_notification = None, None

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
        
        try:
            with open(self.winning_numbers_file, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 샘플 데이터 저장 실패: {e}")
        
        return sample_data
            
    def get_most_frequent_numbers(self, count=6):
        """가장 자주 나온 번호들"""
        if not self.winning_numbers:
            return sorted(random.sample(range(1, 46), count))
            
        all_numbers = []
        for draw in self.winning_numbers:
            if 'numbers' in draw:
                all_numbers.extend(draw['numbers'])
                
        if not all_numbers:
            return sorted(random.sample(range(1, 46), count))
                
        counter = Counter(all_numbers)
        most_common = counter.most_common(count)
        return [num for num, freq in most_common]
        
    def get_ai_recommended_numbers(self):
        """AI 추천 번호 - numpy 의존성 제거"""
        if not self.winning_numbers:
            return sorted(random.sample(range(1, 46), 6))
            
        # 최근 10회 추첨 분석
        recent_draws = self.winning_numbers[-10:] if len(self.winning_numbers) >= 10 else self.winning_numbers
        recent_numbers = []
        
        for i, draw in enumerate(recent_draws):
            if 'numbers' in draw:
                weight = (i + 1)  # 최근일수록 가중치 높음
                recent_numbers.extend(draw['numbers'] * weight)
                
        if not recent_numbers:
            return sorted(random.sample(range(1, 46), 6))
                
        # 빈도 기반 가중치 계산
        counter = Counter(recent_numbers)
        numbers = list(range(1, 46))
        weighted_numbers = []
        
        for num in numbers:
            freq = counter.get(num, 0)
            if freq == 0:
                weight = 1  # 나오지 않은 번호는 기본 가중치
            elif freq <= 3:
                weight = 3  # 적게 나온 번호는 높은 가중치
            elif freq <= 6:
                weight = 2  # 보통 나온 번호는 중간 가중치
            else:
                weight = 1  # 많이 나온 번호는 낮은 가중치
            
            weighted_numbers.extend([num] * weight)
        
        # 가중치 기반 랜덤 선택
        selected = set()
        while len(selected) < 6 and weighted_numbers:
            selected.add(random.choice(weighted_numbers))
        
        # 부족한 경우 일반 랜덤으로 채우기
        while len(selected) < 6:
            selected.add(random.randint(1, 45))
            
        return sorted(list(selected)[:6])
    
    def get_random_numbers(self):
        """완전 랜덤 번호"""
        return sorted(random.sample(range(1, 46), 6))
    
    def get_least_frequent_numbers(self, count=6):
        """가장 적게 나온 번호들"""
        if not self.winning_numbers:
            return sorted(random.sample(range(1, 46), count))
            
        all_numbers = []
        for data in self.winning_numbers:
            if 'numbers' in data:
                all_numbers.extend(data['numbers'])
        
        if not all_numbers:
            return sorted(random.sample(range(1, 46), count))
            
        counter = Counter(all_numbers)
        least_common = counter.most_common()[-count:] if len(counter.most_common()) >= count else counter.most_common()
        return [num for num, _ in least_common]
    
    def get_hot_numbers(self, recent_count=10):
        """최근 자주 나온 번호들"""
        if not self.winning_numbers:
            return sorted(random.sample(range(1, 46), 6))
            
        recent_numbers = []
        for data in self.winning_numbers[-recent_count:]:
            if 'numbers' in data:
                recent_numbers.extend(data['numbers'])
        
        if not recent_numbers:
            return sorted(random.sample(range(1, 46), 6))
            
        counter = Counter(recent_numbers)
        hot = counter.most_common(6)
        return [num for num, _ in hot]

class TabEnterLottoBuyer:
    """TAB + ENTER 방식 완전 자동화 로또 구매 클래스"""
    
    def __init__(self):
        """초기화 - 모든 설정을 환경변수나 파일에서 로드"""
        self.config = self.load_config()
        self.statistics = LottoStatistics()
        self.auto_recharger = None
        self.notification_manager = None
        self.screenshot_dir = "screenshots"
        self.driver = None
        
        # 신호 핸들러 설정 (도커에서 안전한 종료를 위해)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # 디렉토리 생성
        self._create_directories()
        
        # 로깅 설정
        self.setup_logging()
        
        # 외부 모듈 초기화
        self._init_external_modules()
    
    def _signal_handler(self, signum, frame):
        """신호 핸들러 - 안전한 종료"""
        self.logger.info(f"📡 신호 수신: {signum}, 안전하게 종료합니다...")
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        sys.exit(0)
    
    def _create_directories(self):
        """필요한 디렉토리 생성"""
        directories = [self.screenshot_dir, "logs"]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def load_config(self):
        """설정 로드 - 환경변수 우선, 파일 fallback"""
        config = self._get_default_config()
        
        # 1. JSON 파일에서 기본 설정 로드
        try:
            with open('lotto_config.json', 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"⚠️ 설정 파일 로드 실패: {e}, 기본 설정 사용")
        
        # 2. 환경변수로 오버라이드 (도커 환경 대응)
        config = self._apply_env_overrides(config)
        
        # 3. 인증정보 처리
        config['login'] = self._get_credentials()
        
        return config
    
    def _get_default_config(self):
        """기본 설정 반환"""
        return {
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
                "auto_recharge": True,
                "recharge_amount": 10000,
                "min_balance": 5000,
                "recharge_method": "account_transfer"
            },
            "options": {
                "save_screenshot": True,
                "headless": True,  # 도커 환경 기본값
                "wait_time": 2,
                "retry_count": 3
            }
        }
    
    def _apply_env_overrides(self, config):
        """환경변수 기반 설정 오버라이드"""
        # 구매 설정
        if os.getenv('LOTTO_PURCHASE_COUNT'):
            try:
                config['purchase']['count'] = int(os.getenv('LOTTO_PURCHASE_COUNT'))
            except ValueError:
                pass
        
        # 결제 설정
        if os.getenv('LOTTO_AUTO_RECHARGE'):
            config['payment']['auto_recharge'] = os.getenv('LOTTO_AUTO_RECHARGE').lower() == 'true'
        
        if os.getenv('LOTTO_RECHARGE_AMOUNT'):
            try:
                config['payment']['recharge_amount'] = int(os.getenv('LOTTO_RECHARGE_AMOUNT'))
            except ValueError:
                pass
        
        if os.getenv('LOTTO_MIN_BALANCE'):
            try:
                config['payment']['min_balance'] = int(os.getenv('LOTTO_MIN_BALANCE'))
            except ValueError:
                pass
        
        # 옵션 설정
        if os.getenv('LOTTO_HEADLESS'):
            config['options']['headless'] = os.getenv('LOTTO_HEADLESS').lower() == 'true'
        
        if os.getenv('LOTTO_SCREENSHOT'):
            config['options']['save_screenshot'] = os.getenv('LOTTO_SCREENSHOT').lower() == 'true'
        
        # 도커 환경 감지
        if os.getenv('DOCKER_ENV') or os.path.exists('/.dockerenv'):
            config['options']['headless'] = True
            config['options']['save_screenshot'] = True
            print("🐳 도커 환경 감지: 헤드리스 모드 활성화")
        
        return config
    
    def _get_credentials(self):
        """인증정보 로드 - 완전 자동화"""
        # 1. 환경변수에서 시도 (도커에서 주로 사용)
        if os.getenv('LOTTO_USER_ID') and os.getenv('LOTTO_PASSWORD'):
            return {
                'user_id': os.getenv('LOTTO_USER_ID'),
                'password': os.getenv('LOTTO_PASSWORD')
            }
        
        # 2. 도커 시크릿에서 시도
        try:
            with open('/run/secrets/lotto_user_id', 'r') as f:
                user_id = f.read().strip()
            with open('/run/secrets/lotto_password', 'r') as f:
                password = f.read().strip()
            if user_id and password:
                print("🔐 도커 시크릿에서 인증정보 로드")
                return {'user_id': user_id, 'password': password}
        except:
            pass
        
        # 3. .env 파일에서 시도
        if os.path.exists('.env'):
            env_vars = {}
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
            
            if env_vars.get('LOTTO_USER_ID') and env_vars.get('LOTTO_PASSWORD'):
                print("🔐 .env 파일에서 인증정보 로드")
                return {
                    'user_id': env_vars['LOTTO_USER_ID'],
                    'password': env_vars['LOTTO_PASSWORD']
                }
        
        # 4. 암호화된 파일에서 시도
        if CredentialManager:
            try:
                credential_manager = CredentialManager("credentials.enc")
                if credential_manager.has_credentials():
                    credentials = credential_manager.load_credentials()
                    if credentials:
                        print("🔐 암호화된 파일에서 인증정보 로드")
                        return {
                            'user_id': credentials.user_id,
                            'password': credentials.password
                        }
            except Exception as e:
                print(f"⚠️ 암호화 파일 로드 실패: {e}")
        
        # 5. 모든 방법 실패 시 에러
        raise Exception("❌ 인증정보를 찾을 수 없습니다. 환경변수나 도커 시크릿을 설정하세요.")
    
    def _init_external_modules(self):
        """외부 모듈 초기화"""
        # NotificationManager 초기화
        if NotificationManager:
            try:
                self.notification_manager = NotificationManager(self.config)
                print("✅ 알림 서비스 초기화 완료")
            except Exception as e:
                print(f"⚠️ 알림 서비스 초기화 실패: {e}")
                self.notification_manager = None
        
        # AutoRecharger 초기화
        if AutoRecharger and self.config['payment'].get('auto_recharge'):
            try:
                self.auto_recharger = AutoRecharger(self.config)
                print("✅ 자동충전 기능 활성화")
            except Exception as e:
                print(f"⚠️ 자동충전 초기화 실패: {e}")
    
    def setup_logging(self):
        """로깅 설정"""
        log_level = logging.DEBUG if os.getenv('LOTTO_DEBUG') == 'true' else logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/lotto_auto_buyer.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 도커 환경에서는 stdout으로만 출력
        if os.getenv('DOCKER_ENV'):
            logging.getLogger().handlers = [logging.StreamHandler()]
    
    def setup_driver(self):
        """Chrome 드라이버 설정 - 도커 최적화"""
        try:
            options = Options()
            
            # 기본 옵션
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 도커/헤드리스 환경 옵션
            if self.config['options']['headless']:
                options.add_argument('--headless=new')  # 새로운 헤드리스 모드
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-plugins')
                options.add_argument('--disable-images')  # 이미지 로딩 비활성화로 속도 향상
                options.add_argument('--window-size=1920,1080')
                
                # 메모리 사용량 최적화
                options.add_argument('--memory-pressure-off')
                options.add_argument('--max_old_space_size=4096')
            
            # 도커에서 Selenium Grid 사용 시
            selenium_grid_url = os.getenv('SELENIUM_GRID_URL')
            if selenium_grid_url:
                from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
                self.driver = webdriver.Remote(
                    command_executor=selenium_grid_url,
                    desired_capabilities=DesiredCapabilities.CHROME,
                    options=options
                )
                print("🕸️ Selenium Grid 연결 완료")
            else:
                self.driver = webdriver.Chrome(options=options)
            
            # 자동화 감지 회피
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 타임아웃 설정
            self.driver.implicitly_wait(self.config['options'].get('wait_time', 2))
            self.driver.set_page_load_timeout(30)
            
            self.logger.info("✅ Chrome 드라이버 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 드라이버 초기화 실패: {e}")
            return False
    
    def find_element_robust(self, selectors, description, timeout=10):
        """여러 선택자를 시도해서 요소 찾기"""
        self.logger.debug(f"🔍 {description} 찾는 중...")
        
        for i, (by_type, selector, desc) in enumerate(selectors):
            try:
                self.logger.debug(f"  시도 {i+1}: {desc}")
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by_type, selector))
                )
                self.logger.debug(f"  ✅ 성공: {desc}")
                return element
                
            except Exception:
                continue
        
        raise Exception(f"{description}를 모든 방법으로 찾을 수 없습니다.")
    
    def login(self):
        """TAB + ENTER 방식 로그인 - 자동화"""
        try:
            user_id = self.config['login']['user_id']
            password = self.config['login']['password']
            
            # 로그인 시작 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_login_start(user_id))
            
            self.logger.info("🔐 TAB + ENTER 로그인 시작")
            self.driver.get("https://www.dhlottery.co.kr/user.do?method=login")
            time.sleep(3)
            
            # ID 입력 필드 찾기 (검증된 방식)
            id_selectors = [
                (By.ID, "userId", "기존 ID 선택자"),
                (By.NAME, "userId", "Name 속성"),
                (By.NAME, "user_id", "Name 속성 (언더스코어)"),
                (By.CSS_SELECTOR, "input[type='text']:first-of-type", "첫 번째 텍스트 입력"),
            ]
            
            id_input = self.find_element_robust(id_selectors, "ID 입력 필드", timeout=5)
            id_input.clear()
            id_input.send_keys(user_id)
            self.logger.info("✅ ID 입력 완료")
            
            # 비밀번호 입력 필드 찾기 (검증된 방식)
            password_selectors = [
                (By.NAME, "password", "Name 속성 (검증됨)"),
                (By.ID, "password", "기존 비밀번호 선택자"),
                (By.CSS_SELECTOR, "input[type='password']", "비밀번호 타입"),
                (By.NAME, "userPw", "UserPw"),
            ]
            
            pw_input = self.find_element_robust(password_selectors, "비밀번호 입력 필드", timeout=5)
            pw_input.clear()
            pw_input.send_keys(password)
            self.logger.info("✅ 비밀번호 입력 완료")
            
            # TAB + ENTER 방식으로 로그인 (검증된 방식)
            self.logger.info("🔄 TAB + ENTER 로그인 실행...")
            pw_input.send_keys(Keys.TAB)
            time.sleep(1)  # 포커스 이동 대기
            pw_input.send_keys(Keys.ENTER)
            
            # 로그인 처리 대기
            time.sleep(5)
            
            # 로그인 성공 확인
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            success_indicators = [
                "마이페이지", "로그아웃", "내정보", "예치금", "구매내역", "당첨조회"
            ]
            
            login_success = False
            
            # URL 변경 확인
            if "login" not in current_url.lower():
                login_success = True
                self.logger.info(f"✅ URL 변경 확인: {current_url}")
            
            # 페이지 내용 확인
            for indicator in success_indicators:
                if indicator in page_source:
                    login_success = True
                    self.logger.info(f"✅ 성공 지표 발견: {indicator}")
                    break
            
            if login_success:
                self.logger.info("🎉 TAB + ENTER 로그인 성공!")
                
                if self.notification_manager:
                    run_notification(self.notification_manager.notify_login_success(user_id))
                
                return True
            else:
                self.logger.error("❌ 로그인 실패")
                
                if self.notification_manager:
                    run_notification(self.notification_manager.notify_login_failure(user_id, "TAB + ENTER 로그인 실패"))
                
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 로그인 오류: {e}")
            return False
    
    def check_balance(self):
        """잔액 확인 - 자동화 (사용자 입력 제거)"""
        try:
            self.driver.get("https://www.dhlottery.co.kr/myPage.do?method=myPage")
            time.sleep(3)
            
            # 예치금 찾기 (향상된 방법)
            balance_selectors = [
                (By.XPATH, "//td[contains(text(), '예치금')]/following-sibling::td[contains(text(), '원')]"),
                (By.XPATH, "//strong[contains(text(), '원') and contains(text(), ',')]"),
                (By.XPATH, "//td[@class='ta_right' and contains(text(), '원')]"),
                (By.CSS_SELECTOR, "td.ta_right"),
                (By.XPATH, "//*[contains(text(), '원') and string-length(text()) > 3 and string-length(text()) < 20]"),
            ]
            
            for i, (selector_type, selector) in enumerate(balance_selectors):
                try:
                    elements = self.driver.find_elements(selector_type, selector)
                    for element in elements:
                        text = element.text.strip()
                        if not text:
                            continue
                            
                        # 숫자 추출 및 검증
                        import re
                        numbers = re.findall(r'[\d,]+', text)
                        
                        for number_str in numbers:
                            clean_number = number_str.replace(',', '')
                            if clean_number.isdigit() and len(clean_number) >= 3:
                                balance = int(clean_number)
                                if 0 <= balance <= 50000000:  # 5천만원 이하
                                    self.logger.info(f"✅ 예치금 발견: {balance:,}원")
                                    
                                    if self.notification_manager:
                                        run_notification(self.notification_manager.notify_balance_check(balance))
                                    
                                    return balance
                except Exception:
                    continue
            
            # 모든 방법 실패시 0원 반환 (사용자 입력 요청하지 않음)
            self.logger.warning("⚠️ 예치금을 찾을 수 없습니다. 0원으로 설정")
            
            # 디버그용 스크린샷만 저장
            if self.config['options'].get('save_screenshot'):
                try:
                    screenshot_path = f"screenshots/balance_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    self.driver.save_screenshot(screenshot_path)
                    self.logger.info(f"📷 디버그 스크린샷: {screenshot_path}")
                except:
                    pass
            
            return 0
            
        except Exception as e:
            self.logger.error(f"❌ 잔액 확인 실패: {e}")
            return 0
    
    def get_purchase_numbers(self, purchase_info):
        """설정 파일에서 번호 가져오기 또는 생성"""
        p_type = purchase_info['type']
        config_numbers = purchase_info.get('numbers', [])
        
        self.logger.info(f"📋 설정 확인 - {p_type}: {config_numbers}")
        
        if config_numbers:
            if p_type == '반자동' and len(config_numbers) == 3:
                self.logger.info(f"✅ 설정 번호 사용: {config_numbers}")
                return config_numbers
            elif p_type.startswith('수동') and len(config_numbers) == 6:
                self.logger.info(f"✅ 설정 번호 사용: {config_numbers}")
                return config_numbers
            else:
                self.logger.warning(f"⚠️ 번호 개수 오류, 자동 생성")
        
        # 자동 생성
        if p_type == '자동':
            return []
        elif p_type == '반자동':
            numbers = sorted(random.sample(range(1, 46), 3))
            self.logger.info(f"🎲 반자동 번호 생성: {numbers}")
            return numbers
        elif p_type == '수동(랜덤)':
            numbers = self.statistics.get_random_numbers()
            self.logger.info(f"🎲 랜덤 번호 생성: {numbers}")
            return numbers
        elif p_type == '수동(AI추천)':
            numbers = self.statistics.get_ai_recommended_numbers()
            self.logger.info(f"🤖 AI 추천 번호 생성: {numbers}")
            return numbers
        elif p_type == '수동(통계분석)':
            numbers = self.statistics.get_most_frequent_numbers(6)
            self.logger.info(f"📊 통계 번호 생성: {numbers}")
            return numbers
        else:
            return []

    def setup_purchase_page(self, purchase_count=1):
        """구매 페이지 설정"""
        try:
            self.logger.info("🎯 구매 페이지 설정...")
            self.driver.get("https://ol.dhlottery.co.kr/olotto/game/game645.do")
            
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "amoundApply"))
            )
            
            # 혼합선택 탭 활성화
            try:
                self.driver.execute_script("selectWayTab(0);")
                time.sleep(1)
            except Exception as e:
                self.logger.debug(f"탭 활성화 실패: {e}")
            
            # 적용수량 설정
            amount_select = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "amoundApply"))
            )
            select_obj = Select(amount_select)
            select_obj.select_by_value(str(purchase_count))
            self.logger.info(f"✅ 수량 {purchase_count} 설정")
            time.sleep(1)
            return True
                    
        except Exception as e:
            self.logger.error(f"구매 페이지 설정 실패: {e}")
            return False

    def click_number_enhanced(self, number):
        """번호 클릭"""
        try:
            checkbox = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, f"check645num{number}"))
            )
            
            if not checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", checkbox)
                time.sleep(0.3)
                return True
            return True
                        
        except Exception as e:
            self.logger.debug(f"번호 {number} 클릭 실패: {e}")
            return False

    def select_auto_numbers(self):
        """자동 번호 선택"""
        try:
            auto_checkbox = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "checkAutoSelect"))
            )
            
            if not auto_checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", auto_checkbox)
            
            time.sleep(1)
            
            confirm_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnSelectNum"))
            )
            self.driver.execute_script("arguments[0].click();", confirm_btn)
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"자동 선택 실패: {e}")
            return False

    def select_semi_auto_numbers(self, numbers):
        """반자동 번호 선택"""
        try:
            for num in numbers:
                self.click_number_enhanced(num)
                time.sleep(0.5)
            
            auto_checkbox = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "checkAutoSelect"))
            )
            if not auto_checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", auto_checkbox)
            
            time.sleep(1)
            
            confirm_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnSelectNum"))
            )
            self.driver.execute_script("arguments[0].click();", confirm_btn)
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"반자동 선택 실패: {e}")
            return False

    def select_manual_numbers(self, numbers):
        """수동 번호 선택"""
        try:
            for num in numbers:
                self.click_number_enhanced(num)
                time.sleep(0.5)
            
            time.sleep(1)
            
            confirm_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnSelectNum"))
            )
            self.driver.execute_script("arguments[0].click();", confirm_btn)
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"수동 선택 실패: {e}")
            return False

    def complete_purchase(self):
        """구매 완료"""
        try:
            buy_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnBuy"))
            )
            self.driver.execute_script("arguments[0].click();", buy_btn)
            self.logger.info("구매하기 버튼 클릭")
            time.sleep(3)
            
            # 구매 확인
            try:
                self.driver.execute_script("closepopupLayerConfirm(true);")
                confirmation_found = True
            except Exception:
                confirmation_found = False
            
            if not confirmation_found:
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
                        confirmation_found = True
                        break
                    except:
                        continue
            
            time.sleep(3)
            return confirmation_found
            
        except Exception as e:
            self.logger.error(f"구매 완료 실패: {e}")
            return False

    def buy_lotto_games(self, purchase_count):
        """로또 구매 실행"""
        try:
            self.logger.info(f"🎯 구매 시작 ({purchase_count}게임)")
            
            lotto_list = self.config['purchase']['lotto_list']
            success_count = 0
            
            for i in range(purchase_count):
                try:
                    if i < len(lotto_list):
                        purchase_info = lotto_list[i]
                    else:
                        purchase_info = lotto_list[-1] if lotto_list else {'type': '자동', 'numbers': []}
                    
                    p_type = purchase_info['type']
                    numbers = self.get_purchase_numbers(purchase_info)
                    
                    self.logger.info(f"🎮 [{i+1}] {p_type}: {numbers}")
                    
                    if not self.setup_purchase_page(1):
                        continue
                    
                    # 번호 선택
                    if p_type == '자동':
                        success = self.select_auto_numbers()
                    elif p_type == '반자동':
                        success = self.select_semi_auto_numbers(numbers)
                    elif '수동' in p_type:
                        success = self.select_manual_numbers(numbers)
                    else:
                        success = False
                    
                    if not success:
                        continue
                    
                    # 구매 완료
                    if self.complete_purchase():
                        success_count += 1
                        self.logger.info(f"✅ [{i+1}] 구매 성공!")
                        
                        if self.config['options'].get('save_screenshot'):
                            try:
                                screenshot_path = f"screenshots/purchase_{i+1}_{datetime.now().strftime('%H%M%S')}.png"
                                self.driver.save_screenshot(screenshot_path)
                            except:
                                pass
                        
                        time.sleep(3)
                    else:
                        self.logger.warning(f"❌ [{i+1}] 구매 실패")
                        
                except Exception as e:
                    self.logger.error(f"[{i+1}] 구매 오류: {e}")
                    continue
            
            return success_count
            
        except Exception as e:
            self.logger.error(f"구매 실패: {e}")
            return 0

    def run(self, immediate=False):
        """메인 실행 - 완전 자동화"""
        try:
            self.logger.info("🚀 TAB + ENTER 방식 자동화 로또 구매 시작")
            
            if self.notification_manager:
                run_notification(self.notification_manager.notify_program_start())
            
            # 드라이버 설정
            if not self.setup_driver():
                raise Exception("드라이버 초기화 실패")
            
            # TAB + ENTER 로그인
            if not self.login():
                raise Exception("TAB + ENTER 로그인 실패")
            
            # 잔액 확인
            balance = self.check_balance()
            
            # 자동충전 처리
            min_balance = self.config['payment'].get('min_balance', 5000)
            self.logger.info(f"💰 잔액: {balance:,}원, 최소: {min_balance:,}원")
            
            if balance < min_balance and self.auto_recharger:
                if self.config['payment'].get('auto_recharge', False):
                    recharge_amount = self.config['payment'].get('recharge_amount', 10000)
                    
                    if self.notification_manager:
                        run_notification(self.notification_manager.notify_recharge_start(recharge_amount))
                    
                    if self.auto_recharger.auto_recharge(self.driver, balance):
                        self.logger.info("💳 충전 완료!")
                        balance = self.check_balance()
                        
                        if self.notification_manager:
                            run_notification(self.notification_manager.notify_recharge_success(recharge_amount, balance))
                    else:
                        raise Exception("자동충전 실패")
                else:
                    if balance < 1000:
                        raise Exception("잔액 부족")
            
            # 로또 구매 (즉시 실행 또는 스케줄)
            if immediate or datetime.now().weekday() in [0, 3]:
                purchase_count = self.config['purchase']['count']
                
                if self.notification_manager:
                    run_notification(self.notification_manager.notify_purchase_start(purchase_count))
                
                success_count = self.buy_lotto_games(purchase_count)
                
                if success_count > 0:
                    self.logger.info(f"🎉 구매 완료: {success_count}/{purchase_count}")
                    
                    if self.notification_manager:
                        run_notification(self.notification_manager.notify_purchase_success(success_count, success_count * 1000))
                    
                    return True
                else:
                    raise Exception("구매된 게임 없음")
            else:
                self.logger.info("📅 구매 스케줄이 아님 (월/목 또는 --now)")
                return True
            
        except Exception as e:
            self.logger.error(f"❌ 실행 실패: {e}")
            
            if self.notification_manager:
                run_notification(self.notification_manager.notify_critical("시스템 실패", str(e)))
            
            return False
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

def main():
    """메인 함수 - 완전 자동화"""
    parser = argparse.ArgumentParser(description='TAB + ENTER 방식 자동화 로또 구매 시스템')
    parser.add_argument('--now', action='store_true', help='즉시 구매')
    parser.add_argument('--test', action='store_true', help='테스트 모드')
    parser.add_argument('--config', action='store_true', help='설정 확인')
    
    args = parser.parse_args()
    
    try:
        if args.config:
            # 설정 확인만
            buyer = TabEnterLottoBuyer()
            config_copy = buyer.config.copy()
            config_copy['login']['password'] = '***'
            print(json.dumps(config_copy, indent=2, ensure_ascii=False))
            return
        
        if args.test:
            # 테스트 모드 (실제 구매 안함)
            print("🧪 테스트 모드 - 실제 구매하지 않음")
            buyer = TabEnterLottoBuyer()
            print("✅ TAB + ENTER 방식 초기화 완료")
            return
        
        # 실제 실행
        buyer = TabEnterLottoBuyer()
        success = buyer.run(immediate=args.now)
        
        if success:
            print("✅ TAB + ENTER 방식 실행 성공")
        else:
            print("❌ 실행 실패")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 시스템 에러: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
