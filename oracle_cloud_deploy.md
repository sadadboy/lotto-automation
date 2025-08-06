# oracle_cloud_deploy.md - 오라클 클라우드 배포 가이드

## 🌥️ 오라클 클라우드 배포 가이드

### 1. 오라클 클라우드 인스턴스 생성

#### 1.1 인스턴스 사양
- **Shape**: VM.Standard.A1.Flex (ARM 기반, 무료)
- **OCPU**: 2개
- **Memory**: 12GB
- **OS**: Ubuntu 22.04
- **Storage**: 50GB

#### 1.2 보안 규칙 설정
```bash
# 인바운드 규칙 추가
- 포트 5000: GUI 대시보드
- 포트 5001: API 서버 (선택사항)
- 포트 22: SSH
```

### 2. 서버 초기 설정

#### 2.1 SSH 접속
```bash
ssh -i your-private-key.pem ubuntu@your-instance-ip
```

#### 2.2 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2.3 필수 패키지 설치
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git 설치
sudo apt install -y git
```

### 3. 프로젝트 배포

#### 3.1 프로젝트 클론
```bash
git clone https://github.com/your-repo/lotto-auto-complete.git
cd lotto-auto-complete
```

#### 3.2 설정 파일 수정
```bash
# 설정 파일 복사
cp lotto_config.json.example lotto_config.json

# 설정 편집
nano lotto_config.json
# 로그인 정보 및 설정 입력
```

#### 3.3 Docker 이미지 빌드 및 실행
```bash
# ARM 아키텍처용 이미지 빌드
docker-compose -f docker-compose.arm.yml build

# 백그라운드 실행
docker-compose -f docker-compose.arm.yml up -d

# 로그 확인
docker-compose logs -f
```

### 4. 방화벽 설정

#### 4.1 Ubuntu 방화벽
```bash
sudo ufw allow 22/tcp
sudo ufw allow 5000/tcp
sudo ufw allow 5001/tcp
sudo ufw enable
```

#### 4.2 오라클 클라우드 보안 리스트
1. OCI 콘솔 접속
2. Networking > Virtual Cloud Networks
3. Security Lists > Add Ingress Rules
4. 포트 5000, 5001 추가

### 5. HTTPS 설정 (선택사항)

#### 5.1 Nginx 설치
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

#### 5.2 Nginx 설정
```bash
sudo nano /etc/nginx/sites-available/lotto
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 5.3 SSL 인증서 발급
```bash
sudo ln -s /etc/nginx/sites-available/lotto /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com
```

### 6. 모니터링 설정

#### 6.1 시스템 모니터링
```bash
# htop 설치
sudo apt install -y htop

# 디스크 사용량 확인
df -h

# Docker 상태 확인
docker ps
docker stats
```

#### 6.2 자동 재시작 설정
```bash
# systemd 서비스 생성
sudo nano /etc/systemd/system/lotto-auto.service
```

```ini
[Unit]
Description=Lotto Auto Buyer
After=docker.service
Requires=docker.service

[Service]
Type=forking
WorkingDirectory=/home/ubuntu/lotto-auto-complete
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 활성화
sudo systemctl enable lotto-auto
sudo systemctl start lotto-auto
```

### 7. 백업 설정

#### 7.1 자동 백업 스크립트
```bash
nano backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 설정 파일 백업
tar -czf $BACKUP_DIR/lotto_backup_$DATE.tar.gz \
    lotto_config.json \
    purchase_history.json \
    winning_numbers.json \
    screenshots/

# 7일 이상된 백업 삭제
find $BACKUP_DIR -name "lotto_backup_*.tar.gz" -mtime +7 -delete
```

#### 7.2 크론탭 설정
```bash
crontab -e
# 매일 새벽 3시 백업
0 3 * * * /home/ubuntu/lotto-auto-complete/backup.sh
```

### 8. 문제 해결

#### 8.1 Docker 권한 문제
```bash
# Docker 그룹에 사용자 추가 후 재로그인
sudo usermod -aG docker $USER
exit
# 다시 SSH 접속
```

#### 8.2 메모리 부족
```bash
# 스왑 파일 생성
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### 8.3 포트 접근 불가
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep 5000

# Docker 네트워크 확인
docker network ls
docker network inspect lotto-network
```

### 9. 보안 강화

#### 9.1 SSH 보안
```bash
# SSH 설정 편집
sudo nano /etc/ssh/sshd_config

# 다음 설정 변경
PermitRootLogin no
PasswordAuthentication no
```

#### 9.2 환경 변수 사용
```bash
# .env 파일 생성
nano .env
```

```env
LOTTO_USER_ID=your_id
LOTTO_PASSWORD=your_password
FLASK_SECRET_KEY=your-secret-key
```

### 10. 성능 최적화

#### 10.1 Docker 리소스 제한
```yaml
# docker-compose.yml에 추가
services:
  lotto-buyer:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

#### 10.2 로그 순환
```bash
# Docker 로그 크기 제한
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### 11. 업데이트 절차

```bash
# 1. 백업
./backup.sh

# 2. 서비스 중지
docker-compose down

# 3. 코드 업데이트
git pull origin main

# 4. 이미지 재빌드
docker-compose build --no-cache

# 5. 서비스 시작
docker-compose up -d

# 6. 상태 확인
docker-compose ps
docker-compose logs -f
```

## 📞 지원

문제가 발생하면 다음을 확인하세요:
- Docker 로그: `docker-compose logs`
- 시스템 로그: `journalctl -u lotto-auto`
- 애플리케이션 로그: `docker exec lotto-auto-buyer cat /app/logs/lotto_auto_buyer.log`
