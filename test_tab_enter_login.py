#!/usr/bin/env python3
"""
TAB + ENTER 방식 로그인을 사용한 강화된 테스트
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
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TabEnterLottoTester:
    """TAB + ENTER 방식 로또 테스터"""
    
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
                logging.FileHandler('tab_enter_test.log', encoding='utf-8'),
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
            options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("✅ Chrome 드라이버 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 드라이버 초기화 실패: {e}")
            return False
    
    def find_element_robust(self, selectors, description, timeout=10):
        """여러 선택자를 시도해서 요소 찾기"""
        self.logger.info(f"🔍 {description} 찾는 중...")
        
        for i, (by_type, selector, desc) in enumerate(selectors):
            try:
                self.logger.info(f"  시도 {i+1}: {desc}")
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by_type, selector))
                )
                self.logger.info(f"  ✅ 성공: {desc}")
                return element
                
            except Exception as e:
                self.logger.info(f"  ❌ 실패: {desc}")
                continue
        
        raise Exception(f"{description}를 모든 방법으로 찾을 수 없습니다.")
    
    def tab_enter_login(self, credentials):
        """TAB + ENTER 방식 로그인"""
        test_name = "TAB + ENTER 로그인"
        self.logger.info(f"🧪 {test_name} 테스트 시작")
        
        try:
            user_id = credentials['user_id']
            password = credentials['password']
            
            # 로그인 페이지 접속
            self.driver.get("https://www.dhlottery.co.kr/user.do?method=login")
            time.sleep(3)
            
            # ID 입력 필드 찾기
            id_selectors = [
                (By.ID, "userId", "기존 ID 선택자"),
                (By.NAME, "userId", "Name 속성"),
                (By.NAME, "user_id", "Name 속성 (언더스코어)"),
                (By.CSS_SELECTOR, "input[type='text']:first-of-type", "첫 번째 텍스트 입력"),
            ]
            
            id_input = self.find_element_robust(id_selectors, "ID 입력 필드", timeout=5)
            id_input.clear()
            id_input.send_keys(user_id)
            self.logger.info("  ✅ ID 입력 완료")
            
            # 비밀번호 입력 필드 찾기
            password_selectors = [
                (By.ID, "password", "기존 비밀번호 선택자"),
                (By.NAME, "password", "Name 속성"),
                (By.CSS_SELECTOR, "input[type='password']", "비밀번호 타입"),
                (By.NAME, "userPw", "UserPw"),
                (By.NAME, "passwd", "Passwd"),
            ]
            
            pw_input = self.find_element_robust(password_selectors, "비밀번호 입력 필드", timeout=5)
            pw_input.clear()
            pw_input.send_keys(password)
            self.logger.info("  ✅ 비밀번호 입력 완료")
            
            # TAB + ENTER 방식으로 로그인
            self.logger.info("  🔄 TAB 키 입력...")
            pw_input.send_keys(Keys.TAB)
            time.sleep(1)  # 포커스 이동 대기
            
            self.logger.info("  ⏎ ENTER 키 입력...")
            pw_input.send_keys(Keys.ENTER)
            
            # 또는 활성 요소에서 ENTER 시도
            try:
                active_element = self.driver.switch_to.active_element
                active_element.send_keys(Keys.ENTER)
                self.logger.info("  ⏎ 활성 요소에서 ENTER 입력")
            except:
                pass
            
            # 로그인 처리 대기
            time.sleep(5)
            
            # 로그인 성공 확인
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            success_indicators = [
                "마이페이지",
                "로그아웃", 
                "내정보",
                "예치금",
                "구매내역",
                "당첨조회",
                "welcome"
            ]
            
            login_success = False
            
            # URL 변경 확인
            if "login" not in current_url.lower() or current_url != "https://www.dhlottery.co.kr/user.do?method=login":
                login_success = True
                self.logger.info(f"  ✅ URL 변경 확인: {current_url}")
            
            # 페이지 내용 확인
            for indicator in success_indicators:
                if indicator in page_source:
                    login_success = True
                    self.logger.info(f"  ✅ 성공 지표 발견: {indicator}")
                    break
            
            if login_success:
                self.logger.info("  🎉 TAB + ENTER 로그인 성공!")
                self.test_results[test_name] = {
                    "status": "성공", 
                    "message": f"정상 로그인 (URL: {current_url})"
                }
                return True
            else:
                # 실패 원인 분석
                error_msg = "로그인 상태 확인 실패"
                
                # 오류 메시지 찾기
                error_keywords = ["오류", "실패", "확인", "error", "fail", "invalid"]
                for keyword in error_keywords:
                    if keyword in page_source.lower():
                        # 오류 메시지 추출 시도
                        try:
                            error_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                            for element in error_elements[:3]:  # 처음 3개만 확인
                                text = element.text.strip()
                                if text and len(text) < 100:  # 너무 긴 텍스트 제외
                                    error_msg = text
                                    break
                        except:
                            pass
                        break
                
                # 디버그 정보 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(f'tab_enter_debug_{timestamp}.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                
                self.logger.error(f"  ❌ TAB + ENTER 로그인 실패: {error_msg}")
                self.test_results[test_name] = {"status": "실패", "message": error_msg}
                return False
                
        except Exception as e:
            self.logger.error(f"  ❌ {test_name} 실패: {e}")
            self.test_results[test_name] = {"status": "실패", "message": str(e)}
            return False
    
    def test_balance_check_enhanced(self):
        """향상된 잔액 확인 테스트"""
        test_name = "잔액 확인"
        self.logger.info(f"🧪 {test_name} 테스트 시작")
        
        try:
            # 마이페이지로 이동
            self.driver.get("https://www.dhlottery.co.kr/myPage.do?method=myPage")
            time.sleep(3)
            
            # 다양한 방법으로 예치금 찾기
            balance_selectors = [
                (By.XPATH, "//td[contains(text(), '예치금')]/following-sibling::td[contains(text(), '원')]"),
                (By.XPATH, "//strong[contains(text(), '원') and contains(text(), ',')]"),
                (By.XPATH, "//td[@class='ta_right' and contains(text(), '원')]"),
                (By.CSS_SELECTOR, "td.ta_right"),
                (By.XPATH, "//*[contains(text(), '원') and string-length(text()) > 3 and string-length(text()) < 20]"),
                (By.CSS_SELECTOR, ".amount"),
                (By.CSS_SELECTOR, ".balance"),
                (By.CSS_SELECTOR, ".money"),
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
                            if not text:
                                continue
                                
                            self.logger.info(f"    - 요소 {j+1}: '{text}'")
                            
                            # 숫자 추출 및 검증
                            import re
                            numbers = re.findall(r'[\d,]+', text)
                            
                            for number_str in numbers:
                                clean_number = number_str.replace(',', '')
                                if clean_number.isdigit() and len(clean_number) >= 3:
                                    balance = int(clean_number)
                                    if 0 <= balance <= 50000000:  # 5천만원 이하
                                        balance_amount = balance
                                        balance_found = True
                                        self.logger.info(f"  ✅ 예치금 발견: {balance:,}원")
                                        break
                            
                            if balance_found:
                                break
                                
                        except Exception as inner_e:
                            continue
                    
                    if balance_found:
                        break
                        
                except Exception as e:
                    continue
            
            if balance_found:
                self.test_results[test_name] = {
                    "status": "성공", 
                    "message": f"예치금 {balance_amount:,}원 확인", 
                    "balance": balance_amount
                }
                return True
            else:
                # 디버깅 정보 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(f'balance_debug_{timestamp}.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                
                self.logger.warning(f"  ⚠️ 예치금을 찾을 수 없습니다. 디버그 파일: balance_debug_{timestamp}.html")
                self.test_results[test_name] = {
                    "status": "경고", 
                    "message": "예치금 요소를 찾을 수 없음"
                }
                return False
                
        except Exception as e:
            self.logger.error(f"  ❌ {test_name} 실패: {e}")
            self.test_results[test_name] = {"status": "실패", "message": str(e)}
            return False
    
    def test_purchase_page_quick(self):
        """빠른 구매 페이지 테스트"""
        test_name = "구매 페이지"
        self.logger.info(f"🧪 {test_name} 테스트 시작")
        
        try:
            # 로또 구매 페이지로 이동
            self.driver.get("https://ol.dhlottery.co.kr/olotto/game/game645.do")
            time.sleep(3)
            
            # 핵심 요소 확인
            key_elements = {
                "수량선택": ["amoundApply", "amount", "qty"],
                "확인버튼": ["btnSelectNum", "selectNum", "confirm"],
                "구매버튼": ["btnBuy", "buy", "purchase"]
            }
            
            found_elements = []
            
            for element_name, possible_ids in key_elements.items():
                element_found = False
                for possible_id in possible_ids:
                    try:
                        element = self.driver.find_element(By.ID, possible_id)
                        if element.is_displayed():
                            found_elements.append(f"{element_name}({possible_id})")
                            element_found = True
                            self.logger.info(f"  ✅ {element_name} 발견: {possible_id}")
                            break
                    except:
                        continue
                
                if not element_found:
                    self.logger.warning(f"  ❌ {element_name} 찾을 수 없음")
            
            if found_elements:
                self.test_results[test_name] = {
                    "status": "성공",
                    "message": f"구매 요소 확인: {', '.join(found_elements)}"
                }
                return True
            else:
                self.test_results[test_name] = {
                    "status": "실패",
                    "message": "구매 관련 요소를 찾을 수 없음"
                }
                return False
                
        except Exception as e:
            self.logger.error(f"  ❌ {test_name} 실패: {e}")
            self.test_results[test_name] = {"status": "실패", "message": str(e)}
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🎯 TAB + ENTER 방식 로또 테스트 시작")
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
                ("TAB + ENTER 로그인", lambda: self.tab_enter_login(credentials)),
                ("잔액 확인", self.test_balance_check_enhanced),
                ("구매 페이지", self.test_purchase_page_quick),
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                print(f"\n📋 {test_name} 테스트...")
                result = test_func()
                if result:
                    passed_tests += 1
                time.sleep(2)
            
            # 결과 출력
            self.print_test_summary(passed_tests, total_tests)
            
            return passed_tests >= 2  # 3개 중 2개 이상 성공하면 OK
            
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
        print("📊 TAB + ENTER 방식 테스트 결과")
        print("=" * 50)
        
        for test_name, result in self.test_results.items():
            status = result["status"]
            message = result["message"]
            
            if status == "성공":
                print(f"✅ {test_name}: {message}")
            elif status == "부분성공" or status == "경고":
                print(f"⚠️  {test_name}: {message}")
            else:
                print(f"❌ {test_name}: {message}")
        
        print(f"\n🎯 전체 결과: {passed}/{total} 테스트 통과")
        
        if passed >= 2:
            print("🎉 TAB + ENTER 방식으로 기본 기능 작동 확인!")
            print("✅ 이 방식으로 자동화 시스템을 구축할 수 있습니다.")
            
            # 자동화 시스템 생성 제안
            print("\n💡 다음 단계:")
            print("1. TAB + ENTER 방식을 사용한 자동화 시스템 생성")
            print("2. 실제 소액 구매 테스트")
            print("3. 도커 자동화 적용")
        else:
            print("⚠️ 일부 기능에 문제가 있습니다.")
            print("🔧 TAB + ENTER로 해결되지 않는 문제가 있습니다.")

def main():
    """메인 함수"""
    tester = TabEnterLottoTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 TAB + ENTER 방식으로 기본 기능 확인 완료!")
        print("🎯 자동화 시스템 구축 준비됨!")
    else:
        print("\n🔧 추가 문제 해결이 필요합니다.")
    
    return success

if __name__ == "__main__":
    main()
