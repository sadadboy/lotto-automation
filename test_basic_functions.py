#!/usr/bin/env python3
"""
로또 기본 기능 테스트 스크립트
자동화 전에 핵심 기능들이 제대로 작동하는지 확인
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 현재 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

class LottoFunctionTester:
    """로또 기본 기능 테스트 클래스"""
    
    def __init__(self):
        self.driver = None
        self.test_results = {}
        self.setup_logging()
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test_results.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_test_credentials(self):
        """테스트용 인증정보 가져오기"""
        # 1. 환경변수에서 시도
        if os.getenv('LOTTO_USER_ID') and os.getenv('LOTTO_PASSWORD'):
            return {
                'user_id': os.getenv('LOTTO_USER_ID'),
                'password': os.getenv('LOTTO_PASSWORD')
            }
        
        # 2. .env 파일에서 시도
        if os.path.exists('.env'):
            env_vars = {}
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
            
            if env_vars.get('LOTTO_USER_ID') and env_vars.get('LOTTO_PASSWORD'):
                return {
                    'user_id': env_vars['LOTTO_USER_ID'],
                    'password': env_vars['LOTTO_PASSWORD']
                }
        
        # 3. 수동 입력
        print("🔐 테스트용 인증정보를 입력하세요:")
        user_id = input("로또 사이트 ID: ").strip()
        password = input("로또 사이트 비밀번호: ").strip()
        
        if user_id and password:
            return {'user_id': user_id, 'password': password}
        else:
            raise Exception("인증정보가 입력되지 않았습니다.")
    
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            options = Options()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # 테스트는 GUI 모드로 실행 (문제 확인을 위해)
            options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("✅ Chrome 드라이버 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 드라이버 초기화 실패: {e}")
            return False
    
    def test_login(self, credentials):
        """로그인 기능 테스트"""
        test_name = "로그인"
        self.logger.info(f"🧪 {test_name} 테스트 시작")
        
        try:
            user_id = credentials['user_id']
            password = credentials['password']
            
            # 로그인 페이지 접속
            self.driver.get("https://www.dhlottery.co.kr/user.do?method=login")
            time.sleep(2)
            
            # ID 입력 필드 찾기 및 입력
            try:
                id_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "userId"))
                )
                id_input.clear()
                id_input.send_keys(user_id)
                self.logger.info("  ✅ ID 입력 완료")
            except Exception as e:
                raise Exception(f"ID 입력 필드를 찾을 수 없습니다: {e}")
            
            # 비밀번호 입력 필드 찾기 및 입력
            try:
                pw_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "password"))
                )
                pw_input.clear()
                pw_input.send_keys(password)
                self.logger.info("  ✅ 비밀번호 입력 완료")
            except Exception as e:
                raise Exception(f"비밀번호 입력 필드를 찾을 수 없습니다: {e}")
            
            # 로그인 버튼 클릭
            try:
                login_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][value='로그인']"))
                )
                login_btn.click()
                self.logger.info("  ✅ 로그인 버튼 클릭 완료")
            except Exception as e:
                raise Exception(f"로그인 버튼을 찾을 수 없습니다: {e}")
            
            # 로그인 결과 확인
            time.sleep(3)
            
            if "마이페이지" in self.driver.page_source or "로그아웃" in self.driver.page_source:
                self.logger.info("  ✅ 로그인 성공 확인")
                self.test_results[test_name] = {"status": "성공", "message": "정상 로그인"}
                return True
            else:
                # 오류 메시지 확인
                try:
                    error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert, .warning")
                    error_msg = ""
                    for element in error_elements:
                        if element.text.strip():
                            error_msg = element.text.strip()
                            break
                    
                    if not error_msg:
                        error_msg = "로그인 후 예상되는 요소를 찾을 수 없음"
                    
                    raise Exception(f"로그인 실패: {error_msg}")
                    
                except Exception as inner_e:
                    raise Exception(f"로그인 실패: {inner_e}")
                    
        except Exception as e:
            self.logger.error(f"  ❌ {test_name} 실패: {e}")
            self.test_results[test_name] = {"status": "실패", "message": str(e)}
            return False
    
    def test_balance_check(self):
        """잔액 확인 기능 테스트"""
        test_name = "잔액 확인"
        self.logger.info(f"🧪 {test_name} 테스트 시작")
        
        try:
            # 마이페이지로 이동
            self.driver.get("https://www.dhlottery.co.kr/myPage.do?method=myPage")
            time.sleep(3)
            
            # 예치금 찾기 시도
            balance_selectors = [
                (By.XPATH, "//td[contains(text(), '예치금')]/following-sibling::td[contains(text(), '원')]"),
                (By.XPATH, "//strong[contains(text(), '원') and contains(text(), ',')]"),
                (By.XPATH, "//td[@class='ta_right' and contains(text(), '원') and not(contains(text(), '0 원'))]"),
                (By.CSS_SELECTOR, "td.ta_right:not(:empty)"),
                (By.XPATH, "//*[contains(text(), '원') and string-length(text()) > 3]")
            ]
            
            balance_found = False
            balance_amount = 0
            
            for i, (selector_type, selector) in enumerate(balance_selectors):
                try:
                    elements = self.driver.find_elements(selector_type, selector)
                    self.logger.info(f"  🔍 선택자 {i+1}: {len(elements)}개 요소 발견")
                    
                    for j, element in enumerate(elements):
                        try:
                            text = element.text.strip()
                            self.logger.info(f"    - 요소 {j+1}: '{text}'")
                            
                            # 숫자 추출
                            clean_text = ''.join(c for c in text if c.isdigit() or c == ',')
                            clean_text = clean_text.replace(',', '')
                            
                            if clean_text.isdigit() and len(clean_text) >= 3:
                                balance = int(clean_text)
                                if 0 <= balance <= 10000000:  # 합리적인 범위
                                    balance_amount = balance
                                    balance_found = True
                                    self.logger.info(f"  ✅ 예치금 발견: {balance:,}원")
                                    break
                                    
                        except Exception as inner_e:
                            self.logger.debug(f"    요소 파싱 실패: {inner_e}")
                            continue
                    
                    if balance_found:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"  선택자 {i+1} 시도 실패: {e}")
                    continue
            
            if balance_found:
                self.test_results[test_name] = {
                    "status": "성공", 
                    "message": f"예치금 {balance_amount:,}원 확인", 
                    "balance": balance_amount
                }
                return True
            else:
                # 페이지 소스 일부 저장 (디버깅용)
                with open('balance_debug.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                
                self.logger.warning("  ⚠️ 예치금을 찾을 수 없습니다. 페이지 소스를 저장했습니다.")
                self.test_results[test_name] = {
                    "status": "경고", 
                    "message": "예치금 요소를 찾을 수 없음 (페이지 구조 변경 가능성)"
                }
                return False
                
        except Exception as e:
            self.logger.error(f"  ❌ {test_name} 실패: {e}")
            self.test_results[test_name] = {"status": "실패", "message": str(e)}
            return False
    
    def test_purchase_page_access(self):
        """구매 페이지 접근 테스트"""
        test_name = "구매 페이지 접근"
        self.logger.info(f"🧪 {test_name} 테스트 시작")
        
        try:
            # 로또 구매 페이지로 이동
            self.driver.get("https://ol.dhlottery.co.kr/olotto/game/game645.do")
            time.sleep(3)
            
            # 핵심 요소들 확인
            required_elements = [
                ("amoundApply", "적용수량 선택"),
                ("btnSelectNum", "확인 버튼"),
                ("btnBuy", "구매하기 버튼")
            ]
            
            missing_elements = []
            found_elements = []
            
            for element_id, description in required_elements:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, element_id))
                    )
                    found_elements.append(description)
                    self.logger.info(f"  ✅ {description} 요소 확인")
                except:
                    missing_elements.append(description)
                    self.logger.warning(f"  ❌ {description} 요소 누락")
            
            if not missing_elements:
                self.test_results[test_name] = {
                    "status": "성공", 
                    "message": "모든 구매 관련 요소 확인"
                }
                return True
            else:
                self.test_results[test_name] = {
                    "status": "부분성공", 
                    "message": f"일부 요소 누락: {', '.join(missing_elements)}"
                }
                return len(found_elements) > len(missing_elements)
                
        except Exception as e:
            self.logger.error(f"  ❌ {test_name} 실패: {e}")
            self.test_results[test_name] = {"status": "실패", "message": str(e)}
            return False
    
    def test_number_selection(self):
        """번호 선택 기능 테스트"""
        test_name = "번호 선택"
        self.logger.info(f"🧪 {test_name} 테스트 시작")
        
        try:
            # 구매 페이지에 있는지 확인
            current_url = self.driver.current_url
            if "game645" not in current_url:
                self.driver.get("https://ol.dhlottery.co.kr/olotto/game/game645.do")
                time.sleep(3)
            
            # 번호 선택 테스트 (1, 2, 3번 선택 시도)
            test_numbers = [1, 2, 3]
            selected_numbers = []
            
            for number in test_numbers:
                try:
                    # 체크박스 클릭 시도
                    checkbox_id = f"check645num{number}"
                    checkbox = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, checkbox_id))
                    )
                    
                    if checkbox.is_displayed() and checkbox.is_enabled():
                        if not checkbox.is_selected():
                            self.driver.execute_script("arguments[0].click();", checkbox)
                            time.sleep(0.5)
                            
                            # 선택 확인
                            if checkbox.is_selected():
                                selected_numbers.append(number)
                                self.logger.info(f"  ✅ 번호 {number} 선택 성공")
                            else:
                                self.logger.warning(f"  ⚠️ 번호 {number} 선택 실패")
                        else:
                            selected_numbers.append(number)
                            self.logger.info(f"  ✅ 번호 {number} 이미 선택됨")
                    else:
                        self.logger.warning(f"  ❌ 번호 {number} 체크박스 비활성화")
                        
                except Exception as e:
                    self.logger.warning(f"  ❌ 번호 {number} 선택 실패: {e}")
                    continue
            
            if selected_numbers:
                self.test_results[test_name] = {
                    "status": "성공" if len(selected_numbers) == len(test_numbers) else "부분성공",
                    "message": f"선택된 번호: {selected_numbers}"
                }
                return True
            else:
                self.test_results[test_name] = {
                    "status": "실패",
                    "message": "모든 번호 선택 실패"
                }
                return False
                
        except Exception as e:
            self.logger.error(f"  ❌ {test_name} 실패: {e}")
            self.test_results[test_name] = {"status": "실패", "message": str(e)}
            return False
    
    def test_auto_recharge_access(self):
        """자동충전 페이지 접근 테스트"""
        test_name = "자동충전 접근"
        self.logger.info(f"🧪 {test_name} 테스트 시작")
        
        try:
            # 충전 페이지로 이동
            self.driver.get("https://www.dhlottery.co.kr/payment.do?method=payment")
            time.sleep(3)
            
            # 충전 관련 요소 확인
            recharge_indicators = [
                "충전",
                "입금",
                "계좌이체",
                "신용카드",
                "결제"
            ]
            
            page_text = self.driver.page_source
            found_indicators = []
            
            for indicator in recharge_indicators:
                if indicator in page_text:
                    found_indicators.append(indicator)
                    self.logger.info(f"  ✅ '{indicator}' 관련 요소 발견")
            
            if found_indicators:
                self.test_results[test_name] = {
                    "status": "성공",
                    "message": f"충전 관련 요소 확인: {', '.join(found_indicators)}"
                }
                return True
            else:
                self.test_results[test_name] = {
                    "status": "실패",
                    "message": "충전 관련 요소를 찾을 수 없음"
                }
                return False
                
        except Exception as e:
            self.logger.error(f"  ❌ {test_name} 실패: {e}")
            self.test_results[test_name] = {"status": "실패", "message": str(e)}
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🔍 로또 시스템 기본 기능 테스트 시작")
        print("=" * 50)
        
        # 인증정보 가져오기
        try:
            credentials = self.get_test_credentials()
        except Exception as e:
            print(f"❌ 인증정보 로드 실패: {e}")
            return False
        
        # 드라이버 설정
        if not self.setup_driver():
            print("❌ 드라이버 설정 실패")
            return False
        
        try:
            # 테스트 실행
            tests = [
                ("로그인", lambda: self.test_login(credentials)),
                ("잔액 확인", self.test_balance_check),
                ("구매 페이지 접근", self.test_purchase_page_access),
                ("번호 선택", self.test_number_selection),
                ("자동충전 접근", self.test_auto_recharge_access)
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                print(f"\n📋 {test_name} 테스트...")
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(2)  # 테스트 간 간격
            
            # 결과 출력
            self.print_test_summary(passed_tests, total_tests)
            
            return passed_tests == total_tests
            
        except Exception as e:
            self.logger.error(f"테스트 실행 중 오류: {e}")
            return False
        finally:
            if self.driver:
                input("\n🔍 브라우저를 확인하려면 Enter를 누르세요...")
                self.driver.quit()
    
    def print_test_summary(self, passed, total):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        
        for test_name, result in self.test_results.items():
            status = result["status"]
            message = result["message"]
            
            if status == "성공":
                print(f"✅ {test_name}: {message}")
            elif status == "부분성공":
                print(f"⚠️  {test_name}: {message}")
            else:
                print(f"❌ {test_name}: {message}")
        
        print(f"\n🎯 전체 결과: {passed}/{total} 테스트 통과")
        
        if passed == total:
            print("🎉 모든 기본 기능이 정상 작동합니다!")
            print("✅ 자동화 시스템 구축을 진행할 수 있습니다.")
        else:
            print("⚠️ 일부 기능에 문제가 있습니다.")
            print("🔧 문제를 해결한 후 자동화를 진행하세요.")
        
        # 다음 단계 안내
        print("\n💡 다음 단계:")
        if passed == total:
            print("1. 실제 구매 테스트 (소액)")
            print("2. 자동충전 테스트 (필요시)")
            print("3. 자동화 시스템 적용")
        else:
            print("1. 실패한 테스트 원인 분석")
            print("2. 로또 사이트 UI 변경 확인")
            print("3. 코드 수정 후 재테스트")

def main():
    """메인 함수"""
    tester = LottoFunctionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 기본 기능 테스트 완료 - 자동화 준비됨!")
    else:
        print("\n🔧 문제 해결 후 다시 테스트하세요.")
    
    return success

if __name__ == "__main__":
    main()
