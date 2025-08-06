#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# auto_recharge.py - 실제 간편충전 동작에 맞는 자동충전 모듈

import time
import logging
import io
import base64
from datetime import datetime
from PIL import Image, ImageEnhance
import pytesseract
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class AutoRecharger:
    def __init__(self, config):
        self.config = config
        self.setup_logging()
        self.setup_ocr()
        
    def setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger('AutoRecharger')
        
    def setup_ocr(self):
        """OCR 설정"""
        try:
            # pytesseract 경로 설정 (Windows)
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            self.ocr_available = True
            self.logger.info("✅ OCR 엔진 초기화 성공")
        except:
            self.ocr_available = False
            self.logger.warning("⚠️ OCR 엔진을 찾을 수 없습니다 (수동 입력 사용)")
    
    def auto_recharge(self, driver, current_balance):
        """자동충전 메인 로직"""
        try:
            payment_config = self.config.get('payment', {})
            
            # 최소 잔액 확인
            min_balance = payment_config.get('min_balance', 30000)
            if current_balance >= min_balance:
                self.logger.info(f"💰 충전 불필요 (현재: {current_balance:,}원)")
                return True
            
            # 자동충전 활성화 확인
            if not payment_config.get('auto_recharge', False):
                self.logger.warning("⚠️ 자동충전이 비활성화되어 있습니다")
                return False
            
            # 충전 금액 결정
            recharge_amount = payment_config.get('recharge_amount', 10000)
            
            self.logger.info(f"💳 자동충전 시작")
            self.logger.info(f"  - 현재 잔액: {current_balance:,}원")
            self.logger.info(f"  - 충전 금액: {recharge_amount:,}원")
            
            # 간편 충전 시도
            self.logger.info("💳 간편 충전(케이뱅크) 시도 중...")
            return self.recharge_with_easy_charge(driver, recharge_amount, current_balance)
                
        except Exception as e:
            self.logger.error(f"자동충전 실패: {e}")
            return False
    
    def recharge_with_easy_charge(self, driver, amount, before_balance):
        """실제 간편 충전 로직 (Alert 처리 중심)"""
        try:
            self.logger.info(f"💳 간편 충전 시작: {amount:,}원")
            
            # 충전 페이지로 이동
            driver.get("https://www.dhlottery.co.kr/payment.do?method=payment")
            time.sleep(3)
            
            # 간편충전 탭이 기본 선택되어 있는지 확인
            try:
                # 간편 충전 금액 선택
                amount_select = driver.find_element(By.ID, "EcAmt")
                current_amount = int(amount_select.get_attribute("value"))
                
                if current_amount != amount:
                    self.logger.info(f"💰 충전 금액 변경: {current_amount:,}원 → {amount:,}원")
                    from selenium.webdriver.support.ui import Select
                    select = Select(amount_select)
                    select.select_by_value(str(amount))
                else:
                    self.logger.info(f"💰 충전 금액 확인: {amount:,}원")
                    
            except Exception as e:
                self.logger.warning(f"금액 설정 실패, 기본값 사용: {e}")
            
            # 충전하기 버튼 클릭
            try:
                charge_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn_common.mid.blu[onclick='goEasyChargePC()']"))
                )
                charge_btn.click()
                self.logger.info("✅ 충전하기 버튼 클릭")
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"충전 버튼 클릭 실패: {e}")
                return False
            
            # 팝업 창으로 전환
            main_window = driver.current_window_handle
            all_windows = driver.window_handles
            
            popup_window = None
            for window in all_windows:
                if window != main_window:
                    popup_window = window
                    break
            
            if popup_window:
                driver.switch_to.window(popup_window)
                self.logger.info("✅ 팝업 창으로 전환")
                time.sleep(2)
            else:
                self.logger.warning("⚠️ 팝업 창을 찾을 수 없음")
                return False
            
            # 가상 키패드에서 비밀번호 입력 및 Alert 처리
            password = "128500"
            success = self.input_keypad_password(driver, password)
            
            # 메인 창으로 복귀
            try:
                driver.switch_to.window(main_window)
                self.logger.info("✅ 메인 창으로 복귀")
            except:
                pass
            
            if success:
                self.logger.info("✅ 간편 충전 성공!")
                return True
            else:
                self.logger.error("❌ 간편 충전 실패")
                return False
                
        except Exception as e:
            self.logger.error(f"간편 충전 오류: {e}")
            return False
    
    def input_keypad_password(self, driver, password):
        """가상 키패드 비밀번호 입력 (OCR 또는 수동) + Alert 처리"""
        try:
            self.logger.info(f"🔢 가상 키패드 비밀번호 입력: {'*' * len(password)}")
            
            # 키패드 대기
            keypad_container = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#nppfs-keypad-ecpassword, .nppfs-keypad, .kpd-wrap"))
            )
            time.sleep(2)
            
            # 키패드 버튼들 찾기
            keypad_buttons = driver.find_elements(By.CSS_SELECTOR, ".kpd-data[data-action*='data:']")
            
            if not keypad_buttons:
                self.logger.error("❌ 키패드 버튼을 찾을 수 없습니다")
                return False
            
            self.logger.info(f"🔢 키패드 버튼 {len(keypad_buttons)}개 발견")
            
            # 비밀번호 입력 시도
            input_success = False
            
            # OCR 사용 가능한 경우 자동 입력 시도
            if self.ocr_available:
                input_success = self.auto_input_with_ocr(driver, keypad_buttons, password)
            
            # OCR 실패시 또는 OCR 불가능시 수동 입력
            if not input_success:
                input_success = self.manual_input_fallback(driver, password)
            
            if input_success:
                # 비밀번호 입력 후 Alert 대기 및 분석
                return self.handle_charge_alert(driver)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"키패드 입력 오류: {e}")
            return False
    
    def handle_charge_alert(self, driver):
        """충전 결과 Alert 처리 및 분석"""
        try:
            self.logger.info("⏱️ 충전 결과 Alert 대기 중...")
            
            # Alert 대기 (최대 15초)
            start_time = time.time()
            while time.time() - start_time < 15:
                try:
                    # Alert 체크
                    alert = WebDriverWait(driver, 1).until(EC.alert_is_present())
                    alert_text = alert.text
                    self.logger.info(f"📢 Alert 감지: {alert_text}")
                    
                    # Alert 내용 분석
                    success = self.analyze_charge_alert(alert_text)
                    
                    # Alert 닫기
                    alert.accept()
                    self.logger.info("✅ Alert 닫기 완료")
                    
                    # 충전 성공 여부 반환
                    if success:
                        self.logger.info("✅ Alert 분석 결과: 충전 성공!")
                        time.sleep(2)  # 처리 완료 대기
                        return True
                    else:
                        self.logger.error("❌ Alert 분석 결과: 충전 실패")
                        return False
                    
                except TimeoutException:
                    # Alert이 아직 나타나지 않음
                    time.sleep(0.5)
                    continue
                except Exception as e:
                    self.logger.debug(f"Alert 체크 중 오류: {e}")
                    time.sleep(0.5)
                    continue
            
            # Alert 대기 시간 초과
            self.logger.warning("⚠️ Alert 대기 시간 초과 - 다른 방법으로 확인")
            return self.fallback_popup_close_check(driver)
            
        except Exception as e:
            self.logger.error(f"Alert 처리 오류: {e}")
            return self.fallback_popup_close_check(driver)
    
    def analyze_charge_alert(self, alert_text):
        """충전 Alert 내용 분석"""
        try:
            self.logger.info(f"🔍 Alert 내용 분석: '{alert_text}'")
            
            # 성공 지표 키워드
            success_keywords = [
                "성공", "success", "완료", "complete", "처리가 완료", 
                "충전되었습니다", "충전이 완료", "결제완료",
                "정상적으로", "정상처리", "OK", "확인"
            ]
            
            # 실패 지표 키워드
            failure_keywords = [
                "실패", "fail", "error", "오류", "비밀번호", "잘못",
                "취소", "cancel", "처리에 실패", "인증실패",
                "시간초과", "만료", "차단", "불가능"
            ]
            
            alert_lower = alert_text.lower()
            
            # 실패 키워드 먼저 체크 (우선순위 높음)
            for keyword in failure_keywords:
                if keyword in alert_text or keyword.lower() in alert_lower:
                    self.logger.warning(f"❌ 실패 키워드 발견: '{keyword}'")
                    return False
            
            # 성공 키워드 체크
            for keyword in success_keywords:
                if keyword in alert_text or keyword.lower() in alert_lower:
                    self.logger.info(f"✅ 성공 키워드 발견: '{keyword}'")
                    return True
            
            # 키워드가 없으면 기본적으로 성공으로 간주 (일반적으로 성공시 단순 메시지)
            self.logger.info("🤔 특정 키워드 없음 - 기본 성공으로 간주")
            return True
            
        except Exception as e:
            self.logger.error(f"Alert 분석 오류: {e}")
            return False
    
    def fallback_popup_close_check(self, driver):
        """팝업 닫힘 체크로 fallback 확인"""
        try:
            self.logger.info("🔄 팝업 닫힘 체크로 충전 성공 여부 확인...")
            
            # 팝업창이 닫힐 때까지 대기 (최대 10초)
            start_time = time.time()
            while time.time() - start_time < 10:
                try:
                    current_windows = driver.window_handles
                    if len(current_windows) == 1:  # 팝업창이 닫힘
                        self.logger.info("✅ 팝업창이 닫혔습니다 - 충전 성공으로 간주")
                        return True
                    time.sleep(0.5)
                except:
                    time.sleep(0.5)
                    continue
            
            self.logger.warning("⚠️ 팝업창이 닫히지 않음 - 충전 실패 가능성")
            return False
            
        except Exception as e:
            self.logger.error(f"팝업 닫힘 체크 오류: {e}")
            return False
    
    def auto_input_with_ocr(self, driver, keypad_buttons, password):
        """OCR을 사용한 자동 키패드 입력"""
        try:
            self.logger.info("🔍 OCR로 키패드 숫자 인식 중...")
            
            # 각 버튼의 숫자를 OCR로 인식
            button_map = {}  # {숫자: 버튼_요소}
            
            for i, button in enumerate(keypad_buttons):
                try:
                    # 버튼 위치와 크기 가져오기
                    location = button.location
                    size = button.size
                    
                    # 버튼 영역 스크린샷
                    driver.save_screenshot(f"temp_keypad_{i}.png")
                    
                    # 이미지 로드 후 버튼 영역 추출
                    full_image = Image.open(f"temp_keypad_{i}.png")
                    
                    # 버튼 영역 좌표 계산
                    left = location['x']
                    top = location['y'] 
                    right = left + size['width']
                    bottom = top + size['height']
                    
                    # 버튼 영역 크롭
                    button_image = full_image.crop((left, top, right, bottom))
                    
                    # 이미지 전처리 (OCR 정확도 향상)
                    button_image = button_image.convert('L')  # 그레이스케일
                    enhancer = ImageEnhance.Contrast(button_image)
                    button_image = enhancer.enhance(2.0)  # 대비 증가
                    
                    # OCR로 숫자 인식
                    text = pytesseract.image_to_string(
                        button_image, 
                        config='--psm 10 -c tessedit_char_whitelist=0123456789'
                    ).strip()
                    
                    if text.isdigit() and len(text) == 1:
                        button_map[text] = button
                        self.logger.debug(f"🔍 버튼 {i}: '{text}' 인식")
                    
                    # 임시 파일 삭제
                    import os
                    try:
                        os.remove(f"temp_keypad_{i}.png")
                    except:
                        pass
                        
                except Exception as e:
                    self.logger.debug(f"버튼 {i} OCR 실패: {e}")
                    continue
            
            self.logger.info(f"🔍 OCR 인식 완료: {len(button_map)}개 숫자 발견")
            
            # 비밀번호 입력
            if len(button_map) >= 6:  # 최소 6개 숫자 필요
                for digit in password:
                    if digit in button_map:
                        try:
                            button_map[digit].click()
                            self.logger.info(f"✅ 숫자 '{digit}' 클릭")
                            time.sleep(0.5)
                        except Exception as e:
                            self.logger.error(f"❌ 숫자 '{digit}' 클릭 실패: {e}")
                            return False
                    else:
                        self.logger.error(f"❌ 숫자 '{digit}'를 찾을 수 없습니다")
                        return False
                
                # 6자리 입력 완료
                self.logger.info("✅ 6자리 비밀번호 입력 완료")
                time.sleep(1)  # 입력 처리 대기
                return True
                
            else:
                self.logger.warning("⚠️ OCR 인식 불충분")
                return False
                
        except Exception as e:
            self.logger.error(f"OCR 자동 입력 실패: {e}")
            return False
    
    def manual_input_fallback(self, driver, password):
        """수동 입력 fallback (입력만 담당)"""
        try:
            self.logger.info("📷 키패드 스크린샷 저장 중...")
            
            # 디버그용 스크린샷
            try:
                screenshot_path = f"keypad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                driver.save_screenshot(screenshot_path)
                self.logger.info(f"📷 키패드 스크린샷: {screenshot_path}")
            except:
                pass
            
            # 사용자에게 수동 입력 요청
            self.logger.info("🔢 가상 키패드에 수동으로 비밀번호를 입력해주세요")
            self.logger.info(f"📝 입력할 비밀번호: {password}")
            self.logger.info("⏱️ 15초 내에 수동으로 6자리를 입력해주세요...")
            
            # 15초 대기
            time.sleep(15)
            
            # 입력 완료로 간주
            self.logger.info("✅ 수동 입력 완료로 간주")
            return True
                
        except Exception as e:
            self.logger.error(f"수동 입력 처리 오류: {e}")
            return False
    

    def recharge_with_account(self, driver, amount):
        """계좌이체로 충전 (미구현)"""
        self.logger.warning("⚠️ 계좌이체 충전은 미구현")
        return False
    
    def recharge_with_card(self, driver, amount):
        """신용카드로 충전 (미구현)"""
        self.logger.warning("⚠️ 신용카드 충전은 미구현")
        return False
    
    def check_recharge_complete(self, driver):
        """충전 완료 확인 (기본)"""
        try:
            page_source = driver.page_source
            complete_indicators = ["충전완료", "충전성공", "complete", "success"]
            
            for indicator in complete_indicators:
                if indicator in page_source:
                    return True
            return False
            
        except:
            return False

def test_auto_recharge():
    """자동충전 테스트"""
    config = {
        'payment': {
            'auto_recharge': True,
            'recharge_amount': 10000,
            'min_balance': 30000,
            'recharge_method': 'easy_charge'
        }
    }
    
    recharger = AutoRecharger(config)
    print("자동충전 모듈 테스트")
    print(f"설정: {config['payment']}")
    print(f"OCR 사용 가능: {recharger.ocr_available}")

if __name__ == "__main__":
    test_auto_recharge()
