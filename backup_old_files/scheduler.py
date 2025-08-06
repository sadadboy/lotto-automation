# scheduler.py - 스케줄 기반 자동 실행
import schedule
import time
import json
import subprocess
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """설정 파일 로드"""
    try:
        with open('lotto_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        return None

def run_lotto_purchase():
    """로또 구매 실행"""
    logger.info("🎲 스케줄된 로또 구매 시작...")
    
    try:
        result = subprocess.run(
            ['python', 'lotto_auto_buyer.py', '--now'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("✅ 스케줄된 구매 완료")
            logger.info(f"출력: {result.stdout}")
        else:
            logger.error(f"❌ 스케줄된 구매 실패: {result.stderr}")
            
    except Exception as e:
        logger.error(f"스케줄 실행 오류: {e}")

def setup_schedule():
    """스케줄 설정"""
    config = load_config()
    if not config:
        logger.error("설정 파일을 로드할 수 없습니다.")
        return False
    
    schedule_config = config.get('schedule', {})
    if not schedule_config.get('enabled', False):
        logger.info("스케줄이 비활성화되어 있습니다.")
        return False
    
    # 스케줄 설정
    day = schedule_config.get('day', 'friday')
    time_str = schedule_config.get('time', '14:00')
    
    # 요일별 스케줄 설정
    if day.lower() == 'monday':
        schedule.every().monday.at(time_str).do(run_lotto_purchase)
    elif day.lower() == 'tuesday':
        schedule.every().tuesday.at(time_str).do(run_lotto_purchase)
    elif day.lower() == 'wednesday':
        schedule.every().wednesday.at(time_str).do(run_lotto_purchase)
    elif day.lower() == 'thursday':
        schedule.every().thursday.at(time_str).do(run_lotto_purchase)
    elif day.lower() == 'friday':
        schedule.every().friday.at(time_str).do(run_lotto_purchase)
    elif day.lower() == 'saturday':
        schedule.every().saturday.at(time_str).do(run_lotto_purchase)
    elif day.lower() == 'sunday':
        schedule.every().sunday.at(time_str).do(run_lotto_purchase)
    elif day.lower() == 'daily':
        schedule.every().day.at(time_str).do(run_lotto_purchase)
    
    logger.info(f"✅ 스케줄 설정 완료: 매주 {day} {time_str}")
    return True

def main():
    """메인 함수"""
    logger.info("🔄 로또 자동구매 스케줄러 시작")
    
    if not setup_schedule():
        logger.error("스케줄 설정 실패")
        return
    
    # 다음 실행 시간 표시
    next_run = schedule.next_run()
    if next_run:
        logger.info(f"⏰ 다음 실행 예정: {next_run}")
    
    # 스케줄 실행
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
            
            # 매 시간마다 상태 로그
            if datetime.now().minute == 0:
                next_run = schedule.next_run()
                if next_run:
                    logger.info(f"⏰ 다음 실행 예정: {next_run}")
                    
    except KeyboardInterrupt:
        logger.info("스케줄러 종료")
    except Exception as e:
        logger.error(f"스케줄러 오류: {e}")

if __name__ == "__main__":
    main()
