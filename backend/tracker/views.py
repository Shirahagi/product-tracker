from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Item, ScanRecord, RoutingRule
from .serializers import ItemSerializer

@api_view(['GET'])
def get_items(request):
    items = Item.objects.all().order_by('-updated_at')
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def process_scan(request):
    barcode = request.data.get('barcode', '')

    # 1. 业务逻辑判定：尝试匹配规则
    # 逻辑：找出数据库中哪个“前缀”是当前条码的开头
    rule = RoutingRule.objects.filter(code_prefix__in=[barcode[:i] for i in range(len(barcode), 0, -1)]).first()
    
    # 如果没匹配到规则，默认返回 "人工分拣"
    target_channel = rule.target_channel if rule else "人工分拣"

    # 2. 正常数据库更新逻辑
    item, created = Item.objects.get_or_create(barcode=barcode)
    item.save()

    # 记录扫码信息
    ScanRecord.objects.create(item=item, target_channel=target_channel)

    # 3. 把 target_channel 一起返回给前端
    return Response({
        'message': '扫码成功',
        'target_channel': target_channel, # 前端将根据此字段控制转向
        'item': ItemSerializer(item).data
    })