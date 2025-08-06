#!/usr/bin/env python3
"""
로또 사이트 현재 상태 진단 및 선택자 업데이트 스크립트
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class LottoSiteDiagnostic:
    """로또 사이트 진단 클래스"""
    
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            options = Options()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # GUI 모드로 실행 (진단을 위해)
            options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Chrome 드라이버 초기화 완료")
            return True
            
        except Exception as e:
            print(f"❌ 드라이버 초기화 실패: {e}")
            return False
    
    def analyze_login_page(self):
        """로그인 페이지 분석"""
        print("\n🔍 로그인 페이지 구조 분석 중...")
        
        try:
            # 로그인 페이지 접속
            self.driver.get("https://www.dhlottery.co.kr/user.do?method=login")
            time.sleep(3)
            
            print(f"현재 URL: {self.driver.current_url}")
            print(f"페이지 제목: {self.driver.title}")
            
            # 페이지 소스 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f'login_page_source_{timestamp}.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print(f"✅ 페이지 소스 저장: login_page_source_{timestamp}.html")
            
            # 입력 필드들 찾기
            self.find_input_fields()
            
            # 로그인 버튼 찾기
            self.find_login_buttons()
            
        except Exception as e:
            print(f"❌ 로그인 페이지 분석 실패: {e}")
    
    def find_input_fields(self):
        """입력 필드 찾기"""
        print("\n📝 입력 필드 분석:")
        
        # 모든 input 요소 찾기
        input_elements = self.driver.find_elements(By.TAG_NAME, "input")
        print(f"총 {len(input_elements)}개의 input 요소 발견")
        
        for i, element in enumerate(input_elements):
            try:
                element_id = element.get_attribute('id') or 'no-id'
                element_name = element.get_attribute('name') or 'no-name'
                element_type = element.get_attribute('type') or 'no-type'
                element_class = element.get_attribute('class') or 'no-class'
                placeholder = element.get_attribute('placeholder') or 'no-placeholder'
                
                print(f"  [{i+1}] ID: {element_id}, Name: {element_name}, Type: {element_type}")
                print(f"      Class: {element_class}")
                print(f"      Placeholder: {placeholder}")
                
                # 가능한 ID/패스워드 필드 식별
                if any(keyword in element_id.lower() for keyword in ['user', 'id', 'login']):
                    print(f"      ⭐ 가능한 ID 필드")
                elif any(keyword in element_id.lower() for keyword in ['pass', 'pw', 'password']):
                    print(f"      ⭐ 가능한 비밀번호 필드")
                elif element_type.lower() == 'password':
                    print(f"      ⭐ 비밀번호 타입 필드")
                    
                print()
                
            except Exception as e:
                print(f"  요소 {i+1} 분석 실패: {e}")
    
    def find_login_buttons(self):
        """로그인 버튼 찾기"""
        print("\n🔘 로그인 버튼 분석:")
        
        # 버튼과 submit 요소들 찾기
        button_selectors = [
            (By.TAG_NAME, "button"),
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.CSS_SELECTOR, "input[type='button']"),
            (By.CSS_SELECTOR, "a.btn"),
            (By.CSS_SELECTOR, "*[onclick*='login']")
        ]
        
        all_buttons = []
        
        for selector_type, selector in button_selectors:
            try:
                elements = self.driver.find_elements(selector_type, selector)
                for element in elements:
                    try:
                        text = element.text.strip() or element.get_attribute('value') or 'no-text'
                        element_id = element.get_attribute('id') or 'no-id'
                        element_class = element.get_attribute('class') or 'no-class'
                        onclick = element.get_attribute('onclick') or 'no-onclick'
                        
                        all_buttons.append({
                            'text': text,
                            'id': element_id,
                            'class': element_class,
                            'onclick': onclick,
                            'tag': element.tag_name
                        })
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        # 중복 제거 및 로그인 관련 버튼 식별
        unique_buttons = []
        for button in all_buttons:
            if button not in unique_buttons:
                unique_buttons.append(button)
        
        print(f"총 {len(unique_buttons)}개의 버튼/submit 요소 발견")
        
        for i, button in enumerate(unique_buttons):
            print(f"  [{i+1}] 텍스트: '{button['text']}'")
            print(f"      ID: {button['id']}, Class: {button['class']}")
            print(f"      Tag: {button['tag']}, Onclick: {button['onclick'][:50]}...")
            
            # 로그인 버튼 식별
            if any(keyword in button['text'].lower() for keyword in ['로그인', 'login', '확인']):
                print(f"      ⭐ 가능한 로그인 버튼")
            print()
    
    def test_current_selectors(self):
        """현재 사용 중인 선택자들 테스트"""
        print("\n🧪 현재 선택자 테스트:")
        
        # 기존 선택자들
        selectors_to_test = [
            ("ID 필드 (기존)", By.ID, "userId"),
            ("비밀번호 필드 (기존)", By.ID, "password"),
            ("로그인 버튼 (기존)", By.CSS_SELECTOR, "input[type='submit'][value='로그인']"),
            
            # 대안 선택자들
            ("ID 필드 (name)", By.NAME, "userId"),
            ("비밀번호 필드 (name)", By.NAME, "password"),
            ("비밀번호 필드 (type)", By.CSS_SELECTOR, "input[type='password']"),
            ("로그인 버튼 (텍스트)", By.XPATH, "//input[@value='로그인']"),
            ("로그인 버튼 (button)", By.XPATH, "//button[contains(text(), '로그인')]"),
        ]
        
        for description, by_type, selector in selectors_to_test:
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((by_type, selector))
                )
                print(f"  ✅ {description}: 찾음")
            except:
                print(f"  ❌ {description}: 못찾음")
    
    def suggest_new_selectors(self):
        """새로운 선택자 제안"""
        print("\n💡 추천 선택자:")
        
        # 페이지에서 실제로 작동할 가능성이 높은 선택자들 찾기
        print("ID 필드 후보:")
        id_candidates = [
            "userId", "user_id", "username", "loginId", "memberId"
        ]
        
        for candidate in id_candidates:
            try:
                element = self.driver.find_element(By.ID, candidate)
                print(f"  ✅ By.ID, '{candidate}' - 발견!")
            except:
                try:
                    element = self.driver.find_element(By.NAME, candidate)
                    print(f"  ✅ By.NAME, '{candidate}' - 발견!")
                except:
                    pass
        
        print("\n비밀번호 필드 후보:")
        password_candidates = [
            "password", "userPw", "passwd", "pwd", "userPassword"
        ]
        
        for candidate in password_candidates:
            try:
                element = self.driver.find_element(By.ID, candidate)
                print(f"  ✅ By.ID, '{candidate}' - 발견!")
            except:
                try:
                    element = self.driver.find_element(By.NAME, candidate)
                    print(f"  ✅ By.NAME, '{candidate}' - 발견!")
                except:
                    pass
        
        # type="password" 찾기
        try:
            password_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
            if password_inputs:
                print(f"  ✅ input[type='password'] - {len(password_inputs)}개 발견!")
                for i, element in enumerate(password_inputs):
                    element_id = element.get_attribute('id') or 'no-id'
                    element_name = element.get_attribute('name') or 'no-name'
                    print(f"     [{i+1}] ID: {element_id}, Name: {element_name}")
        except:
            pass
    
    def run_diagnosis(self):
        """전체 진단 실행"""
        print("🏥 로또 사이트 현재 상태 진단 시작")
        print("=" * 50)
        
        if not self.setup_driver():
            return
        
        try:
            self.analyze_login_page()
            self.test_current_selectors()
            self.suggest_new_selectors()
            
            print("\n" + "=" * 50)
            print("📋 진단 완료!")
            print("💡 위의 정보를 바탕으로 선택자를 업데이트하세요.")
            
            input("\n🔍 브라우저를 직접 확인하려면 Enter를 누르세요...")
            
        except Exception as e:
            print(f"❌ 진단 중 오류: {e}")
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """메인 함수"""
    diagnostic = LottoSiteDiagnostic()
    diagnostic.run_diagnosis()

if __name__ == "__main__":
    main()
