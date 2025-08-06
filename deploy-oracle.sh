#!/bin/bash
# 오라클 클라우드 배포 스크립트

set -e

echo "🚀 로또 자동구매 시스템 배포 시작..."

# 1. 시스템 업데이트
echo "📦 시스템 패키지 업데이트..."
sudo apt update && sudo apt upgrade -y

# 2. Docker 설치
echo "🐳 Docker 설치..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker 설치 완료"
else
    echo "✅ Docker 이미 설치됨"
fi

# 3. Docker Compose 설치
echo "🔧 Docker Compose 설치..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose 설치 완료"
else
    echo "✅ Docker Compose 이미 설치됨"
fi

# 4. 프로젝트 디렉토리 생성
PROJECT_DIR="$HOME/lotto_auto_complete"
if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
fi
cd "$PROJECT_DIR"

# 5. 환경변수 파일 설정
if [ ! -f ".env" ]; then
    echo "📝 환경변수 파일 설정..."
    read -s -p "마스터 패스워드를 입력하세요: " MASTER_PASSWORD
    echo
    
    cat > .env << EOF
LOTTO_MASTER_PASSWORD=$MASTER_PASSWORD
TZ=Asia/Seoul
DEBUG=false
CHROME_NO_SANDBOX=true
CHROME_DISABLE_GPU=true
CHROME_DISABLE_DEV_SHM=true
LOG_LEVEL=INFO
EOF
    chmod 600 .env
    echo "✅ 환경변수 파일 생성 완료"
else
    echo "✅ 환경변수 파일 이미 존재함"
fi

# 6. 로그 디렉토리 생성
mkdir -p logs
chmod 755 logs

# 7. 방화벽 설정 (선택사항)
echo "🔒 방화벽 설정..."
if command -v ufw &> /dev/null; then
    sudo ufw --force enable
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    # 대시보드용 포트 (필요시)
    # sudo ufw allow 8080
    echo "✅ 방화벽 설정 완료"
fi

# 8. 크론잡 설정
echo "⏰ 크론잡 설정..."
CRON_JOB="0 14 * * 1,4 cd $PROJECT_DIR && docker-compose --profile scheduler up -d"
(crontab -l 2>/dev/null | grep -v "lotto_auto_complete"; echo "$CRON_JOB") | crontab -
echo "✅ 크론잡 설정 완료 (매주 월, 목요일 14시)"

# 9. systemd 서비스 생성 (선택사항)
echo "🔧 시스템 서비스 생성..."
sudo tee /etc/systemd/system/lotto-scheduler.service > /dev/null << EOF
[Unit]
Description=Lotto Auto Buyer Scheduler
Requires=docker.service
After=docker.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose --profile scheduler up
ExecStop=/usr/local/bin/docker-compose --profile scheduler down
Restart=unless-stopped
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable lotto-scheduler.service
echo "✅ 시스템 서비스 생성 완료"

# 10. 테스트 실행
echo "🧪 설정 테스트..."
if [ -f "credentials.enc" ] && [ -f "lotto_config.json" ]; then
    echo "✅ 필수 파일 확인됨"
    
    # Docker 이미지 빌드
    docker-compose build
    
    # 테스트 실행
    echo "📱 테스트 실행 중..."
    docker-compose --profile manual run --rm lotto-auto-buyer python lotto_auto_buyer_integrated.py --test-credentials
    
    if [ $? -eq 0 ]; then
        echo "✅ 테스트 성공!"
    else
        echo "❌ 테스트 실패. 설정을 확인해주세요."
        exit 1
    fi
else
    echo "⚠️ credentials.enc 또는 lotto_config.json 파일이 없습니다."
    echo "💡 먼저 로컬에서 설정을 완료한 후 파일을 업로드해주세요."
fi

echo ""
echo "🎉 배포 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. credentials.enc 및 lotto_config.json 파일 업로드"
echo "2. 수동 실행: docker-compose --profile manual run --rm lotto-auto-buyer"
echo "3. 스케줄러 시작: sudo systemctl start lotto-scheduler"
echo "4. 로그 확인: docker-compose logs -f"
echo ""
echo "🔧 유용한 명령어:"
echo "- 상태 확인: sudo systemctl status lotto-scheduler"
echo "- 로그 확인: tail -f logs/cron.log"
echo "- 수동 실행: docker-compose --profile manual run --rm lotto-auto-buyer"
echo ""

# 11. 정리
echo "🧹 임시 파일 정리..."
sudo apt autoremove -y
sudo apt autoclean

echo "✅ 배포 스크립트 완료!"
