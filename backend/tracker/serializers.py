from rest_framework import serializers
from .models import Item, ScanRecord

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'