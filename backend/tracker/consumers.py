import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ScanConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 当 Vue 前端连接时，把这个连接加入到一个名叫 "scan_group" 的广播组
        self.room_group_name = 'scan_group'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept() # 接受连接
        print(" 前端大屏已通过 WebSocket 接入产线系统！")

    async def disconnect(self, close_code):
        # 断开连接时，移出广播组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(" 前端大屏已断开连接。")

    # 这个函数专门用来接收后端发来的广播，并推给前端
    async def send_scan_signal(self, event):
        message = event['message']
        # 通过 WebSocket 把 JSON 数据推给 Vue
        await self.send(text_data=json.dumps(message))