# 🎲 완전 자동화 로또 구매 시스템 가이드

## 🎯 개요

이 시스템은 **사용자 입력 없이 완전 자동화**된 로또 구매를 제공합니다. 도커 환경에서 실행되며, 환경변수만 설정하면 별도의 상호작용 없이 로또를 자동으로 구매합니다.

## ✨ 주요 특징

- ✅ **완전 자동화**: 사용자 입력 없이 실행
- 🐳 **도커 최적화**: 컨테이너 환경에서 안정적 실행
- 🔐 **보안 강화**: Docker secrets 지원
- 📊 **모니터링**: 웹 대시보드 제공
- 🔔 **알림 지원**: Discord 웹훅 알림
- 📅 **스케줄 실행**: 크론 기반 자동 스케줄링
- 🛡️ **에러 처리**: 강건한 예외 처리

## 🚀 빠른 시작

### 1단계: 환경 설정

```bash
# 저장소 클론 (또는 파일 다운로드)
cd lotto_auto_complete

# 환경변수 파일 복사
cp .env.automated .env

# 환경변수 편집 (필수!)
nano .env  # 또는 메모장으로 편집
```

**`.env` 파일에서 반드시 설정해야 할 항목:**
```env
LOTTO_USER_ID=실제_로또_아이디
LOTTO_PASSWORD=실제_로또_비밀번호
```

### 2단계: 검증

시스템이 올바르게 설정되었는지 확인:

```bash
python validate_automation.py
```

### 3단계: 실행

#### 즉시 구매 (한 번만 실행)
```bash
# Linux/Mac
./run_automated.sh now

# Windows
run_automated.bat now
```

#### 자동 스케줄 실행 (매주 월/목 14시)
```bash
# Linux/Mac
./run_automated.sh schedule

# Windows  
run_automated.bat schedule
```

#### 모니터링과 함께 실행
```bash
# Linux/Mac
./run_automated.sh monitor

# Windows
run_automated.bat monitor
```

## 📋 상세 설정

### 환경변수 설정

`.env` 파일에서 설정 가능한 모든 옵션:

```env
# 🔐 필수 인증정보
LOTTO_USER_ID=your_id
LOTTO_PASSWORD=your_password

# 🎯 구매 설정
LOTTO_PURCHASE_COUNT=5              # 구매할 게임 수
LOTTO_AUTO_RECHARGE=true            # 자동충전 사용
LOTTO_RECHARGE_AMOUNT=10000         # 충전 금액
LOTTO_MIN_BALANCE=5000              # 최소 잔액

# 🖥️ 시스템 옵션
LOTTO_HEADLESS=true                 # 헤드리스 모드
LOTTO_SCREENSHOT=true               # 스크린샷 저장
LOTTO_DEBUG=false                   # 디버그 모드

# 📅 스케줄 설정
CRON_SCHEDULE=0 14 * * 1,4          # 크론 스케줄

# 🔔 Discord 알림
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### 구매 설정 커스터마이징

`lotto_config.json` 파일에서 상세 구매 설정:

```json
{
  "purchase": {
    "count": 5,
    "lotto_list": [
      {"type": "자동", "numbers": []},
      {"type": "반자동", "numbers": [6, 11, 18]},
      {"type": "수동(랜덤)", "numbers": []},
      {"type": "수동(AI추천)", "numbers": []},
      {"type": "수동(통계분석)", "numbers": []}
    ]
  }
}
```

## 🐳 도커 실행 방법

### 직접 실행
```bash
# 즉시 구매
docker-compose -f docker-compose.automated.yml --profile immediate up --build

# 백그라운드 스케줄러
docker-compose -f docker-compose.automated.yml --profile scheduler up -d --build

# 모니터링 포함
docker-compose -f docker-compose.automated.yml --profile scheduler --profile monitor up -d --build
```

### Docker Secrets 사용 (권장)
```bash
# secrets 디렉토리 생성
mkdir -p secrets

# 인증정보 파일 생성
echo "your_user_id" > secrets/lotto_user_id.txt
echo "your_password" > secrets/lotto_password.txt
chmod 600 secrets/*

# 실행
docker-compose -f docker-compose.automated.yml --profile scheduler up -d
```

## 📊 모니터링

### 웹 대시보드
모니터링 서비스 실행 시 웹 대시보드 접근:
```
http://localhost:8080
```

### 로그 확인
```bash
# 실시간 로그
docker-compose -f docker-compose.automated.yml logs -f

# 저장된 로그
./run_automated.sh logs    # Linux/Mac
run_automated.bat logs     # Windows
```

### 상태 확인
```bash
./run_automated.sh status    # Linux/Mac
run_automated.bat status     # Windows
```

## 🛡️ 보안 고려사항

### 1. 인증정보 보호
- 환경변수나 Docker secrets 사용
- `.env` 파일을 Git에 커밋하지 마세요
- 컨테이너에서 최소 권한 사용자로 실행

### 2. 네트워크 보안
- 필요한 포트만 노출
- VPN 환경에서 실행 권장

### 3. 로그 관리
- 로그 파일에 민감정보 포함되지 않도록 주의
- 정기적인 로그 로테이션

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. 인증 실패
```
❌ 로그인 실패
```
**해결:** `.env` 파일의 `LOTTO_USER_ID`와 `LOTTO_PASSWORD` 확인

#### 2. 도커 권한 오류
```
❌ Permission denied
```
**해결:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

#### 3. 포트 충돌
```
❌ Port already in use
```
**해결:** `.env`에서 `MONITOR_PORT` 변경

#### 4. 메모리 부족
```
❌ Out of memory
```
**해결:** 
- 다른 애플리케이션 종료
- Docker Desktop에서 메모리 할당량 증가

### 디버그 모드
상세한 로그를 보려면:
```env
LOTTO_DEBUG=true
```

### 테스트 모드
실제 구매 없이 테스트:
```bash
./run_automated.sh test
```

## 📅 운영 가이드

### 일반적인 운영 시나리오

#### 1. 개발/테스트 환경
```bash
# 즉시 실행으로 테스트
./run_automated.sh now
```

#### 2. 프로덕션 환경
```bash
# 스케줄러 백그라운드 실행
./run_automated.sh schedule

# 상태 모니터링
./run_automated.sh status
```

#### 3. 클라우드 배포
```bash
# Docker Compose로 전체 스택 배포
docker-compose -f docker-compose.automated.yml --profile scheduler --profile monitor up -d
```

### 정기 유지보수

#### 주간 점검
- 로그 확인: `./run_automated.sh logs`
- 상태 확인: `./run_automated.sh status`
- 스크린샷 검토

#### 월간 정리
- 오래된 로그 삭제
- 스크린샷 정리
- 시스템 업데이트

```bash
# 시스템 정리
./run_automated.sh clean
```

## 🆘 지원

### 로그 수집
문제 발생 시 다음 정보를 수집:

1. **시스템 정보**
   ```bash
   python validate_automation.py > validation_report.txt
   ```

2. **로그 파일**
   - `data/logs/lotto_auto_buyer.log`
   - `data/logs/cron.log`

3. **설정 파일**
   - `.env` (민감정보 제거 후)
   - `lotto_config.json`

### 문제 신고
다음 정보와 함께 문제를 신고하세요:
- 실행 환경 (OS, Docker 버전)
- 오류 메시지
- 재현 단계
- 로그 파일

## 📝 변경 이력

### v2.0.0 (완전 자동화 버전)
- ✅ 사용자 입력 완전 제거
- 🐳 도커 최적화
- 🔐 보안 강화
- 📊 모니터링 추가

### v1.x (기존 버전)
- 기본 로또 구매 기능
- 수동 설정 필요

---

## 🎉 마무리

이제 완전 자동화된 로또 구매 시스템을 사용할 수 있습니다!

**핵심 명령어 요약:**
```bash
# 설정 확인
python validate_automation.py

# 즉시 구매
./run_automated.sh now

# 자동 스케줄 시작
./run_automated.sh schedule

# 모니터링 확인
./run_automated.sh status
```

행운을 빕니다! 🍀
