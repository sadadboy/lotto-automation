FROM python:3.11-slim

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99 \
    LOTTO_HEADLESS=true

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    xauth \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver 자동 설치 (webdriver-manager 사용)
RUN pip install webdriver-manager

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p /app/logs

# 크론잡을 위한 스크립트 생성
RUN echo '#!/bin/bash\n\
cd /app\n\
export LOTTO_MASTER_PASSWORD="${LOTTO_MASTER_PASSWORD}"\n\
python lotto_auto_buyer_integrated.py --now --headless >> /app/logs/cron.log 2>&1\n\
' > /app/run-lotto.sh && chmod +x /app/run-lotto.sh

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 기본 실행 명령어
CMD ["python", "lotto_auto_buyer_integrated.py", "--now", "--headless"]
