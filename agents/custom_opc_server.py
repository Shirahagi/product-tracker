import asyncio
import requests
from asyncua import Server, ua

DJANGO_BASE_URL = "http://127.0.0.1:8000/api"

async def monitor_station(name, trigger_node, barcode_node, action_node, api_url, station_id=None):
    """通用的工位监控引擎（无论是起点还是分流口，全靠这个引擎驱动）"""
    print(f" [{name}] 监控单元已启动...")
    last_trigger = False

    while True:
        try:
            current_trigger = await trigger_node.read_value()
            
            # 检测到上升沿（从 0 变 1）
            if current_trigger and not last_trigger:
                raw_barcode = await barcode_node.read_value()
                barcode = str(raw_barcode).strip()

                if not barcode:
                    print(f" [{name}] 拦截：条码为空！")
                else:
                    print(f"\n [{name}] 扫码触发,条码: [{barcode}]")
                    
                    # === 业务分发逻辑 ===
                    if name == "ENTRY":
                        # 起点站：调用模拟弹窗接口
                        res = requests.get(f"{api_url}?barcode={barcode}", timeout=3)
                        print(f"   ->  [起点] 网页弹窗信号已发送！")
                        
                    elif name == "EXIT":
                        # 下线站：调用分流接口，传 EXIT
                        res = requests.post(api_url, json={"barcode": barcode, "station_id": "EXIT"}, timeout=3)
                        print(f"   ->  [下线] 货物已从数据库清理！")
                        
                    else:
                        # 分流口 1, 2, 3：调用判定接口
                        res = requests.post(api_url, json={"barcode": barcode, "station_id": station_id}, timeout=3)
                        should_divert = res.json().get('should_divert', False)
                        action_val = 2 if should_divert else 1
                        
                        # 把动作指令写回 OPC，供外部 PLC 读取
                        await action_node.write_value(ua.DataValue(ua.Variant(action_val, ua.VariantType.Int16)))
                        print(f"   ->  [分流 {station_id}] 决策下发：{'转向 (2)' if should_divert else '放行 (1)'}")

                # 无论如何，执行完毕后复位触发信号 (变回 0)
                await trigger_node.write_value(False)

            last_trigger = current_trigger
        except Exception as e:
            print(f" [{name}] 运行异常: {e}")
            
        await asyncio.sleep(0.1) # 100ms 极速轮询

async def run_gateway():
    print(" 正在初始化 [全线] OPC UA 工业网关...")
    opc_server = Server()
    await opc_server.init()
    opc_server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    
    # 允许外部任意写入（解决之前的权限痛点）
    opc_server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
    opc_server.allow_remote_admin(True)
    
    idx = await opc_server.register_namespace("http://myfactory.local")
    my_device = await opc_server.nodes.objects.add_object(idx, "ProductionLine")
    
    # ========================================================
    # 批量创建全线标签 (Tags) 并开放写权限
    # ========================================================
    nodes = {}
    # 定义我们要创建的工位：(工位前缀, 是否需要返回值)
    stations_config =[
        ("Entry", False),   # 起点
        ("S1", True),       # 分流 1
        ("S2", True),       # 分流 2
        ("S3", True),       # 分流 3
        ("Exit", False)     # 终点
    ]

    for prefix, needs_action in stations_config:
        # 创建 Trigger 和 Barcode
        t_node = await my_device.add_variable(idx, f"{prefix}_Trigger", False, varianttype=ua.VariantType.Boolean)
        b_node = await my_device.add_variable(idx, f"{prefix}_Barcode", "", varianttype=ua.VariantType.String)
        await t_node.set_writable()
        await b_node.set_writable()
        nodes[f"{prefix}_Trigger"] = t_node
        nodes[f"{prefix}_Barcode"] = b_node
        
        # 如果需要返回值（分流口），则创建 Action 标签
        if needs_action:
            a_node = await my_device.add_variable(idx, f"{prefix}_Action", 0, varianttype=ua.VariantType.Int16)
            await a_node.set_writable()
            nodes[f"{prefix}_Action"] = a_node

    # ========================================================
    # 启动全线监控任务 (并发运行)
    # ========================================================
    async with opc_server:
        print(" OPC UA 服务器已启动！监听地址: opc.tcp://0.0.0.0:4840\n")
        
        # 把五个监控任务打包，一起丢进后台运行
        await asyncio.gather(
            monitor_station("ENTRY", nodes["Entry_Trigger"], nodes["Entry_Barcode"], None, f"{DJANGO_BASE_URL}/simulate/"),
            monitor_station("DIVERTER_1", nodes["S1_Trigger"], nodes["S1_Barcode"], nodes["S1_Action"], f"{DJANGO_BASE_URL}/sorting-logic/", "1"),
            monitor_station("DIVERTER_2", nodes["S2_Trigger"], nodes["S2_Barcode"], nodes["S2_Action"], f"{DJANGO_BASE_URL}/sorting-logic/", "2"),
            monitor_station("DIVERTER_3", nodes["S3_Trigger"], nodes["S3_Barcode"], nodes["S3_Action"], f"{DJANGO_BASE_URL}/sorting-logic/", "3"),
            monitor_station("EXIT", nodes["Exit_Trigger"], nodes["Exit_Barcode"], None, f"{DJANGO_BASE_URL}/sorting-logic/")
        )

if __name__ == "__main__":
    asyncio.run(run_gateway())