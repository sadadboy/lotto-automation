# 🐳 로또 자동구매 Docker 자동화 가이드

## 📋 자동화 모드 사용법

### 1. 환경변수 방식 (권장)
```bash
# 환경변수 설정
export LOTTO_MASTER_PASSWORD="your_master_password_here"

# 헤드리스 모드로 실행
python lotto_auto_buyer_integrated.py --now --headless
```

### 2. CLI 옵션 방식
```bash
python lotto_auto_buyer_integrated.py --now --master-password "your_password" --headless
```

### 3. Docker 방식

#### 🔧 환경변수로 실행
```bash
docker run -d \
  --name lotto-auto-buyer \
  -e LOTTO_MASTER_PASSWORD="your_master_password" \
  -v $(pwd)/credentials.enc:/app/credentials.enc \
  -v $(pwd)/lotto_config.json:/app/lotto_config.json \
  lotto-auto-buyer:latest
```

#### 🔐 Docker Secrets 방식 (더 안전)
```bash
# 시크릿 생성
echo "your_master_password" | docker secret create master_password -

# 실행
docker service create \
  --name lotto-auto-buyer \
  --secret master_password \
  --mount type=bind,source=$(pwd)/credentials.enc,target=/app/credentials.enc \
  --mount type=bind,source=$(pwd)/lotto_config.json,target=/app/lotto_config.json \
  lotto-auto-buyer:latest
```

## 🏗️ Docker 빌드

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Chrome 설치를 위한 패키지 업데이트
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver 설치
RUN CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 헤드리스 모드 기본 설정
ENV DISPLAY=:99
ENV LOTTO_HEADLESS=true

# 실행
CMD ["python", "lotto_auto_buyer_integrated.py", "--now", "--headless"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  lotto-auto-buyer:
    build: .
    container_name: lotto-auto-buyer
    environment:
      - LOTTO_MASTER_PASSWORD=${LOTTO_MASTER_PASSWORD}
      - TZ=Asia/Seoul
    volumes:
      - ./credentials.enc:/app/credentials.enc:ro
      - ./lotto_config.json:/app/lotto_config.json:ro
      - ./logs:/app/logs
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # 스케줄러 (크론잡 대안)
  lotto-scheduler:
    build: .
    container_name: lotto-scheduler
    environment:
      - LOTTO_MASTER_PASSWORD=${LOTTO_MASTER_PASSWORD}
      - TZ=Asia/Seoul
    volumes:
      - ./credentials.enc:/app/credentials.enc:ro
      - ./lotto_config.json:/app/lotto_config.json:ro
      - ./logs:/app/logs
    command: >
      sh -c "
        # 매주 월, 목요일 오후 2시에 실행
        echo '0 14 * * 1,4 cd /app && python lotto_auto_buyer_integrated.py --now --headless' | crontab -
        crond -f
      "
    restart: unless-stopped
```

## 🌩️ 오라클 클라우드 배포

### 1. 인스턴스 설정
```bash
# Docker 설치
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### 2. 프로젝트 배포
```bash
# 프로젝트 복사
scp -r lotto_auto_complete/ oracle_user@your-instance-ip:~/

# 환경변수 파일 생성
echo "LOTTO_MASTER_PASSWORD=your_password_here" > .env

# 빌드 및 실행
docker-compose --env-file .env up -d
```

### 3. 크론잡 설정 (시스템 레벨)
```bash
# 크론 편집
crontab -e

# 매주 월, 목요일 오후 2시에 실행
0 14 * * 1,4 cd /home/ubuntu/lotto_auto_complete && docker-compose run --rm lotto-auto-buyer
```

## 📊 모니터링

### 로그 확인
```bash
# 실시간 로그
docker-compose logs -f lotto-auto-buyer

# 특정 컨테이너 로그
docker logs lotto-auto-buyer
```

### Discord 알림 확인
- 모든 실행 단계가 Discord로 실시간 알림
- 성공/실패 여부 즉시 확인 가능

## 🔒 보안 고려사항

1. **환경변수 암호화**: `.env` 파일 권한을 600으로 설정
2. **Docker Secrets 사용**: 프로덕션에서는 Docker Secrets 권장
3. **방화벽 설정**: 필요한 포트만 열기
4. **정기 업데이트**: 의존성 및 Chrome 버전 주기적 업데이트

## ⚡ 자동화 스케줄 예시

```bash
# 매주 월, 목요일 오후 2시 (로또 마감 1시간 전)
0 14 * * 1,4 /path/to/run-lotto.sh

# 매일 오전 9시 잔액 확인만
0 9 * * * python lotto_auto_buyer_integrated.py --check-balance-only
```

---

**🎯 이제 완전 자동화된 로또 구매 시스템이 준비되었습니다!**
- ✅ 인터랙티브 입력 없음
- ✅ 환경변수/Docker Secrets 지원  
- ✅ 헤드리스 모드 지원
- ✅ Discord 실시간 알림
- ✅ 오라클 클라우드 배포 준비 완료
