# auto_recharge.py - 자동충전 모듈
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class AutoRecharger:
    def __init__(self, config):
        self.config = config
        self.setup_logging()
        
    def setup_logging(self):
        """로깅 설정"""
        self.logger = logging.getLogger('AutoRecharger')
        
    def recharge_with_account(self, driver, amount):
        """계좌이체로 충전"""
        try:
            self.logger.info(f"💳 계좌이체 충전 시작: {amount:,}원")
            
            # 충전 페이지로 이동
            driver.get("https://www.dhlottery.co.kr/payment.do?method=payment")
            time.sleep(3)
            
            # 충전 방법 선택 - 계좌이체
            try:
                # 계좌이체 라디오 버튼 클릭
                account_radio = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "radio_account_transfer"))
                )
                driver.execute_script("arguments[0].click();", account_radio)
                self.logger.info("✅ 계좌이체 선택")
                time.sleep(1)
            except:
                self.logger.warning("계좌이체 옵션을 찾을 수 없습니다")
            
            # 충전 금액 입력
            try:
                amount_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "recharge_amount"))
                )
                amount_input.clear()
                amount_input.send_keys(str(amount))
                self.logger.info(f"✅ 충전 금액 입력: {amount:,}원")
                time.sleep(1)
            except:
                # 금액 선택 버튼 방식일 수도 있음
                self.select_amount_button(driver, amount)
            
            # 충전하기 버튼 클릭
            try:
                recharge_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnRecharge"))
                )
                driver.execute_script("arguments[0].click();", recharge_btn)
                self.logger.info("✅ 충전하기 버튼 클릭")
                time.sleep(3)
                
                # 계좌이체 인증 페이지 대기
                self.logger.info("⏳ 계좌이체 인증 대기중...")
                self.logger.info("💡 수동으로 계좌이체 인증을 완료해주세요")
                
                # 인증 완료 대기 (최대 3분)
                for i in range(180):
                    if self.check_recharge_complete(driver):
                        self.logger.info("✅ 충전 완료!")
                        return True
                    time.sleep(1)
                    
                    if i % 10 == 0:
                        self.logger.info(f"⏳ 대기중... ({i}초)")
                
                self.logger.warning("⚠️ 충전 시간 초과")
                return False
                
            except Exception as e:
                self.logger.error(f"충전 버튼 클릭 실패: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"계좌이체 충전 실패: {e}")
            return False
    
    def recharge_with_card(self, driver, amount):
        """신용카드로 충전"""
        try:
            self.logger.info(f"💳 신용카드 충전 시작: {amount:,}원")
            
            # 충전 페이지로 이동
            driver.get("https://www.dhlottery.co.kr/payment.do?method=payment")
            time.sleep(3)
            
            # 신용카드 선택
            try:
                card_radio = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "radio_credit_card"))
                )
                driver.execute_script("arguments[0].click();", card_radio)
                self.logger.info("✅ 신용카드 선택")
                time.sleep(1)
            except:
                self.logger.warning("신용카드 옵션을 찾을 수 없습니다")
            
            # 금액 입력 및 충전 진행
            # ... (계좌이체와 유사한 로직)
            
            self.logger.warning("⚠️ 신용카드 충전은 아직 구현 중입니다")
            return False
            
        except Exception as e:
            self.logger.error(f"신용카드 충전 실패: {e}")
            return False
    
    def select_amount_button(self, driver, amount):
        """금액 버튼 선택 방식"""
        try:
            # 일반적인 충전 금액 버튼들
            amount_buttons = {
                10000: "1만원",
                30000: "3만원", 
                50000: "5만원",
                100000: "10만원"
            }
            
            if amount in amount_buttons:
                button_text = amount_buttons[amount]
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if button_text in btn.text:
                        driver.execute_script("arguments[0].click();", btn)
                        self.logger.info(f"✅ {button_text} 버튼 클릭")
                        return True
                        
            # 직접 입력 필요
            self.logger.info("버튼에 없는 금액 - 직접 입력 시도")
            return False
            
        except Exception as e:
            self.logger.error(f"금액 버튼 선택 실패: {e}")
            return False
    
    def check_recharge_complete(self, driver):
        """충전 완료 확인"""
        try:
            # URL 변경 확인
            current_url = driver.current_url
            if "complete" in current_url or "success" in current_url:
                return True
                
            # 완료 메시지 확인
            page_source = driver.page_source
            if "충전이 완료되었습니다" in page_source or "충전완료" in page_source:
                return True
                
            # 마이페이지로 리다이렉트 확인
            if "myPage" in current_url:
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"충전 완료 확인 실패: {e}")
            return False
    
    def auto_recharge(self, driver, current_balance):
        """자동충전 메인 함수"""
        try:
            payment_config = self.config.get('payment', {})
            
            # 충전 필요 여부 확인
            min_balance = payment_config.get('min_balance', 5000)
            if current_balance >= min_balance:
                self.logger.info(f"💰 충전 불필요 (현재: {current_balance:,}원)")
                return True
            
            # 자동충전 활성화 확인
            if not payment_config.get('auto_recharge', False):
                self.logger.warning("⚠️ 자동충전이 비활성화되어 있습니다")
                return False
            
            # 충전 금액 결정
            recharge_amount = payment_config.get('recharge_amount', 50000)
            recharge_method = payment_config.get('recharge_method', 'account_transfer')
            
            self.logger.info(f"💳 자동충전 시작")
            self.logger.info(f"  - 현재 잔액: {current_balance:,}원")
            self.logger.info(f"  - 충전 금액: {recharge_amount:,}원")
            self.logger.info(f"  - 충전 방법: {recharge_method}")
            
            # 충전 방법에 따른 처리
            if recharge_method == 'account_transfer':
                return self.recharge_with_account(driver, recharge_amount)
            elif recharge_method == 'credit_card':
                return self.recharge_with_card(driver, recharge_amount)
            else:
                self.logger.error(f"지원하지 않는 충전 방법: {recharge_method}")
                return False
                
        except Exception as e:
            self.logger.error(f"자동충전 실패: {e}")
            return False

def test_auto_recharge():
    """자동충전 테스트"""
    config = {
        'payment': {
            'auto_recharge': True,
            'recharge_amount': 50000,
            'min_balance': 5000,
            'recharge_method': 'account_transfer'
        }
    }
    
    recharger = AutoRecharger(config)
    print("자동충전 모듈 테스트")
    print(f"설정: {config['payment']}")

if __name__ == "__main__":
    test_auto_recharge()
