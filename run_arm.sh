#!/bin/bash
# run_arm.sh - ARM 아키텍처용 실행 스크립트

# Xvfb 시작 (헤드리스 환경용)
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Chrome 옵션 설정
export CHROME_OPTIONS="--no-sandbox --disable-dev-shm-usage --disable-gpu"

# GUI 대시보드 시작
python dashboard.py &

# 스케줄러 실행 (설정에서 활성화된 경우)
if [ "$ENABLE_SCHEDULER" = "true" ]; then
    python scheduler.py &
fi

# 로그 확인
echo "로또 자동구매 시스템이 시작되었습니다. (ARM)"
echo "대시보드: http://localhost:5000"
echo "Chrome: $CHROME_BIN"
echo "ChromeDriver: $CHROME_DRIVER"

# 프로세스 유지
tail -f /dev/null
