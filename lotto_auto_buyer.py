# lotto_auto_buyer.py - 통합 버전 (자동충전 기능 포함)
import json
import time
import logging
import os
import random
from datetime import datetime
from collections import Counter
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# Auto Recharge 모듈 import (안전한 방식)
try:
    from auto_recharge import AutoRecharger
    AUTO_RECHARGE_AVAILABLE = True
    print("✅ AutoRecharger 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ AutoRecharger 모듈 로드 실패: {e}")
    print("자동충전 기능이 비활성화됩니다.")
    AutoRecharger = None
    AUTO_RECHARGE_AVAILABLE = False

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
        """역대 1등 숫자들 중 가장 많이 사용된 숫자"""
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

class LottoAutoBuyer:
    def __init__(self, config_file="lotto_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.statistics = LottoStatistics()
        self.screenshot_dir = "screenshots"
        # AutoRecharger 초기화 (안전한 방식)
        self.recharger = None
        if AUTO_RECHARGE_AVAILABLE and self.config:
            try:
                self.recharger = AutoRecharger(self.config)
                self.logger.info("✅ 자동충전 기능 활성화")
            except Exception as e:
                self.logger.warning(f"⚠️ 자동충전 초기화 실패: {e}")
                self.recharger = None
        elif not AUTO_RECHARGE_AVAILABLE:
            self.logger.info("💳 자동충전 모듈이 비활성화되어 있습니다")
        
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
        
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
        
    def load_config(self):
        """설정파일 읽기"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"설정파일 {self.config_file}을 찾을 수 없습니다.")
            return None
            
    def setup_driver(self):
        """WebDriver 설정"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 도커 환경을 위한 추가 옵션
        if os.environ.get('DOCKER_ENV'):
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.implicitly_wait(3)
            driver.maximize_window()
            return driver
        except Exception as e:
            self.logger.error(f"WebDriver 설정 실패: {e}")
            return None

    def login(self, driver):
        """로그인 (빠른 속도 최적화)"""
        try:
            self.logger.info("🔐 동행복권 로그인...")
            driver.get("https://www.dhlottery.co.kr/user.do?method=login")
            time.sleep(1)  # 3초 → 1초
            
            # 1. ID 입력 필드 찾기
            id_input = None
            id_selectors = [
                (By.ID, "userId"),
                (By.NAME, "userId"),
                (By.CSS_SELECTOR, "input[name='userId']"),
                (By.XPATH, "//input[@placeholder='아이디' or contains(@class, 'user')]"),
                (By.CSS_SELECTOR, "input[type='text']:first-of-type")
            ]
            
            for selector_type, selector in id_selectors:
                try:
                    id_input = WebDriverWait(driver, 3).until(  # 5초 → 3초
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    self.logger.info(f"✅ ID 필드 발견: {selector}")
                    break
                except:
                    continue
            
            if not id_input:
                self.logger.error("❌ ID 입력 필드를 찾을 수 없습니다")
                return False
            
            # 2. 비밀번호 입력 필드 찾기
            pw_input = None
            pw_selectors = [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@placeholder='비밀번호' or contains(@class, 'password')]"),
            ]
            
            for selector_type, selector in pw_selectors:
                try:
                    pw_input = WebDriverWait(driver, 3).until(  # 5초 → 3초
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    self.logger.info(f"✅ 비밀번호 필드 발견: {selector}")
                    break
                except:
                    continue
            
            if not pw_input:
                self.logger.error("❌ 비밀번호 입력 필드를 찾을 수 없습니다")
                return False
            
            # 3. 로그인 정보 빠른 입력
            id_input.clear()
            id_input.send_keys(self.config['login']['user_id'])
            
            pw_input.clear()
            pw_input.send_keys(self.config['login']['password'])
            
            # time.sleep(1) 제거 - 대기 시간 제거
            
            # 4. 로그인 버튼 빠른 처리
            login_success = False
            login_selectors = [
                (By.CSS_SELECTOR, "input[type='submit'][value='로그인']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), '로그인')]"),
                (By.XPATH, "//input[@value='로그인']"),
            ]
            
            for selector_type, selector in login_selectors:
                try:
                    login_btn = WebDriverWait(driver, 3).until(  # 5초 → 3초
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    login_btn.click()
                    self.logger.info(f"✅ 로그인 버튼 클릭: {selector}")
                    login_success = True
                    break
                except:
                    continue
            
            if not login_success:
                # Enter 키로 대체
                try:
                    pw_input.send_keys(Keys.ENTER)
                    self.logger.info("✅ Enter 키로 로그인 시도")
                except:
                    self.logger.error("❌ 로그인 방법을 찾을 수 없습니다")
                    return False
            
            time.sleep(2)  # 5초 → 2초
            
            # 5. 로그인 성공 확인
            success_indicators = [
                "마이페이지", "로그아웃", "myPage", "logout", "main"
            ]
            
            current_url = driver.current_url
            page_source = driver.page_source
            
            for indicator in success_indicators:
                if indicator in current_url or indicator in page_source:
                    self.logger.info("✅ 로그인 성공!")
                    return True
            
            self.logger.error("❌ 로그인 실패 - 성공 지표를 찾을 수 없습니다")
            self.logger.info(f"현재 URL: {current_url[:100]}...")
            return False
            
        except Exception as e:
            self.logger.error(f"로그인 실패: {e}")
            return False

    def check_balance(self, driver):
        """잔액 확인 (강화된 방법)"""
        try:
            self.logger.info("💰 잔액 확인...")
            
            # 마이페이지로 이동
            balance_urls = [
                "https://www.dhlottery.co.kr/userSsl.do?method=myPage",
                "https://www.dhlottery.co.kr/myPage.do?method=myPage",
                "https://www.dhlottery.co.kr/user.do?method=myPage"
            ]
            
            for url in balance_urls:
                try:
                    driver.get(url)
                    time.sleep(3)
                    break
                except:
                    continue
            
            # 여러 방법으로 잔액 찾기
            balance_methods = [
                # 방법 1: strong 태그에서 찾기
                lambda: self._find_balance_in_elements(driver.find_elements(By.TAG_NAME, "strong")),
                # 방법 2: span 태그에서 찾기
                lambda: self._find_balance_in_elements(driver.find_elements(By.TAG_NAME, "span")),
                # 방법 3: td 태그에서 찾기
                lambda: self._find_balance_in_elements(driver.find_elements(By.TAG_NAME, "td")),
                # 방법 4: 특정 클래스로 찾기
                lambda: self._find_balance_in_elements(driver.find_elements(By.CSS_SELECTOR, ".money, .balance, .won, .amount")),
                # 방법 5: 바디 내 모든 텍스트에서 찾기
                lambda: self._find_balance_in_page_source(driver.page_source)
            ]
            
            for i, method in enumerate(balance_methods, 1):
                try:
                    balance = method()
                    if balance is not None:
                        self.logger.info(f"✅ 방법 {i}로 잔액 발견: {balance:,}원")
                        return balance
                except Exception as e:
                    self.logger.debug(f"방법 {i} 실패: {e}")
            
            # 모든 방법 실패시 경고
            self.logger.warning("⚠️ 잔액을 찾을 수 없어 수동 확인 필요")
            self.logger.info("📷 스크린샷 저장 중...")
            
            # 디버그용 스크린샷 저장
            try:
                screenshot_path = f"balance_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                driver.save_screenshot(screenshot_path)
                self.logger.info(f"📷 디버그 스크린샷: {screenshot_path}")
            except:
                pass
            
            # 사용자에게 수동 입력 요청
            self.logger.info("💰 잔액을 수동으로 입력해주세요:")
            try:
                manual_balance = input("잔액을 입력하세요 (숙자만): ")
                if manual_balance.isdigit():
                    balance = int(manual_balance)
                    self.logger.info(f"✅ 수동 입력 잔액: {balance:,}원")
                    return balance
            except KeyboardInterrupt:
                self.logger.info("사용자가 취소했습니다")
            except:
                pass
            
            # 최종 fallback
            self.logger.warning("⚠️ 잔액 확인 실패 - 0원으로 설정 (구매 중지)")
            return 0
            
        except Exception as e:
            self.logger.error(f"잔액 확인 실패: {e}")
            return 0
    
    def _find_balance_in_elements(self, elements):
        """요소들에서 잔액 찾기"""
        for elem in elements:
            try:
                text = elem.text.strip()
                balance = self._extract_balance_from_text(text)
                if balance is not None:
                    return balance
            except:
                continue
        return None
    
    def _find_balance_in_page_source(self, page_source):
        """페이지 소스에서 잔액 찾기"""
        import re
        
        # 여러 패턴으로 잔액 찾기
        patterns = [
            r'(나의예치금|예치금|잔액|보유금액)[^\d]*([\d,]+)\s*원',
            r'([\d,]+)\s*원[^\d]*(나의예치금|예치금|잔액|보유)',
            r'balance[^\d]*([\d,]+)',
            r'([\d,]+)\s*원.*사용가능',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    for group in match:
                        balance = self._extract_balance_from_text(group)
                        if balance is not None:
                            return balance
                else:
                    balance = self._extract_balance_from_text(match)
                    if balance is not None:
                        return balance
        
        return None
    
    def _extract_balance_from_text(self, text):
        """텍스트에서 잔액 추출"""
        if not text or not isinstance(text, str):
            return None
        
        # 숙자와 콤마만 추출
        clean_text = ''.join(c for c in text if c.isdigit() or c == ',')
        if not clean_text:
            return None
        
        try:
            # 콤마 제거 후 숫자 변환
            balance_str = clean_text.replace(",", "")
            if balance_str.isdigit():
                balance = int(balance_str)
                # 유효한 잔액 범위 확인 (0원 ~ 100만원)
                if 0 <= balance <= 1000000:
                    return balance
        except:
            pass
        
        return None

    def handle_alerts(self, driver):
        """알림 처리 (잔액 부족 등)"""
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            self.logger.warning(f"⚠️ Alert 감지: {alert_text}")
            
            # 잔액 부족 관련 메시지 체크
            insufficient_balance_keywords = [
                "잔액", "부족", "예치금", "충전", "balance", "insufficient"
            ]
            
            is_balance_error = any(keyword in alert_text for keyword in insufficient_balance_keywords)
            
            alert.accept()  # Alert 닫기
            
            if is_balance_error:
                self.logger.error("❌ 잔액 부족 Alert 감지 - 구매 중단")
                return "INSUFFICIENT_BALANCE"
            else:
                self.logger.info("ℹ️ 일반 Alert 처리 완료")
                return "ALERT_HANDLED"
                
        except Exception:
            # Alert이 없으면 정상
            return "NO_ALERT"
    
    def complete_purchase(self, driver):
        """구매 완료 (알림 처리 포함)"""
        try:
            self.logger.info("구매하기 버튼 클릭")
            
            # 구매 버튼 찾기 및 클릭
            purchase_selectors = [
                (By.CSS_SELECTOR, "input[type='submit'][value='구매하기']"),
                (By.CSS_SELECTOR, "button[onclick*='purchase']"),
                (By.XPATH, "//input[@value='구매하기']"),
                (By.XPATH, "//button[contains(text(), '구매')]"),
                (By.CSS_SELECTOR, ".btn_purchase, .purchase-btn")
            ]
            
            purchase_clicked = False
            for selector_type, selector in purchase_selectors:
                try:
                    purchase_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    purchase_btn.click()
                    self.logger.info(f"✅ 구매 버튼 클릭: {selector}")
                    purchase_clicked = True
                    break
                except:
                    continue
            
            if not purchase_clicked:
                # JavaScript로 직접 함수 호출 시도
                try:
                    driver.execute_script("""
                        if (typeof lottoTicketPurchase === 'function') {
                            lottoTicketPurchase();
                        } else if (typeof purchase === 'function') {
                            purchase();
                        } else if (typeof buyLotto === 'function') {
                            buyLotto();
                        }
                    """)
                    self.logger.info("✅ JavaScript 함수 직접 호출 성공")
                    purchase_clicked = True
                except Exception as e:
                    self.logger.error(f"❌ 구매 버튼 클릭 실패: {e}")
                    return False
            
            # 알림 처리 대기
            time.sleep(3)
            
            # Alert 체크
            alert_result = self.handle_alerts(driver)
            
            if alert_result == "INSUFFICIENT_BALANCE":
                self.logger.error("❌ 잔액 부족으로 구매 실패")
                return False
            elif alert_result == "ALERT_HANDLED":
                self.logger.warning("⚠️ 알림 처리 후 계속")
            
            # 구매 성공 확인
            time.sleep(2)
            
            # 성공 지표 체크
            success_indicators = [
                "구매완료", "구매성공", "success", "complete", "결제완료"
            ]
            
            page_source = driver.page_source
            current_url = driver.current_url
            
            for indicator in success_indicators:
                if indicator in page_source or indicator in current_url:
                    self.logger.info(f"✅ 구매 성공 지표 발견: {indicator}")
                    return True
            
            # 추가 체크: URL 변화 확인
            if "complete" in current_url or "result" in current_url:
                self.logger.info("✅ URL 변화로 구매 성공 확인")
                return True
            
            self.logger.warning("⚠️ 구매 성공 여부를 확인할 수 없습니다")
            return True  # 기본적으로 성공으로 간주
            
        except Exception as e:
            self.logger.error(f"구매 완료 처리 실패: {e}")
            return False
    def auto_recharge(self, driver, current_balance):
        """자동충전 기능"""
        if self.recharger:
            return self.recharger.auto_recharge(driver, current_balance)
        else:
            self.logger.error("자동충전 모듈이 초기화되지 않았습니다.")
            return False

    def click_number_enhanced(self, driver, number):
        """강화된 번호 클릭 방법 - 5가지 방법 시도"""
        try:
            self.logger.info(f"🎯 번호 {number} 클릭 시도...")
            
            # 방법 1: 체크박스 직접 클릭
            try:
                checkbox = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, f"check645num{number}"))
                )
                
                if checkbox.is_displayed() and checkbox.is_enabled():
                    if not checkbox.is_selected():
                        driver.execute_script("arguments[0].click();", checkbox)
                        self.logger.info(f"  ✅ 방법1 성공: 체크박스 직접 클릭 ({number})")
                        time.sleep(0.3)
                        return True
                    else:
                        self.logger.info(f"  ℹ️ 번호 {number} 이미 선택됨")
                        return True
                        
            except Exception as e:
                self.logger.debug(f"  방법1 실패: {e}")
            
            # 방법 2: 라벨 클릭
            try:
                label = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"label[for='check645num{number}']"))
                )
                driver.execute_script("arguments[0].click();", label)
                self.logger.info(f"  ✅ 방법2 성공: 라벨 클릭 ({number})")
                time.sleep(0.3)
                return True
                
            except Exception as e:
                self.logger.debug(f"  방법2 실패: {e}")
            
            # 방법 3: JavaScript 함수 직접 호출
            try:
                driver.execute_script(f"""
                    var checkbox = document.getElementById('check645num{number}');
                    checkbox.checked = true;
                    if (typeof checkLength645 === 'function') {{
                        checkLength645($(checkbox));
                    }}
                """)
                self.logger.info(f"  ✅ 방법3 성공: JavaScript 함수 호출 ({number})")
                time.sleep(0.3)
                return True
                
            except Exception as e:
                self.logger.debug(f"  방법3 실패: {e}")
            
            # 방법 4: 마우스 클릭 시뮬레이션
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                
                label = driver.find_element(By.CSS_SELECTOR, f"label[for='check645num{number}']")
                actions = ActionChains(driver)
                actions.move_to_element(label).click().perform()
                self.logger.info(f"  ✅ 방법4 성공: 마우스 액션 ({number})")
                time.sleep(0.3)
                return True
                
            except Exception as e:
                self.logger.debug(f"  방법4 실패: {e}")
            
            # 방법 5: 강제 체크 설정
            try:
                driver.execute_script(f"""
                    var checkbox = document.getElementById('check645num{number}');
                    if (checkbox) {{
                        checkbox.checked = true;
                        checkbox.setAttribute('checked', 'checked');
                        var event = new Event('change');
                        checkbox.dispatchEvent(event);
                    }}
                """)
                self.logger.info(f"  ✅ 방법5 성공: 강제 체크 설정 ({number})")
                time.sleep(0.3)
                return True
                
            except Exception as e:
                self.logger.debug(f"  방법5 실패: {e}")
            
            self.logger.warning(f"  ❌ 번호 {number} 클릭 모든 방법 실패")
            return False
            
        except Exception as e:
            self.logger.error(f"번호 {number} 클릭 중 오류: {e}")
            return False

    def verify_number_selection(self, driver, numbers):
        """번호 선택 확인"""
        try:
            selected_count = 0
            selected_numbers = []
            
            for num in numbers:
                try:
                    checkbox = driver.find_element(By.ID, f"check645num{num}")
                    if checkbox.is_selected():
                        selected_count += 1
                        selected_numbers.append(num)
                except:
                    pass
            
            self.logger.info(f"🔍 선택 확인: {selected_count}/{len(numbers)}개 선택됨 - {selected_numbers}")
            return selected_count, selected_numbers
            
        except Exception as e:
            self.logger.error(f"번호 선택 확인 실패: {e}")
            return 0, []

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

    def setup_purchase_page(self, driver, purchase_count=1):
        """구매 페이지 초기 설정"""
        try:
            self.logger.info("🎯 로또 구매 페이지 설정...")
            driver.get("https://ol.dhlottery.co.kr/olotto/game/game645.do")
            time.sleep(3)
            
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "amoundApply"))
            )
            
            try:
                driver.execute_script("selectWayTab(0);")
                time.sleep(1)
                self.logger.info("✅ 혼합선택 탭 활성화")
            except Exception as e:
                self.logger.warning(f"혼합선택 탭 활성화 실패: {e}")
            
            try:
                amount_select = WebDriverWait(driver, 10).until(
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

    def select_auto_numbers(self, driver):
        """자동 번호 선택"""
        try:
            auto_selected = False
            
            try:
                auto_checkbox = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "checkAutoSelect"))
                )
                
                if not auto_checkbox.is_selected():
                    driver.execute_script("arguments[0].click();", auto_checkbox)
                    auto_selected = True
                    self.logger.info("자동선택 체크박스 클릭")
                else:
                    auto_selected = True
                    self.logger.info("자동선택 이미 체크됨")
                    
            except Exception as e:
                self.logger.debug(f"자동선택 실패: {e}")
            
            if not auto_selected:
                try:
                    driver.execute_script("""
                        var checkbox = document.getElementById('checkAutoSelect');
                        if (checkbox) {
                            checkbox.checked = true;
                            checkbox.setAttribute('checked', 'checked');
                        }
                    """)
                    auto_selected = True
                    self.logger.info("자동선택 강제 설정")
                except Exception as e:
                    self.logger.debug(f"자동선택 강제 설정 실패: {e}")
            
            if not auto_selected:
                return False
            
            time.sleep(1)
            
            try:
                confirm_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnSelectNum"))
                )
                driver.execute_script("arguments[0].click();", confirm_btn)
                time.sleep(2)
                return True
            except Exception as e:
                self.logger.error(f"확인 버튼 클릭 실패: {e}")
                return False
            
        except Exception as e:
            self.logger.error(f"자동 번호 선택 실패: {e}")
            return False

    def select_semi_auto_numbers(self, driver, numbers):
        """반자동 번호 선택"""
        try:
            self.logger.info(f"반자동 번호 선택: {numbers}")
            
            for num in numbers:
                if self.click_number_enhanced(driver, num):
                    pass
                time.sleep(0.5)
            
            actual_count, actual_numbers = self.verify_number_selection(driver, numbers)
            self.logger.info(f"반자동 번호 선택 결과: {actual_count}/{len(numbers)}개")
            
            try:
                auto_checkbox = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "checkAutoSelect"))
                )
                if not auto_checkbox.is_selected():
                    driver.execute_script("arguments[0].click();", auto_checkbox)
                    self.logger.info("반자동용 자동선택 체크박스 클릭")
            except Exception as e:
                self.logger.warning(f"반자동용 자동선택 실패: {e}")
            
            time.sleep(1)
            
            try:
                confirm_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnSelectNum"))
                )
                driver.execute_script("arguments[0].click();", confirm_btn)
                time.sleep(2)
                return True
            except Exception as e:
                self.logger.error(f"반자동 확인 버튼 클릭 실패: {e}")
                return False
            
        except Exception as e:
            self.logger.error(f"반자동 번호 선택 실패: {e}")
            return False

    def select_manual_numbers(self, driver, numbers):
        """수동 번호 선택"""
        try:
            self.logger.info(f"수동 번호 선택: {numbers}")
            
            for num in numbers:
                if self.click_number_enhanced(driver, num):
                    pass
                time.sleep(0.5)
            
            actual_count, actual_numbers = self.verify_number_selection(driver, numbers)
            self.logger.info(f"수동 번호 선택 결과: {actual_count}/{len(numbers)}개")
            
            time.sleep(1)
            
            try:
                confirm_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnSelectNum"))
                )
                driver.execute_script("arguments[0].click();", confirm_btn)
                time.sleep(2)
                return True
            except Exception as e:
                self.logger.error(f"수동 확인 버튼 클릭 실패: {e}")
                return False
            
        except Exception as e:
            self.logger.error(f"수동 번호 선택 실패: {e}")
            return False

    def complete_purchase(self, driver):
        """구매 완료 처리"""
        try:
            buy_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnBuy"))
            )
            driver.execute_script("arguments[0].click();", buy_btn)
            self.logger.info("구매하기 버튼 클릭")
            time.sleep(3)
            
            confirmation_found = False
            
            try:
                driver.execute_script("closepopupLayerConfirm(true);")
                self.logger.info("✅ JavaScript 함수 직접 호출 성공")
                confirmation_found = True
            except Exception as e:
                self.logger.debug(f"JavaScript 함수 호출 실패: {e}")
            
            if not confirmation_found:
                confirm_selectors = [
                    "//input[@value='확인' and contains(@onclick, 'closepopupLayerConfirm(true)')]",
                    "//input[@value='확인']",
                    "//button[contains(text(), '확인')]",
                    "//input[@value='OK']",
                    "//button[contains(text(), 'OK')]"
                ]
                
                for selector in confirm_selectors:
                    try:
                        confirm_btn = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        driver.execute_script("arguments[0].click();", confirm_btn)
                        self.logger.info(f"✅ 구매 확인 버튼 클릭")
                        confirmation_found = True
                        break
                    except:
                        continue
            
            if not confirmation_found:
                try:
                    WebDriverWait(driver, 3).until(EC.alert_is_present())
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    self.logger.info(f"💬 Alert: {alert_text}")
                    
                    if "구매" in alert_text or "확인" in alert_text:
                        alert.accept()
                        self.logger.info("✅ Alert 확인 완료")
                        confirmation_found = True
                    else:
                        alert.dismiss()
                except:
                    pass
            
            time.sleep(3)
            return confirmation_found
            
        except Exception as e:
            self.logger.error(f"구매 완료 처리 실패: {e}")
            return False

    def take_screenshot(self, driver, filename_prefix="purchase"):
        """스크린샷 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            driver.save_screenshot(filepath)
            self.logger.info(f"📸 스크린샷 저장: {filename}")
            return filepath
        except Exception as e:
            self.logger.error(f"스크린샷 저장 실패: {e}")
            return None

    def buy_lotto_games(self, driver, purchase_count):
        """로또 구매 실행"""
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
                    
                    self.logger.info(f"")
                    self.logger.info(f"🎮 [{i+1}/{purchase_count}] {p_type} 구매 시작...")
                    self.logger.info(f"📋 사용할 번호: {numbers}")
                    
                    if not self.setup_purchase_page(driver, 1):
                        continue
                    
                    # 구매 방식에 따른 처리
                    if p_type == '자동':
                        if self.select_auto_numbers(driver):
                            self.logger.info(f"    ✅ 자동 번호 선택 완료")
                        else:
                            continue
                            
                    elif p_type == '반자동':
                        if self.select_semi_auto_numbers(driver, numbers):
                            self.logger.info(f"    ✅ 반자동 번호 선택 완료: {numbers}")
                        else:
                            continue
                            
                    elif '수동' in p_type:
                        if self.select_manual_numbers(driver, numbers):
                            self.logger.info(f"    ✅ 수동 번호 선택 완료: {numbers}")
                        else:
                            continue
                    
                    # 구매 완료
                    if self.complete_purchase(driver):
                        success_count += 1
                        self.logger.info(f"    🎉 [{i+1}] {p_type} 구매 성공!")
                        
                        # 스크린샷 저장
                        if self.config['options'].get('save_screenshot', True):
                            self.take_screenshot(driver, f"purchase_{i+1}_{p_type}")
                        
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
            
            self.logger.info(f"📝 구매 내역 저장 완료")
            
        except Exception as e:
            self.logger.error(f"구매 내역 저장 실패: {e}")

    def run(self):
        """메인 실행 함수"""
        if not self.config:
            self.logger.error("설정파일을 불러올 수 없습니다.")
            return
            
        self.logger.info("🎲 로또 자동 구매 시작!")
        self.logger.info("🔧 통합 버전 (자동충전 기능 포함)")
        
        driver = self.setup_driver()
        if not driver:
            return
            
        try:
            # 1. 로그인
            if not self.login(driver):
                self.logger.error("로그인 실패")
                return
            
            # 2. 잔액 확인
            balance = self.check_balance(driver)
            purchase_count = self.config['purchase']['count']
            required_amount = purchase_count * 1000
            
            self.logger.info(f"💰 잔액: {balance:,}원, 필요금액: {required_amount:,}원")
            
            # 3. 자동충전 처리
            min_balance = self.config['payment'].get('min_balance', 5000)
            auto_recharge_enabled = self.config['payment'].get('auto_recharge', False)
            
            self.logger.info(f"💳 자동충전 설정 확인:")
            self.logger.info(f"  - 현재 잔액: {balance:,}원")
            self.logger.info(f"  - 최소 잔액: {min_balance:,}원")
            self.logger.info(f"  - 자동충전 설정: {auto_recharge_enabled}")
            self.logger.info(f"  - AutoRecharger 상태: {'Available' if self.recharger else 'None'}")
            
            if balance < min_balance:  # 최소 잔액 이하면 충전
                self.logger.info(f"💳 잔액이 {min_balance:,}원 이하입니다. 자동충전을 시도합니다.")
                if auto_recharge_enabled:
                    if self.recharger:  # AutoRecharger 객체가 있을 때만
                        self.logger.info("🔄 자동충전 시작...")
                        if self.auto_recharge(driver, balance):
                            # 충전 후 잔액 재확인
                            self.logger.info("✅ 자동충전 성공! 잔액 재확인 중...")
                            balance = self.check_balance(driver)
                            self.logger.info(f"💰 충전 후 잔액: {balance:,}원")
                        else:
                            self.logger.error("❌ 자동충전 실패. 수동으로 충전 후 다시 실행해주세요.")
                            return
                    else:
                        self.logger.error("❌ AutoRecharger 객체가 초기화되지 않았습니다.")
                        self.logger.info("💳 수동으로 충전 후 다시 실행해주세요.")
                        if balance < 1000:  # 1게임도 구매 불가
                            self.logger.error("❌ 잔액 부족으로 구매할 수 없습니다.")
                            return
                else:
                    self.logger.warning("⚠️ 자동충전이 비활성화되어 있습니다.")
                    self.logger.info("💳 설정 파일에서 'auto_recharge'를 true로 변경해주세요.")
                    if balance < 1000:  # 1게임도 구매 불가
                        self.logger.error("❌ 잔액 부족으로 구매할 수 없습니다.")
                        return
            else:
                self.logger.info(f"✅ 잔액이 충분합니다 ({balance:,}원 >= {min_balance:,}원)")
            
            # 4. 구매 가능 게임 수 조정
            if balance < required_amount:
                max_games = balance // 1000
                if max_games <= 0:
                    self.logger.error("💸 잔액 부족으로 구매할 수 없습니다.")
                    return
                purchase_count = max_games
                self.logger.info(f"🎯 잔액에 맞춰 구매 수량 조정: {purchase_count}게임")
            
            # 5. 로또 구매
            success_count = self.buy_lotto_games(driver, purchase_count)
            
            # 6. 결과 보고
            if success_count > 0:
                self.logger.info("")
                self.logger.info("🎉" + "="*50)
                self.logger.info(f"🎉 로또 구매 완료!")
                self.logger.info(f"📊 구매 결과: {success_count}/{purchase_count}게임 성공")
                self.logger.info(f"💰 총 구매금액: {success_count * 1000:,}원")
                self.logger.info(f"💳 남은 잔액: {balance - (success_count * 1000):,}원")
                self.logger.info(f"📸 스크린샷: {self.screenshot_dir}/ 폴더")
                self.logger.info("🎉" + "="*50)
                
                # 구매 내역 저장
                self.save_purchase_history(success_count, purchase_count)
                
            else:
                self.logger.error("❌ 구매된 게임이 없습니다.")
                
        except Exception as e:
            self.logger.error(f"프로세스 오류: {e}")
            import traceback
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
        finally:
            self.logger.info("🔚 5초 후 브라우저 종료...")
            time.sleep(5)
            driver.quit()

def main():
    """메인 함수"""
    buyer = LottoAutoBuyer()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        buyer.run()
    else:
        print("사용법: python lotto_auto_buyer.py --now")
        print()
        print("🔧 통합 버전 기능:")
        print("  ✅ 강화된 번호 클릭 (5가지 방법)")
        print("  ✅ 설정 파일 번호 정확 사용")
        print("  ✅ 자동충전 기능 (5000원 이하)")
        print("  ✅ 도커 환경 지원")
        print("  ✅ GUI 대시보드 준비")
        print()
        print("💡 자동충전 설정:")
        print("  - 설정 파일에서 'auto_recharge': true")
        print("  - 최소 잔액: 5000원")
        print("  - 충전 금액: 50000원 (설정 가능)")

if __name__ == "__main__":
    main()
