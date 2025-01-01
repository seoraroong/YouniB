from django.urls import re_path
from myproject import consumers
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from myproject.consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<user_id>\d+)/$', NotificationConsumer.as_asgi()),
]
