from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"user_{self.user_id}"

        logger.debug(f"WebSocket 연결 요청: user_id={self.user_id}, group_name={self.group_name}")

        try:
            # 그룹에 추가
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            logger.debug(f"WebSocket 연결 성공: user_id={self.user_id}, group_name={self.group_name}")
        except Exception as e:
            logger.error(f"WebSocket 연결 실패: user_id={self.user_id}, 오류={e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            # 그룹에서 제거
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.debug(f"WebSocket 연결 종료: user_id={self.user_id}, group_name={self.group_name}")
        except Exception as e:
            logger.error(f"WebSocket 연결 종료 중 오류 발생: user_id={self.user_id}, 오류={e}")

    # 알림 처리
    async def user_notification(self, event):
        try:
            message = event.get("message", "")
            
            # 메시지 전송
            await self.send(text_data=json.dumps({
                "message": message,
            }))
            logger.debug(f"알림 전송 성공: user_id={self.user_id}, message={message}")
        except Exception as e:
            logger.error(f"알림 전송 실패: user_id={self.user_id}, 오류={e}")
