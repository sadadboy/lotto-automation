#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord 알림 서비스 모듈
"""
import asyncio
import aiohttp
import json
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class NotificationLevel(Enum):
    """알림 레벨"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class NotificationMessage:
    """알림 메시지"""
    title: str
    message: str
    level: NotificationLevel
    timestamp: datetime
    extra_data: Optional[Dict[str, Any]] = None


class DiscordNotifier:
    """Discord 웹훅 알림 서비스"""
    
    def __init__(self, webhook_url: str, enabled: bool = True):
        self.webhook_url = webhook_url
        self.enabled = enabled
        self.session = None
        
        # 알림 레벨별 색상 및 이모지
        self.color_map = {
            NotificationLevel.INFO: 0x3498db,      # 파란색
            NotificationLevel.SUCCESS: 0x2ecc71,   # 초록색
            NotificationLevel.WARNING: 0xf39c12,   # 주황색
            NotificationLevel.ERROR: 0xe74c3c,     # 빨간색
            NotificationLevel.CRITICAL: 0x8e44ad   # 보라색
        }
        
        self.emoji_map = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.SUCCESS: "✅",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨"
        }
    
    def is_enabled(self) -> bool:
        """알림 서비스 활성화 여부"""
        return self.enabled and bool(self.webhook_url)
    
    async def send_notification(self, 
                              title: str, 
                              message: str, 
                              level: NotificationLevel = NotificationLevel.INFO,
                              **extra_data) -> bool:
        """알림 전송"""
        if not self.is_enabled():
            return False
        
        try:
            notification = NotificationMessage(
                title=title,
                message=message,
                level=level,
                timestamp=datetime.now(),
                extra_data=extra_data if extra_data else None
            )
            
            return await self._send_webhook(notification)
            
        except Exception as e:
            print(f"Discord 알림 전송 실패: {e}")
            return False
    
    async def _send_webhook(self, notification: NotificationMessage) -> bool:
        """Discord 웹훅으로 실제 전송"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # 이모지 및 색상
            emoji = self.emoji_map.get(notification.level, "📢")
            color = self.color_map.get(notification.level, 0x95a5a6)
            
            # Embed 구성
            embed = {
                "title": f"{emoji} {notification.title}",
                "description": notification.message,
                "color": color,
                "timestamp": notification.timestamp.isoformat(),
                "footer": {
                    "text": f"로또 자동구매 시스템 | Level: {notification.level.value.upper()}"
                }
            }
            
            # 추가 데이터가 있으면 필드로 추가
            if notification.extra_data:
                embed["fields"] = []
                for key, value in notification.extra_data.items():
                    # 한글 키를 적절한 이름으로 변환
                    field_name = self._format_field_name(key)
                    embed["fields"].append({
                        "name": field_name,
                        "value": str(value),
                        "inline": True
                    })
            
            # 시간 정보 추가
            embed["fields"] = embed.get("fields", [])
            embed["fields"].append({
                "name": "📅 시간",
                "value": notification.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "inline": True
            })
            
            payload = {
                "embeds": [embed],
                "username": "로또 자동구매 봇",
                "avatar_url": "https://cdn.discordapp.com/attachments/placeholder/lotto_bot_avatar.png"
            }
            
            async with self.session.post(self.webhook_url, json=payload) as response:
                success = response.status == 204
                if success:
                    print(f"✅ Discord 알림 전송 성공: {notification.title}")
                else:
                    print(f"❌ Discord 알림 전송 실패: HTTP {response.status}")
                return success
                
        except Exception as e:
            print(f"Discord 웹훅 전송 오류: {e}")
            return False
    
    def _format_field_name(self, key: str) -> str:
        """필드 이름 포맷팅"""
        name_map = {
            "user_id": "👤 사용자",
            "사용자": "👤 사용자",
            "balance": "💰 잔액",
            "잔액": "💰 잔액",
            "amount": "💳 금액",
            "금액": "💳 금액",
            "충전금액": "💳 충전금액",
            "games": "🎰 게임수",
            "게임수": "🎰 게임수",
            "구매게임수": "🎰 구매게임수",
            "numbers": "🔢 번호",
            "번호": "🔢 번호",
            "error": "⚠️ 오류",
            "오류": "⚠️ 오류",
            "url": "🔗 URL",
            "status": "📊 상태",
            "상태": "📊 상태"
        }
        return name_map.get(key, f"📌 {key}")
    
    async def close(self):
        """세션 종료"""
        if self.session:
            await self.session.close()
            self.session = None
    
    # 편의 메서드들
    async def send_info(self, title: str, message: str, **kwargs):
        """정보 알림"""
        return await self.send_notification(title, message, NotificationLevel.INFO, **kwargs)
    
    async def send_success(self, title: str, message: str, **kwargs):
        """성공 알림"""
        return await self.send_notification(title, message, NotificationLevel.SUCCESS, **kwargs)
    
    async def send_warning(self, title: str, message: str, **kwargs):
        """경고 알림"""
        return await self.send_notification(title, message, NotificationLevel.WARNING, **kwargs)
    
    async def send_error(self, title: str, message: str, **kwargs):
        """오류 알림"""
        return await self.send_notification(title, message, NotificationLevel.ERROR, **kwargs)
    
    async def send_critical(self, title: str, message: str, **kwargs):
        """심각한 오류 알림"""
        return await self.send_notification(title, message, NotificationLevel.CRITICAL, **kwargs)


class NotificationManager:
    """알림 관리자 - 설정 기반 초기화"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.discord_notifier = None
        self._setup_discord()
    
    def _setup_discord(self):
        """Discord 알림 설정"""
        try:
            discord_config = self.config.get('notifications', {}).get('discord', {})
            
            enabled = discord_config.get('enabled', False)
            webhook_url = discord_config.get('webhook_url', '')
            
            if enabled and webhook_url:
                self.discord_notifier = DiscordNotifier(webhook_url, enabled)
                print("✅ Discord 알림 서비스 활성화")
            else:
                if not enabled:
                    print("ℹ️ Discord 알림이 비활성화되어 있습니다")
                elif not webhook_url:
                    print("⚠️ Discord 웹훅 URL이 설정되지 않았습니다")
                    
        except Exception as e:
            print(f"⚠️ Discord 알림 설정 실패: {e}")
            self.discord_notifier = None
    
    def is_notification_enabled(self, notification_type: str) -> bool:
        """특정 타입의 알림이 활성화되어 있는지 확인"""
        if not self.discord_notifier or not self.discord_notifier.is_enabled():
            return False
        
        discord_config = self.config.get('notifications', {}).get('discord', {})
        return discord_config.get(f'notify_{notification_type}', True)
    
    async def notify_login_start(self, user_id: str):
        """로그인 시작 알림"""
        if self.is_notification_enabled('login'):
            await self.discord_notifier.send_info(
                "로그인 시작",
                f"로또 사이트 로그인을 시작합니다.",
                사용자=user_id
            )
    
    async def notify_login_success(self, user_id: str):
        """로그인 성공 알림"""
        if self.is_notification_enabled('login'):
            await self.discord_notifier.send_success(
                "로그인 성공",
                f"로또 사이트에 성공적으로 로그인했습니다.",
                사용자=user_id
            )
    
    async def notify_login_failure(self, user_id: str, error: str = ""):
        """로그인 실패 알림"""
        if self.is_notification_enabled('login'):
            message = "로그인에 실패했습니다."
            extra_data = {"사용자": user_id}
            if error:
                message += f" ({error})"
                extra_data["오류"] = error
            
            await self.discord_notifier.send_error("로그인 실패", message, **extra_data)
    
    async def notify_balance_check(self, balance: int):
        """잔액 확인 알림"""
        if self.is_notification_enabled('balance'):
            await self.discord_notifier.send_info(
                "잔액 확인",
                f"현재 예치금 잔액을 확인했습니다.",
                잔액=f"{balance:,}원"
            )
    
    async def notify_recharge_start(self, amount: int):
        """충전 시작 알림"""
        if self.is_notification_enabled('recharge'):
            await self.discord_notifier.send_warning(
                "충전 시작",
                f"예치금 충전을 시작합니다.",
                충전금액=f"{amount:,}원"
            )
    
    async def notify_recharge_success(self, amount: int, new_balance: int = None):
        """충전 성공 알림"""
        if self.is_notification_enabled('recharge'):
            extra_data = {"충전금액": f"{amount:,}원"}
            if new_balance is not None:
                extra_data["충전후잔액"] = f"{new_balance:,}원"
            
            await self.discord_notifier.send_success(
                "충전 완료",
                f"{amount:,}원 충전이 완료되었습니다.",
                **extra_data
            )
    
    async def notify_recharge_failure(self, amount: int, error: str = ""):
        """충전 실패 알림"""
        if self.is_notification_enabled('recharge'):
            message = f"{amount:,}원 충전에 실패했습니다."
            extra_data = {"충전금액": f"{amount:,}원"}
            if error:
                message += f" ({error})"
                extra_data["오류"] = error
            
            await self.discord_notifier.send_error("충전 실패", message, **extra_data)
    
    async def notify_purchase_start(self, games_count: int):
        """로또 구매 시작 알림"""
        if self.is_notification_enabled('purchase'):
            await self.discord_notifier.send_info(
                "로또 구매 시작",
                f"로또 구매를 시작합니다.",
                구매게임수=f"{games_count}게임",
                예상금액=f"{games_count * 1000:,}원"
            )
    
    async def notify_purchase_success(self, games_count: int, total_amount: int = None):
        """로또 구매 성공 알림"""
        if self.is_notification_enabled('purchase'):
            extra_data = {"구매게임수": f"{games_count}게임"}
            if total_amount:
                extra_data["구매금액"] = f"{total_amount:,}원"
            else:
                extra_data["구매금액"] = f"{games_count * 1000:,}원"
            
            await self.discord_notifier.send_success(
                "로또 구매 완료",
                f"{games_count}게임 구매가 완료되었습니다.",
                **extra_data
            )
    
    async def notify_purchase_failure(self, games_count: int, error: str = ""):
        """로또 구매 실패 알림"""
        if self.is_notification_enabled('purchase'):
            message = f"{games_count}게임 로또 구매에 실패했습니다."
            extra_data = {"구매게임수": f"{games_count}게임"}
            if error:
                message += f" ({error})"
                extra_data["오류"] = error
            
            await self.discord_notifier.send_error("로또 구매 실패", message, **extra_data)
    
    async def notify_error(self, title: str, error_message: str, **extra_data):
        """일반 오류 알림"""
        if self.is_notification_enabled('errors'):
            await self.discord_notifier.send_error(title, error_message, **extra_data)
    
    async def notify_critical(self, title: str, error_message: str, **extra_data):
        """심각한 오류 알림"""
        if self.is_notification_enabled('errors'):
            await self.discord_notifier.send_critical(title, error_message, **extra_data)
    
    async def notify_program_start(self):
        """프로그램 시작 알림"""
        if self.is_notification_enabled('login'):  # login 설정을 따름
            await self.discord_notifier.send_info(
                "프로그램 시작",
                "🚀 로또 자동구매 프로그램을 시작합니다."
            )
    
    async def notify_program_complete(self):
        """프로그램 완료 알림"""
        if self.is_notification_enabled('purchase'):  # purchase 설정을 따름
            await self.discord_notifier.send_success(
                "프로그램 완료",
                "🎉 로또 자동구매가 성공적으로 완료되었습니다."
            )
    
    async def cleanup(self):
        """리소스 정리"""
        if self.discord_notifier:
            await self.discord_notifier.close()


# 동기 함수로 비동기 알림 실행하는 유틸리티
def run_notification(coro):
    """비동기 알림을 동기 함수에서 실행 - 세션 정리 포함"""
    try:
        # 새로운 이벤트 루프에서 안전하게 실행
        loop = None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 이벤트 루프가 있으면 태스크로 실행
                asyncio.create_task(coro)
                return
        except RuntimeError:
            pass
        
        # 새로운 이벤트 루프에서 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(coro)
        finally:
            # 루프 정리
            try:
                loop.close()
            except:
                pass
                
    except Exception as e:
        print(f"알림 실행 오류: {e}")
    finally:
        # 이벤트 루프 정리
        try:
            if loop and not loop.is_closed():
                loop.close()
        except:
            pass


if __name__ == "__main__":
    # 간단한 테스트
    async def test_discord_notification():
        """Discord 알림 테스트"""
        # 테스트용 설정
        test_config = {
            "notifications": {
                "discord": {
                    "enabled": True,
                    "webhook_url": "YOUR_DISCORD_WEBHOOK_URL_HERE",
                    "notify_login": True,
                    "notify_balance": True,
                    "notify_recharge": True,
                    "notify_purchase": True,
                    "notify_errors": True
                }
            }
        }
        
        manager = NotificationManager(test_config)
        
        if manager.discord_notifier and manager.discord_notifier.is_enabled():
            print("🧪 Discord 알림 테스트 시작...")
            
            await manager.notify_program_start()
            await asyncio.sleep(1)
            
            await manager.notify_login_start("test_user")
            await asyncio.sleep(1)
            
            await manager.notify_login_success("test_user")
            await asyncio.sleep(1)
            
            await manager.notify_balance_check(45000)
            await asyncio.sleep(1)
            
            await manager.notify_purchase_start(5)
            await asyncio.sleep(1)
            
            await manager.notify_purchase_success(5, 5000)
            await asyncio.sleep(1)
            
            await manager.notify_program_complete()
            
            await manager.cleanup()
            print("✅ Discord 알림 테스트 완료")
        else:
            print("❌ Discord 알림이 설정되지 않았습니다")
            print("웹훅 URL을 설정하고 enabled: true로 변경해주세요")
    
    # asyncio.run(test_discord_notification())
    print("Discord 알림 모듈 로드 완료")
