#!/bin/bash
# run.sh - Docker 컨테이너 실행 스크립트

# Xvfb 시작 (헤드리스 환경용)
if [ "$DOCKER_ENV" = "true" ]; then
    Xvfb :99 -screen 0 1920x1080x24 &
    export DISPLAY=:99
fi

# GUI 대시보드 시작
python dashboard.py &

# 스케줄러 실행 (옵션)
# python scheduler.py &

# 로그 확인
echo "로또 자동구매 시스템이 시작되었습니다."
echo "대시보드: http://localhost:5000"

# 프로세스 유지
tail -f /dev/null
