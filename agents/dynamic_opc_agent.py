import asyncio
import requests
from asyncua import Client, ua

# ================= 配置区 =================
OPC_URL = "opc.tcp://127.0.0.1:49320"
# 指向刚才测试成功的配置接口
CONFIG_API = "http://127.0.0.1:8000/api/config/"
# 业务处理接口基地址
BASE_API = "http://127.0.0.1:8000/api"
# ==========================================

async def station_worker(name, cfg, client):
    """通用的工位监控引擎"""
    print(f" [{name}] 监控单元已启动 (类型: {cfg['type']})")
    
    # 从配置中获取标签路径
    try:
        node_trigger = client.get_node(cfg["tags"]["trigger"])
        node_barcode = client.get_node(cfg["tags"]["barcode"])
        node_action = None
        if cfg["tags"].get("action"):
            node_action = client.get_node(cfg["tags"]["action"])
    except Exception as e:
        print(f" [{name}] 标签路径错误: {e}")
        return

    last_trigger = False

    while True:
        try:
            current_trigger = await node_trigger.read_value()
            
            if current_trigger and not last_trigger:
                barcode = str(await node_barcode.read_value()).strip()
                if not barcode:
                    print(f" [{name}] 拦截：空码")
                else:
                    print(f"\n [{name}] 扫码触发: [{barcode}]")
                    
                    if cfg["type"] == "entry":
                        requests.get(f"{BASE_API}/simulate/?barcode={barcode}", timeout=3)
                        print(f"   -> [起点] 网页弹窗信号已发送")
                        
                    elif cfg["type"] == "sorting":
                        res = requests.post(f"{BASE_API}/sorting-logic/", json={
                            "barcode": barcode, "station_id": cfg["station_id"]
                        }, timeout=3)
                        action = 2 if res.json().get('should_divert') else 1
                        if node_action:
                            await node_action.write_value(ua.DataValue(ua.Variant(action, ua.VariantType.Int16), 
                                                                    SourceTimestamp=None, ServerTimestamp=None))
                        print(f"   -> [分流 {cfg['station_id']}] 决策下发: {action}")
                        
                    elif cfg["type"] == "exit":
                        requests.post(f"{BASE_API}/sorting-logic/", json={
                            "barcode": barcode, "station_id": "EXIT"
                        }, timeout=3)
                        print(f"   -> [下线] 货物已清理")

                # 复位信号
                await node_trigger.write_value(ua.DataValue(ua.Variant(False, ua.VariantType.Boolean), 
                                                           SourceTimestamp=None, ServerTimestamp=None))

            last_trigger = current_trigger
        except Exception as e:
            print(f" [{name}] 通讯异常: {e}")
            
        await asyncio.sleep(0.1)

async def main():
    # 1. 获取动态配置
    print(" 正在从后端获取产线配置...")
    try:
        response = requests.get(CONFIG_API, timeout=5)
        lines = response.json()
    except Exception as e:
        print(f" 无法获取配置: {e}")
        return

    # 2. 连接 OPC UA
    client = Client(url=OPC_URL)
    client.application_uri = "urn:python:asyncua:client"
    
    try:
        async with client:
            print(" 已连接至 KEPServer")
            
            workers = []
            for line in lines:
                for st in line["stations"]:
                    worker_name = f"{line['name']}-{st['name']}"
                    workers.append(station_worker(worker_name, st, client))
            
            if not workers:
                print(" 警告：数据库中没有配置任何工位，请先在 Admin 后台录入！")
                return

            print(f" 成功加载 {len(workers)} 个监控任务，全线开启监控...")
            await asyncio.gather(*workers)
    except Exception as e:
        print(f" 连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())