import requests
import time

# 定义两个不同的接口地址
BASE_URL = "http://127.0.0.1:8000/api"
URL_MANUAL = f"{BASE_URL}/manual-scan/"   # 员工起点录入
URL_SORTING = f"{BASE_URL}/sorting-logic/" # 产线机器自动判定

def run_agent():
    print("1: 模拟起点员工")
    print("2: 模拟 1 号分流口 (负责 A)")
    print("3: 模拟 2 号分流口 (负责 B)")
    print("4: 模拟 3 号分流口 (负责 C)")
    
    mode = input("选择角色: ")

    while True:
        barcode = input("扫码: ").strip()
        if mode == '1':
            requests.get(f"http://127.0.0.1:8000/api/simulate/?barcode={barcode}")
        else:
            # 角色 2 对应 station_id "1", 角色 3 对应 "2"...
            station_id = str(int(mode) - 1) 
            res = requests.post("http://127.0.0.1:8000/api/sorting-logic/", 
                                json={"barcode": barcode, "station_id": station_id})
            print(f"分流口 {station_id} 决策: {res.json()['should_divert']}")

if __name__ == "__main__":
    run_agent()