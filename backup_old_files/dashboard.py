# dashboard.py - 로또 자동구매 GUI 대시보드
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import json
import os
import logging
from datetime import datetime
import subprocess
import threading

app = Flask(__name__)
CORS(app)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 설정 파일 경로
CONFIG_FILE = 'lotto_config.json'
HISTORY_FILE = 'purchase_history.json'
LOG_FILE = 'lotto_auto_buyer.log'

# 전역 변수
purchase_thread = None
is_running = False

def load_config():
    """설정 파일 로드"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        return {}

def save_config(config):
    """설정 파일 저장"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"설정 파일 저장 실패: {e}")
        return False

def load_history():
    """구매 내역 로드"""
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def run_purchase():
    """구매 프로세스 실행"""
    global is_running
    is_running = True
    try:
        # Python 스크립트 실행
        result = subprocess.run(
            ['python', 'lotto_auto_buyer.py', '--now'],
            capture_output=True,
            text=True
        )
        logger.info(f"구매 완료: {result.stdout}")
    except Exception as e:
        logger.error(f"구매 실행 실패: {e}")
    finally:
        is_running = False

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """설정 관리 API"""
    if request.method == 'GET':
        return jsonify(load_config())
    
    elif request.method == 'POST':
        new_config = request.json
        if save_config(new_config):
            return jsonify({'status': 'success', 'message': '설정이 저장되었습니다.'})
        else:
            return jsonify({'status': 'error', 'message': '설정 저장 실패'}), 500

@app.route('/api/history')
def history():
    """구매 내역 조회 API"""
    return jsonify(load_history())

@app.route('/api/purchase', methods=['POST'])
def purchase():
    """구매 실행 API"""
    global purchase_thread, is_running
    
    if is_running:
        return jsonify({'status': 'error', 'message': '이미 구매가 진행 중입니다.'}), 400
    
    # 백그라운드에서 구매 실행
    purchase_thread = threading.Thread(target=run_purchase)
    purchase_thread.start()
    
    return jsonify({'status': 'success', 'message': '구매를 시작했습니다.'})

@app.route('/api/status')
def status():
    """현재 상태 조회 API"""
    return jsonify({
        'is_running': is_running,
        'config_exists': os.path.exists(CONFIG_FILE),
        'history_count': len(load_history())
    })

@app.route('/api/logs')
def logs():
    """로그 조회 API"""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 최근 100줄만 반환
            recent_logs = lines[-100:] if len(lines) > 100 else lines
            return jsonify({'logs': recent_logs})
    except:
        return jsonify({'logs': []})

@app.route('/api/screenshot/<filename>')
def screenshot(filename):
    """스크린샷 조회"""
    try:
        return send_file(f'screenshots/{filename}')
    except:
        return jsonify({'error': 'Screenshot not found'}), 404

@app.route('/api/screenshots')
def screenshots():
    """스크린샷 목록 조회"""
    try:
        files = os.listdir('screenshots')
        screenshots = [f for f in files if f.endswith('.png')]
        return jsonify(screenshots)
    except:
        return jsonify([])

if __name__ == '__main__':
    # templates 디렉토리 생성
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # 개발 서버 실행
    app.run(host='0.0.0.0', port=5000, debug=True)
