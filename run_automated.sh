#!/bin/bash
# 완전 자동화 로또 구매 시스템 - 통합 실행 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 스크립트 제목
echo "🎲 완전 자동화 로또 구매 시스템"
echo "=================================="

# 환경 확인
check_environment() {
    log_info "환경 확인 중..."
    
    # Docker 설치 확인
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        echo "Docker를 설치해주세요: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다."
        echo "Docker Compose를 설치해주세요."
        exit 1
    fi
    
    # .env 파일 확인
    if [ ! -f .env ]; then
        if [ -f .env.automated ]; then
            log_warning ".env 파일이 없습니다. .env.automated를 복사합니다."
            cp .env.automated .env
            log_warning "⚠️  .env 파일을 편집하여 인증정보를 설정하세요!"
            echo "   LOTTO_USER_ID와 LOTTO_PASSWORD를 실제 값으로 변경하세요."
        else
            log_error ".env 파일이 없습니다."
            exit 1
        fi
    fi
    
    # 필수 환경변수 확인
    source .env
    if [ -z "$LOTTO_USER_ID" ] || [ -z "$LOTTO_PASSWORD" ] || [ "$LOTTO_USER_ID" = "your_lotto_user_id" ]; then
        log_error "인증정보가 설정되지 않았습니다."
        echo "   .env 파일에서 LOTTO_USER_ID와 LOTTO_PASSWORD를 설정하세요."
        exit 1
    fi
    
    # 디렉토리 생성
    mkdir -p data/logs data/screenshots secrets
    
    log_success "환경 확인 완료"
}

# Docker Secrets 설정
setup_secrets() {
    log_info "Docker Secrets 설정 중..."
    
    source .env
    
    # Secrets 파일 생성
    echo -n "$LOTTO_USER_ID" > secrets/lotto_user_id.txt
    echo -n "$LOTTO_PASSWORD" > secrets/lotto_password.txt
    
    # 권한 설정
    chmod 600 secrets/*
    
    log_success "Docker Secrets 설정 완료"
}

# 도움말 표시
show_help() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  now                즉시 구매 실행"
    echo "  schedule          스케줄 기반 자동 실행 시작"
    echo "  monitor           모니터링 대시보드와 함께 실행"
    echo "  stop              모든 서비스 중지"
    echo "  logs              로그 확인"
    echo "  status            실행 상태 확인"
    echo "  clean             모든 컨테이너 및 이미지 제거"
    echo "  test              테스트 모드 실행"
    echo "  help              이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 now             # 지금 즉시 로또 구매"
    echo "  $0 schedule        # 매주 월/목 14시 자동 구매 시작"
    echo "  $0 monitor         # 스케줄러 + 웹 모니터링 실행"
    echo "  $0 stop            # 모든 서비스 중지"
}

# 즉시 실행
run_immediate() {
    log_info "즉시 구매 실행 중..."
    
    docker-compose -f docker-compose.automated.yml --profile immediate up --build
    
    log_success "즉시 구매 완료"
}

# 스케줄러 실행
run_scheduler() {
    log_info "스케줄 기반 자동 실행 시작..."
    
    docker-compose -f docker-compose.automated.yml --profile scheduler up -d --build
    
    log_success "스케줄러가 백그라운드에서 실행 중입니다."
    echo "로그 확인: $0 logs"
    echo "중지: $0 stop"
}

# 모니터링 포함 실행
run_with_monitor() {
    log_info "모니터링과 함께 실행 중..."
    
    # nginx 설정 생성
    create_nginx_config
    
    docker-compose -f docker-compose.automated.yml --profile scheduler --profile monitor up -d --build
    
    source .env
    MONITOR_PORT=${MONITOR_PORT:-8080}
    
    log_success "시스템이 모니터링과 함께 실행 중입니다."
    echo "📊 모니터링 대시보드: http://localhost:$MONITOR_PORT"
    echo "📝 로그 확인: $0 logs"
    echo "🛑 중지: $0 stop"
}

# Nginx 설정 생성
create_nginx_config() {
    mkdir -p monitoring
    cat > monitoring/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    server {
        listen 80;
        server_name localhost;
        
        location / {
            root /usr/share/nginx/html;
            autoindex on;
            autoindex_exact_size off;
            autoindex_localtime on;
        }
        
        location /logs/ {
            alias /usr/share/nginx/html/logs/;
            autoindex on;
            autoindex_exact_size off;
            autoindex_localtime on;
        }
        
        location /screenshots/ {
            alias /usr/share/nginx/html/screenshots/;
            autoindex on;
            autoindex_exact_size off;
            autoindex_localtime on;
        }
    }
}
EOF
}

# 서비스 중지
stop_services() {
    log_info "모든 서비스 중지 중..."
    
    docker-compose -f docker-compose.automated.yml down
    
    log_success "모든 서비스가 중지되었습니다."
}

# 로그 확인
show_logs() {
    log_info "로그 확인 중..."
    
    if [ -f data/logs/lotto_auto_buyer.log ]; then
        echo "=== 최근 로그 (마지막 50줄) ==="
        tail -50 data/logs/lotto_auto_buyer.log
    fi
    
    if [ -f data/logs/cron.log ]; then
        echo ""
        echo "=== 크론 로그 (마지막 20줄) ==="
        tail -20 data/logs/cron.log
    fi
    
    echo ""
    echo "실시간 로그 모니터링: docker-compose -f docker-compose.automated.yml logs -f"
}

# 상태 확인
show_status() {
    log_info "실행 상태 확인 중..."
    
    docker-compose -f docker-compose.automated.yml ps
    
    echo ""
    echo "=== 디스크 사용량 ==="
    du -sh data/logs data/screenshots 2>/dev/null || echo "로그/스크린샷 디렉토리가 없습니다."
}

# 정리
cleanup() {
    log_warning "모든 컨테이너, 이미지, 볼륨을 제거합니다."
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f docker-compose.automated.yml down -v --rmi all
        docker system prune -f
        log_success "정리 완료"
    else
        log_info "취소되었습니다."
    fi
}

# 테스트 모드
run_test() {
    log_info "테스트 모드 실행 중..."
    
    docker-compose -f docker-compose.automated.yml run --rm lotto-automated --test
    
    log_success "테스트 완료"
}

# 메인 로직
main() {
    case "${1:-help}" in
        "now")
            check_environment
            setup_secrets
            run_immediate
            ;;
        "schedule")
            check_environment
            setup_secrets
            run_scheduler
            ;;
        "monitor")
            check_environment
            setup_secrets
            run_with_monitor
            ;;
        "stop")
            stop_services
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "clean")
            cleanup
            ;;
        "test")
            check_environment
            setup_secrets
            run_test
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
}

# 트랩 설정 (Ctrl+C 처리)
trap 'echo -e "\n${YELLOW}⚠️  중단되었습니다.${NC}"; exit 130' INT

# 스크립트 실행
main "$@"
