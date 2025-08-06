# 🎲 자동화 로또 구매 시스템

TAB + ENTER 방식을 사용한 완전 자동화 로또 구매 시스템입니다.  
Oracle Cloud에서 Docker로 완전 무인 운영이 가능합니다.

## 🚀 주요 특징

- ✅ **완전 무인 자동화**: 사용자 입력 없이 완전 자동 실행
- 🔑 **TAB + ENTER 로그인**: 안정적이고 자연스러운 로그인 방식
- 🐳 **Docker 최적화**: 컨테이너 환경에서 완벽 동작
- 🔐 **보안 강화**: 환경변수 및 Docker secrets 지원
- 📊 **실시간 모니터링**: Discord 웹훅 알림 지원
- ☁️ **클라우드 배포**: Oracle Cloud 완전 지원

## 📦 시스템 구성

```
lotto_production.py          # 🎯 메인 자동화 시스템
auto_recharge.py            # 💳 자동충전 모듈
discord_notifier.py         # 🔔 Discord 알림
credential_manager.py       # 🔐 인증정보 관리
lotto_config.json          # ⚙️ 설정 파일
docker-compose.yml          # 🐳 Docker 구성
Dockerfile                 # 🐳 컨테이너 이미지
oracle_deploy.sh           # ☁️ Oracle Cloud 배포
```

## 🛠️ 로컬 설치 및 실행

### 1단계: 저장소 클론
```bash
git clone https://github.com/YOUR_USERNAME/lotto-automation.git
cd lotto-automation
```

### 2단계: 환경변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# 인증정보 설정 (필수!)
nano .env
```

`.env` 파일 내용:
```env
LOTTO_USER_ID=your_lotto_id
LOTTO_PASSWORD=your_lotto_password
LOTTO_PURCHASE_COUNT=5
LOTTO_AUTO_RECHARGE=true
LOTTO_RECHARGE_AMOUNT=10000
LOTTO_MIN_BALANCE=5000
DISCORD_WEBHOOK_URL=your_discord_webhook_url
```

### 3단계: 의존성 설치
```bash
pip install -r requirements.txt
```

### 4단계: 실행
```bash
# 테스트 실행
python lotto_production.py --test

# 즉시 구매
python lotto_production.py --now

# 설정 확인
python lotto_production.py --config
```

## 🐳 Docker 실행

### 즉시 실행
```bash
docker-compose up --build
```

### 백그라운드 실행
```bash
docker-compose up -d --build
```

### 로그 확인
```bash
docker-compose logs -f
```

## ☁️ Oracle Cloud 배포

### 1단계: Oracle Cloud 인스턴스 생성
- Ubuntu 20.04 LTS 권장
- 최소 1GB RAM, 1 vCPU
- Docker 및 Git 설치 필요

### 2단계: 서버에서 배포
```bash
# 저장소 클론
git clone https://github.com/YOUR_USERNAME/lotto-automation.git
cd lotto-automation

# 배포 스크립트 실행
chmod +x oracle_deploy.sh
./oracle_deploy.sh
```

### 3단계: 환경변수 설정
```bash
# 환경변수 파일 생성
nano .env

# 또는 Docker secrets 사용
echo "your_lotto_id" | sudo tee /run/secrets/lotto_user_id
echo "your_lotto_password" | sudo tee /run/secrets/lotto_password
```

### 4단계: 자동 실행 시작
```bash
# 스케줄러 시작 (매주 월/목 14시)
docker-compose -f docker-compose.production.yml up -d
```

## 📅 스케줄링

시스템은 기본적으로 **매주 월요일, 목요일 14시**에 자동 실행됩니다.

스케줄 변경:
```env
CRON_SCHEDULE=0 14 * * 1,4  # 매주 월/목 14시
CRON_SCHEDULE=0 9 * * *     # 매일 9시
CRON_SCHEDULE=0 12 * * 6    # 매주 토요일 12시
```

## 🔔 알림 설정

Discord 웹훅을 통한 실시간 알림:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

알림 내용:
- 🔐 로그인 상태
- 💰 잔액 확인
- 💳 자동충전 결과
- 🎯 구매 결과
- ❌ 오류 알림

## 🛡️ 보안 주의사항

### ❌ 절대 업로드하면 안 되는 파일들
- `.env` (환경변수 파일)
- `credentials.enc` (암호화된 인증정보)
- `secrets/` (Docker secrets)
- `logs/` (로그 파일)
- `screenshots/` (스크린샷)

### ✅ 안전한 인증정보 관리
1. **환경변수 사용** (권장)
2. **Docker secrets 사용**
3. **암호화된 파일 사용**

## 📊 모니터링

### 로그 확인
```bash
# Docker 로그
docker-compose logs -f

# 파일 로그
tail -f logs/lotto_auto_buyer.log
```

### 상태 확인
```bash
# 컨테이너 상태
docker-compose ps

# 시스템 리소스
docker stats
```

## 🔧 문제 해결

### 로그인 실패
1. 인증정보 확인
2. 로또 사이트 상태 확인
3. 브라우저 업데이트

### 구매 실패
1. 잔액 확인
2. 로또 사이트 점검 시간 확인
3. 네트워크 연결 상태 확인

### Docker 문제
```bash
# 컨테이너 재시작
docker-compose restart

# 이미지 재빌드
docker-compose up --build --force-recreate
```

## 💻 개발 환경

### 요구사항
- Python 3.8+
- Chrome/Chromium
- Docker (선택사항)

### 개발 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 개발 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 테스트 실행
```bash
# 기본 기능 테스트
python test_basic_functions.py

# TAB + ENTER 테스트
python test_tab_enter_login.py

# 자동화 검증
python validate_automation.py
```

## 📈 성능 최적화

### Docker 최적화
- 멀티스테이지 빌드 사용
- 불필요한 패키지 제거
- 헤드리스 모드 활성화
- 메모리 사용량 제한

### 시스템 최적화
- 스크린샷 저장 최소화
- 로그 로테이션 설정
- 네트워크 타임아웃 조정

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## ⚠️ 면책 조항

이 소프트웨어는 교육 및 개인 사용 목적으로만 제공됩니다. 사용자는 해당 지역의 법률과 로또 사이트의 이용약관을 준수할 책임이 있습니다.

## 📞 지원

문제가 발생하면 [Issues](https://github.com/YOUR_USERNAME/lotto-automation/issues)에 문의하세요.

---

⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!
