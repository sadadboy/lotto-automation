@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 완전 자동화 로또 구매 시스템 - Windows 실행 스크립트

echo 🎲 완전 자동화 로또 구매 시스템
echo ==================================

:: 환경 확인
call :check_environment
if errorlevel 1 exit /b 1

:: 인자에 따른 실행
if "%1"=="now" (
    call :run_immediate
) else if "%1"=="schedule" (
    call :run_scheduler  
) else if "%1"=="monitor" (
    call :run_with_monitor
) else if "%1"=="stop" (
    call :stop_services
) else if "%1"=="logs" (
    call :show_logs
) else if "%1"=="status" (
    call :show_status
) else if "%1"=="clean" (
    call :cleanup
) else if "%1"=="test" (
    call :run_test
) else (
    call :show_help
)

goto :eof

:: 환경 확인
:check_environment
echo ℹ️ 환경 확인 중...

:: Docker 설치 확인
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker가 설치되지 않았습니다.
    echo Docker Desktop을 설치해주세요: https://docs.docker.com/desktop/windows/
    exit /b 1
)

:: Docker Compose 확인
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose가 설치되지 않았습니다.
    exit /b 1
)

:: .env 파일 확인
if not exist .env (
    if exist .env.automated (
        echo ⚠️ .env 파일이 없습니다. .env.automated를 복사합니다.
        copy .env.automated .env >nul
        echo ⚠️ .env 파일을 편집하여 인증정보를 설정하세요!
        echo    LOTTO_USER_ID와 LOTTO_PASSWORD를 실제 값으로 변경하세요.
        pause
    ) else (
        echo ❌ .env 파일이 없습니다.
        exit /b 1
    )
)

:: 디렉토리 생성
if not exist data\logs mkdir data\logs
if not exist data\screenshots mkdir data\screenshots
if not exist secrets mkdir secrets

call :setup_secrets

echo ✅ 환경 확인 완료
goto :eof

:: Docker Secrets 설정
:setup_secrets
echo ℹ️ Docker Secrets 설정 중...

:: .env 파일에서 환경변수 읽기
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="LOTTO_USER_ID" set LOTTO_USER_ID=%%b
    if "%%a"=="LOTTO_PASSWORD" set LOTTO_PASSWORD=%%b
)

:: 인증정보 확인
if "!LOTTO_USER_ID!"=="" (
    echo ❌ LOTTO_USER_ID가 설정되지 않았습니다.
    exit /b 1
)
if "!LOTTO_PASSWORD!"=="" (
    echo ❌ LOTTO_PASSWORD가 설정되지 않았습니다.
    exit /b 1
)
if "!LOTTO_USER_ID!"=="your_lotto_user_id" (
    echo ❌ 기본 인증정보를 실제 값으로 변경하세요.
    exit /b 1
)

:: Secrets 파일 생성
echo !LOTTO_USER_ID!> secrets\lotto_user_id.txt
echo !LOTTO_PASSWORD!> secrets\lotto_password.txt

echo ✅ Docker Secrets 설정 완료
goto :eof

:: 도움말 표시
:show_help
echo 사용법: %0 [옵션]
echo.
echo 옵션:
echo   now                즉시 구매 실행
echo   schedule          스케줄 기반 자동 실행 시작
echo   monitor           모니터링 대시보드와 함께 실행
echo   stop              모든 서비스 중지
echo   logs              로그 확인
echo   status            실행 상태 확인
echo   clean             모든 컨테이너 및 이미지 제거
echo   test              테스트 모드 실행
echo   help              이 도움말 표시
echo.
echo 예시:
echo   %0 now             # 지금 즉시 로또 구매
echo   %0 schedule        # 매주 월/목 14시 자동 구매 시작
echo   %0 monitor         # 스케줄러 + 웹 모니터링 실행
echo   %0 stop            # 모든 서비스 중지
goto :eof

:: 즉시 실행
:run_immediate
echo ℹ️ 즉시 구매 실행 중...

docker-compose -f docker-compose.automated.yml --profile immediate up --build

echo ✅ 즉시 구매 완료
goto :eof

:: 스케줄러 실행
:run_scheduler
echo ℹ️ 스케줄 기반 자동 실행 시작...

docker-compose -f docker-compose.automated.yml --profile scheduler up -d --build

echo ✅ 스케줄러가 백그라운드에서 실행 중입니다.
echo 📝 로그 확인: %0 logs
echo 🛑 중지: %0 stop
goto :eof

:: 모니터링 포함 실행
:run_with_monitor
echo ℹ️ 모니터링과 함께 실행 중...

call :create_nginx_config

docker-compose -f docker-compose.automated.yml --profile scheduler --profile monitor up -d --build

:: 모니터 포트 확인
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="MONITOR_PORT" set MONITOR_PORT=%%b
)
if "!MONITOR_PORT!"=="" set MONITOR_PORT=8080

echo ✅ 시스템이 모니터링과 함께 실행 중입니다.
echo 📊 모니터링 대시보드: http://localhost:!MONITOR_PORT!
echo 📝 로그 확인: %0 logs
echo 🛑 중지: %0 stop
goto :eof

:: Nginx 설정 생성
:create_nginx_config
if not exist monitoring mkdir monitoring

(
echo events {
echo     worker_connections 1024;
echo }
echo.
echo http {
echo     include /etc/nginx/mime.types;
echo     default_type application/octet-stream;
echo.    
echo     server {
echo         listen 80;
echo         server_name localhost;
echo.        
echo         location / {
echo             root /usr/share/nginx/html;
echo             autoindex on;
echo             autoindex_exact_size off;
echo             autoindex_localtime on;
echo         }
echo.        
echo         location /logs/ {
echo             alias /usr/share/nginx/html/logs/;
echo             autoindex on;
echo             autoindex_exact_size off;
echo             autoindex_localtime on;
echo         }
echo.        
echo         location /screenshots/ {
echo             alias /usr/share/nginx/html/screenshots/;
echo             autoindex on;
echo             autoindex_exact_size off;
echo             autoindex_localtime on;
echo         }
echo     }
echo }
) > monitoring\nginx.conf

goto :eof

:: 서비스 중지
:stop_services
echo ℹ️ 모든 서비스 중지 중...

docker-compose -f docker-compose.automated.yml down

echo ✅ 모든 서비스가 중지되었습니다.
goto :eof

:: 로그 확인
:show_logs
echo ℹ️ 로그 확인 중...

if exist data\logs\lotto_auto_buyer.log (
    echo === 최근 로그 ===
    powershell "Get-Content data\logs\lotto_auto_buyer.log | Select-Object -Last 50"
)

if exist data\logs\cron.log (
    echo.
    echo === 크론 로그 ===
    powershell "Get-Content data\logs\cron.log | Select-Object -Last 20"
)

echo.
echo 실시간 로그 모니터링: docker-compose -f docker-compose.automated.yml logs -f
goto :eof

:: 상태 확인
:show_status
echo ℹ️ 실행 상태 확인 중...

docker-compose -f docker-compose.automated.yml ps

echo.
echo === 디스크 사용량 ===
if exist data\logs (
    for /f %%a in ('powershell "(Get-ChildItem -Recurse data\logs | Measure-Object -Property Length -Sum).Sum"') do echo 로그: %%a bytes
)
if exist data\screenshots (
    for /f %%a in ('powershell "(Get-ChildItem -Recurse data\screenshots | Measure-Object -Property Length -Sum).Sum"') do echo 스크린샷: %%a bytes
)
goto :eof

:: 정리
:cleanup
echo ⚠️ 모든 컨테이너, 이미지, 볼륨을 제거합니다.
set /p answer=계속하시겠습니까? (y/N): 

if /i "!answer!"=="y" (
    docker-compose -f docker-compose.automated.yml down -v --rmi all
    docker system prune -f
    echo ✅ 정리 완료
) else (
    echo ℹ️ 취소되었습니다.
)
goto :eof

:: 테스트 모드
:run_test
echo ℹ️ 테스트 모드 실행 중...

docker-compose -f docker-compose.automated.yml run --rm lotto-automated --test

echo ✅ 테스트 완료
goto :eof
