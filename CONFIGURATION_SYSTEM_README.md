# CONFIGURATION_SYSTEM_README.md

# 🎲 로또 자동구매 시스템 - 설정 관리 시스템

## 📋 개요

Clean Architecture와 TDD 원칙을 적용하여 구현된 로또 자동구매 시스템의 설정 관리 모듈입니다.
사용자 인증 정보는 AES 암호화로 안전하게 보호되며, 모든 설정은 JSON 파일로 관리됩니다.

## 🏗️ 아키텍처

```
src/
├── domain/                    # 도메인 레이어
│   ├── entities/             # 비즈니스 엔티티
│   │   ├── configuration.py  # 메인 설정 엔티티
│   │   ├── user_credentials.py
│   │   ├── purchase_settings.py
│   │   └── recharge_settings.py
│   ├── repositories/         # 레포지토리 인터페이스
│   │   └── configuration_repository.py
│   └── services/            # 도메인 서비스
│       └── configuration_service.py
├── application/             # 애플리케이션 레이어
│   └── usecases/           # 유스케이스
│       └── configuration_usecase.py
├── infrastructure/         # 인프라스트럭처 레이어
│   └── repositories/      # 레포지토리 구현체
│       └── file_configuration_repository.py
└── config/                # 설정 관리
    ├── dependency_injection.py  # DI 컨테이너
    └── configuration_cli.py     # CLI 도구
```

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install cryptography pytest pytest-mock
```

### 2. 최초 설정 생성

```bash
# 대화형 설정 생성
python setup_configuration.py

# 또는 CLI로 직접 생성
python -m src.config.configuration_cli init
```

### 3. 설정 확인

```bash
# 설정 상태 확인
python -m src.config.configuration_cli status

# 설정 내용 보기 (마스터 비밀번호 필요)
python -m src.config.configuration_cli show
```

## 🛠️ 주요 기능

### ✅ 구현 완료된 기능

1. **보안 설정 관리**
   - AES-256 암호화로 사용자 인증 정보 보호
   - PBKDF2를 사용한 마스터 키 생성
   - 설정 파일 무결성 검증

2. **유연한 구매 설정**
   - 구매 시간 예약 (HH:MM 형식)
   - 구매 수량 설정 (1-5게임)
   - 다양한 번호 선택 방식 지원
     - 자동 선택
     - 수동 선택 (6개 번호)
     - 반자동 선택 (3개 번호)
     - AI 추천
     - 통계 분석 기반

3. **자동 충전 관리**
   - 최소 잔액 설정
   - 자동 충전 금액 설정
   - 충전 필요 여부 자동 판단

4. **디스코드 알림**
   - 웹훅 URL 설정
   - 알림 ON/OFF 제어

5. **설정 백업 및 복원**
   - 타임스탬프 기반 자동 백업
   - 수동 백업 이름 지정
   - 설정 초기화 시 자동 백업

### 🎯 설정 항목

| 분류 | 항목 | 설명 | 예시 |
|------|------|------|------|
| **사용자** | user_id | 동행복권 사용자 ID | testuser |
| | password | 동행복권 비밀번호 | ******** |
| **구매** | schedule_time | 구매 시간 | 14:00 |
| | purchase_count | 구매 수량 | 3 |
| | lotto_list | 번호 선택 방식 | [자동, 수동, 반자동] |
| **충전** | auto_recharge | 자동충전 사용 | true |
| | minimum_balance | 최소 잔액 | 5000 |
| | recharge_amount | 충전 금액 | 50000 |
| **알림** | webhook_url | 디스코드 웹훅 | https://discord.com/... |
| | enable_notifications | 알림 사용 | true |

## 🖥️ 사용법

### CLI 명령어

```bash
# 설정 초기화
python -m src.config.configuration_cli init \
  --user-id "your_id" \
  --schedule-time "15:30" \
  --purchase-count 3

# 설정 상태 확인
python -m src.config.configuration_cli status

# 설정 내용 표시
python -m src.config.configuration_cli show

# 구매 설정 수정
python -m src.config.configuration_cli update-purchase \
  --schedule-time "16:00" \
  --purchase-count 5

# 충전 설정 수정
python -m src.config.configuration_cli update-recharge \
  --auto-recharge true \
  --minimum-balance 10000

# 설정 백업
python -m src.config.configuration_cli backup --name "manual_backup"

# 설정 초기화
python -m src.config.configuration_cli reset --force
```

### 프로그래밍 인터페이스

```python
from src.config.dependency_injection import get_configuration_usecase

# UseCase 인스턴스 생성
usecase = get_configuration_usecase("config/my_config.json")

# 최초 설정 생성
setup_data = {
    "user_id": "your_id",
    "password": "your_password",
    "master_password": "master_password_123456",
    "schedule_time": "14:00",
    "purchase_count": 3
}

result = usecase.setup_initial_configuration(setup_data)

# 설정 조회
dashboard_data = usecase.get_configuration_dashboard_data("master_password_123456")

# 설정 업데이트
update_data = {"schedule_time": "15:30"}
usecase.update_purchase_configuration(update_data, "master_password_123456")
```

## 🧪 테스트

### 테스트 실행

```bash
# 모든 테스트 실행
python run_tests.py

# 단위 테스트만 실행
python run_tests.py unit

# 통합 테스트만 실행  
python run_tests.py integration

# 커버리지 확인
python run_tests.py coverage
```

### 테스트 구조

```
tests/
├── unit/                          # 단위 테스트
│   ├── test_configuration.py      # 엔티티 테스트
│   ├── test_configuration_repository.py  # Repository 테스트
│   ├── test_configuration_service.py     # Service 테스트
│   └── test_configuration_usecase.py     # UseCase 테스트
├── integration/                   # 통합 테스트
│   └── test_configuration_integration.py
└── fixtures/                     # 테스트 픽스처
    └── __init__.py
```

## 📁 파일 구조

### 설정 파일 구조

```json
{
  "purchase": {
    "schedule_time": "14:00",
    "count": 3,
    "lotto_list": [
      {"type": "자동", "numbers": []},
      {"type": "수동", "numbers": [1, 2, 3, 4, 5, 6]},
      {"type": "반자동", "numbers": [7, 8, 9]}
    ]
  },
  "recharge": {
    "auto_recharge": true,
    "minimum_balance": 5000,
    "recharge_amount": 50000
  },
  "discord": {
    "webhook_url": "https://discord.com/api/webhooks/...",
    "enable_notifications": true
  },
  "encrypted_credentials": {
    "encrypted_user_id": "gAAAAABh...",
    "encrypted_password": "gAAAAABh..."
  },
  "metadata": {
    "created_at": "2024-01-01T12:00:00",
    "version": "1.0",
    "encrypted": true
  }
}
```

## 🔒 보안

### 암호화 방식

- **알고리즘**: AES-256 (Fernet 방식)
- **키 생성**: PBKDF2-HMAC-SHA256 (100,000 라운드)
- **솔트**: 고정 값 (프로덕션에서는 랜덤 생성 권장)

### 보안 권장사항

1. **마스터 비밀번호**
   - 최소 6자 이상 사용
   - 영문, 숫자, 특수문자 조합 권장
   - 정기적인 변경 권장

2. **설정 파일**
   - 적절한 파일 권한 설정 (600)
   - 정기적인 백업
   - 버전 관리에서 제외 (.gitignore)

## 🐛 문제 해결

### 자주 발생하는 문제

1. **"설정 파일을 찾을 수 없습니다"**
   ```bash
   # 설정 디렉토리 생성
   mkdir -p config
   
   # 설정 초기화
   python -m src.config.configuration_cli init
   ```

2. **"마스터 비밀번호가 틀렸습니다"**
   ```bash
   # 비밀번호 검증
   python -m src.config.configuration_cli validate-password
   ```

3. **"설정 파일이 손상되었습니다"**
   ```bash
   # 백업에서 복원하거나 재설정
   python -m src.config.configuration_cli reset
   ```

### 로그 확인

```bash
# 애플리케이션 로그 확인
tail -f logs/lotto_system.log

# 설정 관련 로그만 필터링
grep "Configuration" logs/lotto_system.log
```

## 🔄 업그레이드

### 설정 마이그레이션

새 버전으로 업그레이드할 때:

1. 기존 설정 백업
2. 새 코드 배포
3. 설정 무결성 확인
4. 필요시 설정 업데이트

```bash
# 백업 생성
python -m src.config.configuration_cli backup --name "before_upgrade"

# 업그레이드 후 무결성 확인
python -m src.config.configuration_cli status
```

## 🤝 기여

### 개발 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 테스트 실행
python run_tests.py

# 코드 스타일 확인 (선택)
# pip install black flake8
# black src/ tests/
# flake8 src/ tests/
```

### 코딩 표준

- **아키텍처**: Clean Architecture 원칙 준수
- **테스트**: TDD 방식으로 테스트 먼저 작성
- **명명**: 한국어 주석, 영어 변수명
- **타입힌트**: 모든 public 메서드에 타입 힌트 적용

## 📄 라이선스

이 프로젝트는 개인 사용 목적으로 제작되었습니다.

## 📞 지원

문제가 발생하거나 개선 제안이 있으시면 GitHub Issue를 생성해주세요.

---

**⚠️ 주의사항**: 이 시스템은 교육 및 개인 사용 목적으로 제작되었습니다. 
실제 로또 구매에 사용할 때는 충분한 테스트를 거친 후 사용하시기 바랍니다.
