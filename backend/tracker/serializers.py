from rest_framework import serializers
from .models import Item, ScanRecord

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'barcode', 'name', 'last_channel', 'updated_at']