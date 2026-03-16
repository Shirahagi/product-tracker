from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Item, ScanRecord
from .serializers import ItemSerializer

@api_view(['GET'])
def get_items(request):
    items = Item.objects.all().order_by('-updated_at')
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def process_scan(request):
    barcode = request.data.get('barcode')
    station = request.data.get('station', '默认工位')

    if not barcode:
        return Response({'error': '条码不能为空'}, status=400)

    # 查找或创建货物
    item, created = Item.objects.get_or_create(barcode=barcode)
    
    # 更新货物当前位置
    item.current_station = station
    item.save()

    # 记录此次扫码事件
    ScanRecord.objects.create(item=item, station_name=station)

    return Response({
        'message': '扫码成功',
        'item': ItemSerializer(item).data,
        'is_new': created
    })