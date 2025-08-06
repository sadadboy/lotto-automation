# test_system.py - 시스템 테스트 스크립트
import json
import logging
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_config():
    """설정 파일 테스트"""
    logger.info("1. 설정 파일 테스트")
    try:
        with open('lotto_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 필수 설정 확인
        assert 'login' in config, "login 설정이 없습니다"
        assert 'user_id' in config['login'], "user_id가 없습니다"
        assert 'password' in config['login'], "password가 없습니다"
        
        logger.info("✅ 설정 파일 정상")
        return True
    except Exception as e:
        logger.error(f"❌ 설정 파일 오류: {e}")
        return False

def test_chrome_driver():
    """Chrome 드라이버 테스트"""
    logger.info("2. Chrome 드라이버 테스트")
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        logger.info(f"✅ Chrome 드라이버 정상 (페이지 타이틀: {title})")
        return True
    except Exception as e:
        logger.error(f"❌ Chrome 드라이버 오류: {e}")
        return False

def test_dhlottery_access():
    """동행복권 사이트 접근 테스트"""
    logger.info("3. 동행복권 사이트 접근 테스트")
    try:
        response = requests.get("https://www.dhlottery.co.kr", timeout=10)
        if response.status_code == 200:
            logger.info("✅ 동행복권 사이트 접근 가능")
            return True
        else:
            logger.error(f"❌ 동행복권 사이트 응답 코드: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ 동행복권 사이트 접근 오류: {e}")
        return False

def test_dashboard():
    """대시보드 서버 테스트"""
    logger.info("4. 대시보드 서버 테스트")
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            logger.info("✅ 대시보드 서버 정상")
            return True
        else:
            logger.info("⚠️ 대시보드 서버가 실행 중이 아닙니다")
            return False
    except:
        logger.info("⚠️ 대시보드 서버가 실행 중이 아닙니다")
        return False

def test_file_structure():
    """파일 구조 테스트"""
    logger.info("5. 파일 구조 테스트")
    import os
    
    required_files = [
        'lotto_auto_buyer.py',
        'dashboard.py',
        'lotto_config.json',
        'requirements.txt'
    ]
    
    required_dirs = [
        'templates',
        'screenshots',
        'logs'
    ]
    
    all_good = True
    
    for file in required_files:
        if os.path.exists(file):
            logger.info(f"✅ {file} 존재")
        else:
            logger.error(f"❌ {file} 없음")
            all_good = False
    
    for dir in required_dirs:
        if os.path.exists(dir):
            logger.info(f"✅ {dir}/ 디렉토리 존재")
        else:
            logger.warning(f"⚠️ {dir}/ 디렉토리 없음 - 생성 중...")
            os.makedirs(dir, exist_ok=True)
    
    return all_good

def main():
    """메인 테스트 함수"""
    logger.info("="*50)
    logger.info("로또 자동구매 시스템 테스트 시작")
    logger.info("="*50)
    
    tests = [
        test_config,
        test_chrome_driver,
        test_dhlottery_access,
        test_dashboard,
        test_file_structure
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            logger.error(f"테스트 실행 오류: {e}")
            results.append(False)
    
    logger.info("="*50)
    logger.info("테스트 결과 요약")
    logger.info(f"전체: {len(results)}개")
    logger.info(f"성공: {sum(results)}개")
    logger.info(f"실패: {len(results) - sum(results)}개")
    
    if all(results):
        logger.info("✅ 모든 테스트 통과!")
        return 0
    else:
        logger.error("❌ 일부 테스트 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())
