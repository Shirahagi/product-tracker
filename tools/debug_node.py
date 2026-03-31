import asyncio
from asyncua import Client

async def browse_nodes():
    url = "opc.tcp://127.0.0.1:49320"
    async with Client(url=url) as client:
        print("已连接 KEPServer，正在抓取全线标签...")
        
        # 这里的路径是根据你的截图拼写的
        # 我们直接尝试寻找 DemoPLC 下的所有标签
        # 格式：ns=?;s=SiemensPLC.DemoPLC.标签名
        
        # 我们先通过名称搜索
        search_path = "SiemensPLC.DemoPLC.S1_Trigger"
        
        # 尝试遍历 namespace 寻找真正的 ns 索引
        for ns_idx in range(1, 5):
            node_id = f"ns={ns_idx};s={search_path}"
            try:
                node = client.get_node(node_id)
                val = await node.get_value()
                print(f"\n找到了！正确的 Node ID 格式是: {node_id}")
                print(f"当前实时值: {val}")
                return ns_idx
            except:
                continue
        
        print("\n自动匹配失败。请检查：")
        print("1. KEPServer 里的 [SiemensPLC] 通道名和 [DemoPLC] 设备名是否带了空格？")
        print("2. 确认已经点击了右下角小灯泡的 [重新初始化 (Reinitialize)]。")

if __name__ == "__main__":
    asyncio.run(browse_nodes())