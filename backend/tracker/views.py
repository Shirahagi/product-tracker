from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Item, ScanRecord, RoutingRule, ItemLog, ProductionLine, Station
from .serializers import ItemSerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
import pandas as pd
from rest_framework.parsers import MultiPartParser
from django.db import transaction

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

# 1. 起点录入
@api_view(['POST'])
def manual_scan(request):
    barcode = request.data.get('barcode', '')
    target_channel = request.data.get('target_channel', '')
    
    if not barcode or not target_channel:
        return Response({'error': '条码和通道不能为空'}, status=400)
    
    item, created = Item.objects.get_or_create(barcode=barcode)
    item.status = 'online'
    item.intended_target = target_channel
    item.current_location = "主通道"
    item.last_channel = f"初始登记：去往通道 {target_channel}"
    item.save()

    # 记录到独立的日志表（即使 Item 被删除，日志仍保留）
    ItemLog.objects.create(
        barcode=barcode,
        action=item.last_channel
    )
    broadcast_refresh()
    return Response({'message': '登记成功', 'item': ItemSerializer(item).data})

@api_view(['POST'])
def update_item_channel(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    new_channel = request.data.get('target_channel')

    if not new_channel:
        return Response({'error': '目标通道不能为空'}, status=400)

    # 1. 修改目标通道
    item.intended_target = new_channel 
    item.last_channel = f"人工干预：强制重导向至 {new_channel}"
    item.save()
    
    # 2. 记录到日志表
    ItemLog.objects.create(
        barcode=item.barcode,
        action=item.last_channel
    )
    
    broadcast_refresh()
    return Response({
        'message': '路径已实时修正', 
        'new_channel': new_channel,
        'item': ItemSerializer(item).data
    })

@api_view(['GET'])
def get_item_logs(request, barcode):
    """查询日志 - 支持已删除的货物（从 ItemLog 表查询）"""
    
    # 从独立的日志表查询（不依赖于 Item 表，即使货物被删除也能查询）
    logs = ItemLog.objects.filter(barcode=barcode).order_by('-scanned_at')
    
    if not logs.exists():
        return Response({
            'barcode': barcode,
            'logs': [],
            'total': 0,
            'message': '暂无日志记录'
        })
    
    log_data = [
        {
            'id': log.id,
            'action': log.action,
            'scanned_at': log.scanned_at.isoformat(),
        } 
        for log in logs
    ]
    
    return Response({
        'barcode': barcode,
        'logs': log_data,
        'total': logs.count()
    })


@api_view(['GET'])
def get_all_logs(request):
    """查询所有日志 - 支持分页"""
    
    log_list = ItemLog.objects.all().order_by('-scanned_at')
    paginator = Paginator(log_list, 20)  # 每页20条

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    log_data = [
        {
            'id': log.id,
            'barcode': log.barcode,
            'action': log.action,
            'scanned_at': log.scanned_at.isoformat(),
        } 
        for log in page_obj
    ]
    
    return Response({
        'logs': log_data,
        'total': paginator.count,
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
    })


@api_view(['GET'])
def get_routing_channels(request):
    channels = RoutingRule.objects.values_list('target_channel', flat=True).distinct()
    return Response(list(channels))

@api_view(['GET'])
def simulate_hardware(request):
    simulated_barcode = request.GET.get('barcode')
    if not simulated_barcode:
        return Response({'error': '条码不能为空'}, status=400)
        
    # 1. 根据条码前缀算出目标通道
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
                'target_channel': target,
                'refresh_table': False
            }
        }
    )
    return Response({"status": "已发送"})


from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Item, ItemLog, RoutingRule # 确保导入了所有模型
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import traceback # 用于打印详细错误

def broadcast_refresh():
    """定义在函数外部或内部均可，确保能被调用"""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'scan_group',
            {'type': 'send_scan_signal', 'message': {'refresh_table': True}}
        )
    except Exception as e:
        print(f"WebSocket 广播失败: {e}")

@api_view(['POST'])
def sorting_logic(request):
    try:
        barcode = request.data.get('barcode')
        st_id = str(request.data.get('station_id'))

        # 1. 获取货物和对应的工位配置
        item, _ = Item.objects.get_or_create(barcode=barcode)
        station_cfg = Station.objects.filter(station_id=st_id).first()
    
        if not station_cfg:
            print(f"⚠️ 收到未定义工位 ID: {st_id}")
            return Response({"error": "未定义的工位"}, status=400)

        # 2. 根据工位类型执行不同逻辑
        
        # --- 场景 A: 下线口 (Exit) ---
        if station_cfg.station_type == 'exit':
            item.status = "offline"
            item.current_location = station_cfg.loc_name_pass # 使用数据库配置的名字，如“已下线”
            item.last_channel = f"到达出口: {station_cfg.name}"
            item.save()
            
            ItemLog.objects.create(barcode=barcode, action="流程结束：货物已下线")
            broadcast_refresh()
            return Response({"should_divert": False, "message": "下线成功"})

        # --- 场景 B: 分流口 (Sorting) ---
        target = item.intended_target
        # 如果货没登记过目标，尝试匹配自动规则
        if not target:
            prefixes = [barcode[:i] for i in range(len(barcode), 0, -1)]
            rule = RoutingRule.objects.filter(code_prefix__in=prefixes).first()
            target = rule.target_channel if rule else "未知"
            item.intended_target = target
            item.save()

        # 核心判定
        should_divert = (str(target) == st_id)

        # 3. 动态位置赋值：彻底干掉 loc_map
        if should_divert:
            item.current_location = station_cfg.loc_name_divert # 数据库读到的“分流 1”
            action_text = "转向"
        else:
            item.current_location = station_cfg.loc_name_pass   # 数据库读到的“通道 1-2”
            action_text = "放行"

        # 4. 保存状态与日志
        status_msg = f"{station_cfg.name}: {action_text} (目标:{target})"
        item.last_channel = status_msg
        item.save()
        ItemLog.objects.create(barcode=barcode, action=status_msg)

        # 5. 广播刷新
        broadcast_refresh()

        return Response({
            "should_divert": should_divert,
            "target_channel": target,
            "action": action_text,
            "current_location": item.current_location
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
def get_system_config(request):
    try:
        # 1. 获取所有产线
        lines = ProductionLine.objects.all()
        config = []
        
        for line in lines:
            line_data = {
                "name": line.name,
                "code": line.code,
                "stations": []
            }
            # 2. 获取该产线下的所有工位
            # 注意：这里的 line.stations 对应 models.py 里的 related_name='stations'
            for st in line.stations.all():
                line_data["stations"].append({
                    "name": st.name,
                    "station_id": st.station_id,
                    "type": st.station_type,
                    "tags": {
                        "trigger": st.tag_trigger,
                        "barcode": st.tag_barcode,
                        "action": st.tag_action
                    }
                })
            config.append(line_data)
        
        
        return Response(config)

    except Exception as e:
        # 如果中间崩了，也必须返回一个 Response
        import traceback
        traceback.print_exc() # 在黑框终端打印错误详情
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
def upload_config(request):
    """通过网页上传 Excel 配置"""
    # 1. 检查是否有文件
    excel_file = request.FILES.get('file')
    if not excel_file:
        return Response({'error': '请选择文件'}, status=400)

    try:
        # 使用事务，确保万一 Excel 报错，数据库不会被改得乱七八糟
        with transaction.atomic():
            # --- 1. 处理分流规则 (Rules Sheet) ---
            df_rules = pd.read_excel(excel_file, sheet_name='Rules')
            df_rules = df_rules.dropna(how='all')
            RoutingRule.objects.all().delete()
            for _, row in df_rules.iterrows():
                prefix = str(row.iloc[0]).strip()
                target = str(row.iloc[1]).strip()
                if '---' in prefix or 'nan' in prefix.lower(): continue
                RoutingRule.objects.create(code_prefix=prefix, target_channel=target)

            # --- 2. 处理产线和工位 (Stations Sheet) ---
            # 重新读取文件（指针重置）
            excel_file.seek(0)
            df_stations = pd.read_excel(excel_file, sheet_name='Stations')
            df_stations = df_stations.dropna(how='all')
            df_stations = df_stations[~df_stations.iloc[:, 0].astype(str).str.contains('---')]

            for line_code, group in df_stations.groupby(df_stations.columns[1]):
                line_name = group.iloc[0, 0]
                line, _ = ProductionLine.objects.update_or_create(
                    code=str(line_code).strip(),
                    defaults={'name': str(line_name).strip()}
                )
                line.stations.all().delete()
                for _, row in group.iterrows():
                    Station.objects.create(
                        line=line,
                        name=str(row.iloc[2]),
                        station_id=str(row.iloc[3]),
                        station_type=str(row.iloc[4]).lower().strip(),
                        tag_trigger=str(row.iloc[5]),
                        tag_barcode=str(row.iloc[6]),
                        tag_action=str(row.iloc[7]) if pd.notna(row.iloc[7]) else None,
                        loc_name_pass=str(row.iloc[8]),
                        loc_name_divert=str(row.iloc[9]) if pd.notna(row.iloc[9]) else ""
                    )

        return Response({'message': '✅ 配置上传并同步成功！系统已根据新规则刷新。'})
    except Exception as e:
        return Response({'error': f'导入失败: {str(e)}'}, status=500)