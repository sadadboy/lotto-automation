#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord 웹훅 URL 설정 도구
"""
import json
import os


def setup_discord_webhook():
    """Discord 웹훅 URL 설정"""
    
    print("🎯 Discord 알림 설정")
    print("=" * 50)
    
    # 설정 파일 로드
    config_file = "lotto_config.json"
    if not os.path.exists(config_file):
        print(f"❌ {config_file} 파일이 없습니다.")
        return False
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("📋 Discord 웹훅 URL을 설정하겠습니다.")
    print()
    print("🔗 Discord 웹훅 URL 생성 방법:")
    print("1. Discord 앱에서 알림을 받을 채널로 이동")
    print("2. 채널 설정(톱니바퀴) → 연동 → 웹훅")
    print("3. '새 웹훅' 클릭 → 이름 설정 → '웹훅 URL 복사'")
    print()
    
    # 현재 설정 확인
    discord_config = config.get('notifications', {}).get('discord', {})
    current_url = discord_config.get('webhook_url', '')
    current_enabled = discord_config.get('enabled', False)
    
    if current_url:
        print(f"📝 현재 웹훅 URL: {current_url[:50]}...")
        print(f"📝 현재 활성화 상태: {current_enabled}")
        print()
        
        choice = input("기존 설정을 변경하시겠습니까? (y/N): ").strip().lower()
        if choice not in ['y', 'yes']:
            print("✅ 기존 설정을 유지합니다.")
            return True
    
    # 웹훅 URL 입력
    webhook_url = input("Discord 웹훅 URL을 입력하세요: ").strip()
    
    if not webhook_url:
        print("❌ 웹훅 URL이 입력되지 않았습니다.")
        return False
    
    # URL 유효성 간단 검증
    if not webhook_url.startswith('https://discord.com/api/webhooks/'):
        print("⚠️ 올바른 Discord 웹훅 URL 형식이 아닙니다.")
        print("   URL은 'https://discord.com/api/webhooks/'로 시작해야 합니다.")
        
        continue_choice = input("그래도 계속하시겠습니까? (y/N): ").strip().lower()
        if continue_choice not in ['y', 'yes']:
            print("❌ 설정이 취소되었습니다.")
            return False
    
    # 알림 활성화 확인
    enable_notifications = input("Discord 알림을 활성화하시겠습니까? (Y/n): ").strip().lower()
    enabled = enable_notifications not in ['n', 'no']
    
    # 설정 업데이트
    if 'notifications' not in config:
        config['notifications'] = {}
    
    if 'discord' not in config['notifications']:
        config['notifications']['discord'] = {}
    
    config['notifications']['discord'].update({
        'enabled': enabled,
        'webhook_url': webhook_url,
        'notify_login': True,
        'notify_balance': True,
        'notify_recharge': True,
        'notify_purchase': True,
        'notify_errors': True
    })
    
    # 설정 파일 저장
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✅ Discord 알림 설정이 완료되었습니다!")
        print()
        print("📊 설정 내용:")
        print(f"   웹훅 URL: {webhook_url[:50]}...")
        print(f"   알림 활성화: {enabled}")
        print(f"   로그인 알림: {config['notifications']['discord']['notify_login']}")
        print(f"   잔액 알림: {config['notifications']['discord']['notify_balance']}")
        print(f"   충전 알림: {config['notifications']['discord']['notify_recharge']}")
        print(f"   구매 알림: {config['notifications']['discord']['notify_purchase']}")
        print(f"   오류 알림: {config['notifications']['discord']['notify_errors']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 저장 실패: {e}")
        return False


def test_discord_notification():
    """Discord 알림 테스트"""
    
    print("\n🧪 Discord 알림 테스트")
    print("=" * 30)
    
    try:
        # 설정 로드
        with open("lotto_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        discord_config = config.get('notifications', {}).get('discord', {})
        webhook_url = discord_config.get('webhook_url', '')
        enabled = discord_config.get('enabled', False)
        
        if not webhook_url or not enabled:
            print("❌ Discord 알림이 설정되지 않았거나 비활성화되어 있습니다.")
            return False
        
        # discord_notifier 모듈 import
        try:
            from discord_notifier import DiscordNotifier, NotificationLevel, NotificationMessage
            from datetime import datetime
            import asyncio
        except ImportError as e:
            print(f"❌ Discord 모듈 import 실패: {e}")
            return False
        
        async def send_test_notification():
            """테스트 알림 전송"""
            notifier = DiscordNotifier(webhook_url, enabled)
            
            # 올바른 파라미터로 send_notification 호출
            result = await notifier.send_notification(
                title="테스트 알림",
                message="🎉 로또 자동구매 Discord 알림 테스트입니다!",
                level=NotificationLevel.SUCCESS,
                테스트="성공",
                시간=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            await notifier.close()
            return result
        
        # 테스트 실행
        print("📤 테스트 알림 전송 중...")
        result = asyncio.run(send_test_notification())
        
        if result:
            print("✅ Discord 알림 테스트 성공!")
            print("💬 Discord 채널에서 테스트 메시지를 확인하세요.")
        else:
            print("❌ Discord 알림 테스트 실패")
            print("🔍 웹훅 URL이나 권한을 확인해주세요.")
        
        return result
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        return False


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Discord 알림 설정 도구')
    parser.add_argument('--setup', action='store_true', help='Discord 웹훅 설정')
    parser.add_argument('--test', action='store_true', help='Discord 알림 테스트')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_discord_webhook()
    elif args.test:
        test_discord_notification()
    else:
        print("🎯 Discord 알림 설정 도구")
        print("=" * 30)
        print("옵션을 선택하세요:")
        print("  --setup: Discord 웹훅 설정")
        print("  --test:  Discord 알림 테스트")
        print()
        print("예시:")
        print("  python setup_discord.py --setup")
        print("  python setup_discord.py --test")


if __name__ == "__main__":
    main()
