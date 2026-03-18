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

    item, _ = Item.objects.get_or_create(barcode=barcode)
    
    # 锁定这件货的目标，不管它以后经过哪个口，都以这个为准
    item.intended_target = target_channel 
    item.last_channel = f"初始登记：去往通道 {target_channel}"
    item.save()

    ScanRecord.objects.create(item=item, target_channel=item.last_channel)
    return Response({'message': '登记成功', 'target_channel': target_channel})
from django.shortcuts import get_object_or_404

@api_view(['POST'])
def update_item_channel(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    new_channel = request.data.get('target_channel')

    # 1. 修改最高优先级的指令字段
    item.intended_target = new_channel 
    
    # 2. 记录是谁在什么时间手动改了路径
    item.last_channel = f"人工干预：强制重导向至 {new_channel}"
    item.save()
    
    # 3. 写入日志，方便以后扯皮（证明是人改的，不是机器出错）
    ScanRecord.objects.create(
        item=item, 
        target_channel=f"【紧急修改】目标改为 {new_channel}"
    )

    # 4. 模拟下发机械指令 (如果是给总线发信号的话)
    print(f"!!! 紧急干预成功 !!! 货物 {item.barcode} 目标已修正为 {new_channel}")

    return Response({
        'message': '路径已实时修正', 
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
    station_id = str(request.data.get('station_id')) # 当前分流口编号，如 "1"

    # 获取货物对象
    item, _ = Item.objects.get_or_create(barcode=barcode)

    # 1. 判定逻辑：优先使用预定目标（支持“反悔”逻辑），如果没有则匹配自动规则
    if item.intended_target:
        target = item.intended_target
    else:
        # 自动匹配规则
        rule = RoutingRule.objects.filter(
            code_prefix__in=[barcode[:i] for i in range(len(barcode), 0, -1)]
        ).first()
        target = rule.target_channel if rule else "未知"
        # 补全预定目标，防止后续路段重复计算
        item.intended_target = target
        item.save()

    # 2. 判断当前口是否匹配目标通道
    should_divert = (target == station_id)
    action_text = "转向" if should_divert else "放行"
    
    # 3. 构造统一的状态描述字符串（只构造一次！）
    # 例子：分流口 1: 转向 (目标:1)
    status_msg = f"分流口 {station_id}: {action_text} (目标: {target})"

    # 4. 更新数据库状态 (Item)
    item.last_channel = status_msg
    item.save()

    # 5. 记录历史日志 (ScanRecord) - 只存一次！
    ScanRecord.objects.create(
        item=item, 
        target_channel=status_msg
    )

    # 6. 通过 WebSocket 通知前端刷新表格
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'scan_group',
        {
            'type': 'send_scan_signal',
            'message': {'refresh_table': True}
        }
    )

    # 7. 返回给机械端的指令
    return Response({
        "should_divert": should_divert,
        "target_channel": target,
        "action": action_text
    })