from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Item, ScanRecord, RoutingRule
from .serializers import ItemSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@api_view(['GET'])
def get_items(request):
    # 1. 尝试从请求网址中获取 '?barcode=xxx' 的参数
    search_barcode = request.GET.get('barcode', '')

    # 2. 根据是否有搜索词来决定查询方式
    if search_barcode:
        items = Item.objects.filter(barcode__icontains=search_barcode).order_by('-updated_at')
    else:
        items = Item.objects.all().order_by('-updated_at')
        
    # 3. 翻译并返回
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def manual_scan(request):
    barcode = request.data.get('barcode', '')
    target_channel = request.data.get('target_channel', '')

    if not barcode or not target_channel:
        return Response({'error': '条码和目标通道不能为空'}, status=400)

    # 2. 正常数据库更新逻辑
    item, created = Item.objects.get_or_create(barcode=barcode)
    item.last_channel = target_channel  # 更新最近分流通道
    item.save()

    # 记录扫码信息
    ScanRecord.objects.create(item=item, target_channel=target_channel)

    # 3. 把 target_channel 一起返回给前端
    return Response({
        'message': '手动扫码成功',
        'target_channel': target_channel,
        'item': ItemSerializer(item).data
    })
from django.shortcuts import get_object_or_404

@api_view(['POST'])
def update_item_channel(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    new_channel = request.data.get('target_channel')

    # 1. 保存到数据库
    item.last_channel = new_channel
    item.save()
    
    # 2. 创建扫码记录（机械指令触发的记录）
    ScanRecord.objects.create(item=item, target_channel=new_channel)

    # 3. 模拟触发机械指令
    print(f"[{item.barcode}] 机械指令已下发: 切换至 {new_channel}")

    return Response({
        'message': '更新成功', 
        'new_channel': new_channel,
        'item': ItemSerializer(item).data
    })

@api_view(['GET'])
def get_item_logs(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    scan_records = item.scan_records.all().order_by('-scanned_at')
    logs = [
        {
            'id': record.id,
            'target_channel': record.target_channel,
            'scanned_at': record.scanned_at.isoformat(),
        }
        for record in scan_records
    ]
    return Response({
        'barcode': item.barcode,
        'logs': logs
    })

@api_view(['GET'])
def get_routing_channels(request):
    channels = RoutingRule.objects.values_list('target_channel', flat=True).distinct()
    return Response(list(channels))

@api_view(['GET'])
def simulate_hardware(request):
    simulated_barcode = request.GET.get('barcode')
    # 1. 根据 A/B/C 开头算出 1/2/3 通道
    rule = RoutingRule.objects.filter(
        code_prefix__in=[simulated_barcode[:i] for i in range(len(simulated_barcode), 0, -1)]
    ).first()
    target = rule.target_channel if rule else ""

    # 2. 推送给网页
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'scan_group',
        {
            'type': 'send_scan_signal',
            'message': {
                'barcode': simulated_barcode,
                'target_channel': target, # 这里会传 "1"
                'refresh_table': False
            }
        }
    )
    return Response({"status": "已发送"})

@api_view(['POST'])
def sorting_logic(request):
    barcode = request.data.get('barcode')
    station_id = str(request.data.get('station_id')) # 当前是哪个分流口在扫码

    # 1. 查找规则：这件货应该去哪个通道？
    rule = RoutingRule.objects.filter(
        code_prefix__in=[barcode[:i] for i in range(len(barcode), 0, -1)]
    ).first()
    target = rule.target_channel if rule else "未知"

    # 2. 判定逻辑：当前分流口是否需要执行“转向”动作
    should_divert = (target == station_id)
    action_text = "转向" if should_divert else "放行"

    # 3. 获取或创建货物对象
    item, _ = Item.objects.get_or_create(barcode=barcode)

    # 4. 核心：构造一条描述性的日志信息
    # 例如："分流口 1: 转向" 或 "分流口 1: 放行"
    log_status = f"分流口 {station_id}: {action_text}"

    # 5. 更新 Item 的最新状态
    item.last_channel = log_status
    item.save()

    # 6. 【关键步骤】写入日志表 (ScanRecord)
    # 这样用户点击“查看日志”时，就能看到这一行了
    ScanRecord.objects.create(
        item=item,
        target_channel=log_status  # 将动作描述存入日志
    )

    # 7. 通过 WebSocket 通知前端刷新表格
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'scan_group',
        {
            'type': 'send_scan_signal',
            'message': {'refresh_table': True}
        }
    )

    return Response({
        "should_divert": should_divert,
        "target_channel": target,
        "action": action_text
    })