#!/usr/bin/env python3
"""
강화된 로또 기본 기능 테스트 - 다양한 선택자 지원
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

class RobustLottoTester:
    """강화된 로또 기능 테스터"""
    
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
                logging.FileHandler('robust_test_results.log', encoding='utf-8'),
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
                self.logger.info(f"  ❌ 실패: {desc} - {str(e)[:50]}")
                continue
        
        raise Exception(f"{description}를 모든 방법으로 찾을 수 없습니다.")
    
    def robust_login(self, credentials):
        """강화된 로그인 기능"""
        test_name = "강화된 로그인"
        self.logger.info(f"🧪 {test_name} 테스트 시작")
        
        try:
            user_id = credentials['user_id']
            password = credentials['password']
            
            # 로그인 페이지 접속
            self.driver.get("https://www.dhlottery.co.kr/user.do?method=login")
            time.sleep(3)
            
            # ID 입력 필드 찾기 (여러 방법 시도)
            id_selectors = [
                (By.ID, "userId", "기존 ID 선택자"),
                (By.NAME, "userId", "Name 속성"),
                (By.NAME, "user_id", "Name 속성 (언더스코어)"),
                (By.NAME, "username", "Username"),
                (By.NAME, "loginId", "LoginId"),
                (By.CSS_SELECTOR, "input[placeholder*='아이디']", "플레이스홀더 아이디"),
                (By.CSS_SELECTOR, "input[placeholder*='ID']", "플레이스홀더 ID"),
                (By.XPATH, "//input[contains(@placeholder, '아이디') or contains(@placeholder, 'ID')]", "XPath 플레이스홀더"),
                (By.CSS_SELECTOR, "input[type='text']:first-of-type", "첫 번째 텍스트 입력"),
            ]
            
            id_input = self.find_element_robust(id_selectors, "ID 입력 필드")
            id_input.clear()
            id_input.send_keys(user_id)
            self.logger.info("  ✅ ID 입력 완료")
            
            # 비밀번호 입력 필드 찾기 (여러 방법 시도)
            password_selectors = [
                (By.ID, "password", "기존 비밀번호 선택자"),
                (By.NAME, "password", "Name 속성"),
                (By.NAME, "userPw", "UserPw"),
                (By.NAME, "passwd", "Passwd"),
                (By.NAME, "pwd", "Pwd"),
                (By.CSS_SELECTOR, "input[type='password']", "비밀번호 타입"),
                (By.CSS_SELECTOR, "input[placeholder*='비밀번호']", "플레이스홀더 비밀번호"),
                (By.CSS_SELECTOR, "input[placeholder*='패스워드']", "플레이스홀더 패스워드"),
                (By.XPATH, "//input[@type='password']", "XPath 비밀번호 타입"),
                (By.XPATH, "//input[contains(@placeholder, '비밀번호') or contains(@placeholder, '패스워드')]", "XPath 플레이스홀더"),
            ]
            
            pw_input = self.find_element_robust(password_selectors, "비밀번호 입력 필드")
            pw_input.clear()
            pw_input.send_keys(password)
            self.logger.info("  ✅ 비밀번호 입력 완료")
            
            # 로그인 버튼 찾기 (여러 방법 시도)
            login_button_selectors = [
                (By.CSS_SELECTOR, "input[type='submit'][value='로그인']", "기존 로그인 버튼"),
                (By.CSS_SELECTOR, "input[value='로그인']", "Value 로그인"),
                (By.CSS_SELECTOR, "button[type='submit']", "Submit 버튼"),
                (By.XPATH, "//input[@value='로그인']", "XPath Value 로그인"),
                (By.XPATH, "//button[contains(text(), '로그인')]", "XPath 텍스트 로그인"),
                (By.XPATH, "//input[@type='submit']", "XPath Submit"),
                (By.XPATH, "//button[@type='submit']", "XPath Button Submit"),
                (By.CSS_SELECTOR, ".login-btn", "클래스 login-btn"),
                (By.CSS_SELECTOR, "#loginBtn", "ID loginBtn"),
                (By.CSS_SELECTOR, "form input[type='submit']", "폼 내 Submit"),
            ]
            
            login_btn = self.find_element_robust(login_button_selectors, "로그인 버튼")
            login_btn.click()
            self.logger.info("  ✅ 로그인 버튼 클릭 완료")
            
            # 로그인 결과 확인 (더 넓은 범위로)
            time.sleep(5)  # 로딩 시간 증가
            
            # 성공 확인 방법들
            success_indicators = [
                "마이페이지",
                "로그아웃", 
                "내정보",
                "예치금",
                "구매내역",
                "당첨조회",
                lambda: "login" not in self.driver.current_url.lower(),
                lambda: self.driver.current_url != "https://www.dhlottery.co.kr/user.do?method=login"
            ]
            
            login_success = False
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            for indicator in success_indicators:
                if callable(indicator):
                    try:
                        if indicator():
                            login_success = True
                            break
                    except:
                        continue
                else:
                    if indicator in page_source:
                        login_success = True
                        break
            
            if login_success:
                self.logger.info("  ✅ 로그인 성공 확인")
                self.test_results[test_name] = {"status": "성공", "message": f"정상 로그인 (URL: {current_url})"}
                return True
            else:
                # 실패 원인 분석
                error_selectors = [
                    (By.CSS_SELECTOR, ".error"),
                    (By.CSS_SELECTOR, ".alert"),
                    (By.CSS_SELECTOR, ".warning"),
                    (By.CSS_SELECTOR, ".message"),
                    (By.XPATH, "//*[contains(text(), '오류') or contains(text(), '실패') or contains(text(), '확인')]"),
                ]
                
                error_msg = "로그인 상태 확인 실패"
                for by_type, selector in error_selectors:
                    try:
                        error_elements = self.driver.find_elements(by_type, selector)
                        for element in error_elements:
                            text = element.text.strip()
                            if text and len(text) > 0:
                                error_msg = text
                                break
                        if error_msg != "로그인 상태 확인 실패":
                            break
                    except:
                        continue
                
                # 페이지 소스 저장 (디버깅용)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(f'login_fail_debug_{timestamp}.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                
                raise Exception(f"로그인 실패: {error_msg}")
                
        except Exception as e:
            self.logger.error(f"  ❌ {test_name} 실패: {e}")
            self.test_results[test_name] = {"status": "실패", "message": str(e)}
            return False
    
    def test_page_navigation(self):
        """페이지 네비게이션 테스트"""
        test_name = "페이지 네비게이션"
        self.logger.info(f"🧪 {test_name} 테스트 시작")
        
        try:
            # 주요 페이지들 접근 테스트
            pages_to_test = [
                ("마이페이지", "https://www.dhlottery.co.kr/myPage.do?method=myPage"),
                ("로또구매", "https://ol.dhlottery.co.kr/olotto/game/game645.do"),
                ("충전페이지", "https://www.dhlottery.co.kr/payment.do?method=payment"),
            ]
            
            accessible_pages = []
            
            for page_name, url in pages_to_test:
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    
                    # 페이지 로딩 확인
                    if "오류" not in self.driver.page_source and "error" not in self.driver.page_source.lower():
                        accessible_pages.append(page_name)
                        self.logger.info(f"  ✅ {page_name} 접근 성공")
                    else:
                        self.logger.warning(f"  ⚠️ {page_name} 접근 실패")
                        
                except Exception as e:
                    self.logger.warning(f"  ❌ {page_name} 접근 오류: {e}")
            
            if accessible_pages:
                self.test_results[test_name] = {
                    "status": "성공",
                    "message": f"접근 가능한 페이지: {', '.join(accessible_pages)}"
                }
                return True
            else:
                self.test_results[test_name] = {
                    "status": "실패",
                    "message": "모든 페이지 접근 실패"
                }
                return False
                
        except Exception as e:
            self.logger.error(f"  ❌ {test_name} 실패: {e}")
            self.test_results[test_name] = {"status": "실패", "message": str(e)}
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🔍 강화된 로또 시스템 기본 기능 테스트 시작")
        print("=" * 60)
        
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
                ("강화된 로그인", lambda: self.robust_login(credentials)),
                ("페이지 네비게이션", self.test_page_navigation),
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
            
            return passed_tests > 0  # 하나라도 성공하면 OK
            
        except Exception as e:
            self.logger.error(f"테스트 실행 중 오류: {e}")
            return False
        finally:
            if self.driver:
                input("\n🔍 브라우저를 확인하려면 Enter를 누르세요...")
                self.driver.quit()
    
    def print_test_summary(self, passed, total):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 강화된 테스트 결과 요약")
        print("=" * 60)
        
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
        
        if passed >= total * 0.5:  # 50% 이상 통과
            print("🎉 기본 기능이 어느 정도 작동합니다!")
            print("✅ 부분적으로라도 자동화 시스템 구축 가능합니다.")
        else:
            print("⚠️ 대부분의 기능에 문제가 있습니다.")
            print("🔧 사이트 변경사항을 더 자세히 분석해야 합니다.")

def main():
    """메인 함수"""
    tester = RobustLottoTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 기본 기능 확인 완료!")
    else:
        print("\n🔧 추가 분석이 필요합니다.")
    
    return success

if __name__ == "__main__":
    main()
