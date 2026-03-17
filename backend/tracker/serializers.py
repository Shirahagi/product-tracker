from rest_framework import serializers
from .models import Item, ScanRecord

class ItemSerializer(serializers.ModelSerializer):
    last_channel = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ['id', 'barcode', 'name', 'last_channel', 'updated_at']

    def get_last_channel(self, obj):
        # 获取该物品最新的扫码记录的分流通道
        latest_scan = obj.scan_records.order_by('-scanned_at').first()
        return latest_scan.target_channel if latest_scan else '未分流'