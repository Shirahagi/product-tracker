<template>
  <div class="container">
    <h1>产线</h1>
    <div class="main-layout">
      <!-- 右侧面板 -->
      <div class="full-panel">
        <div class="data-table">
  <h2>实时货物状态</h2>
  
  <div style="margin-bottom: 15px; display: flex; gap: 15px; align-items: center;">
    <!-- 保留手动触发按钮 -->
    <button @click="openManualScan" style="padding: 10px 20px; background: #2c3e50; color: white; border: none; cursor: pointer; font-size: 16px; font-weight: bold; border-radius: 4px;">
      ✋ 手动录入
    </button>
    
    <span style="color: #7f8c8d; font-size: 14px;">
      💡 提示：无需点击任何地方，直接使用扫码枪扫码即可自动弹出确认框。
    </span>
  </div>

          
          <!-- 搜索区 -->
          <div class="search-bar" style="margin-bottom: 15px; display: flex; gap: 10px;">
            <input 
              type="text" 
              v-model="searchQuery" 
              @keyup.enter="fetchItems" 
              placeholder="输入条码搜索..."
              style="padding: 8px; border: 1px solid #2c3e50; width: 200px;"
            />
            <button @click="fetchItems" style="padding: 8px 15px; background: #2c3e50; color: white; border: none; cursor: pointer;">
              搜索
            </button>
            <button @click="searchQuery=''; fetchItems()" style="padding: 8px 15px; background: #95a5a6; color: white; border: none; cursor: pointer;">
              重置
            </button>
          </div>
                <table>
                  <thead>
                    <tr>
                      <th>二维码</th>
                      <th>当前分流通道</th>
                      <th>最后更新时间</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in items" :key="item.id">
                      <td>{{ item.barcode }}</td>
                      <td>
                        <!-- 如果正在编辑，显示下拉选择框 -->
                        <div v-if="item.isEditing">
                          <select v-model="item.editChannel" style="padding: 4px;">
                            <option value="">请选择目标</option>
                            <option v-for="c in channels" :key="c" :value="c">{{ c }}</option>
                          </select>
                          <button @click="saveEdit(item)">保存</button>
                          <button @click="cancelEdit(item)">取消</button>
                        </div>
                        <!-- 正常状态显示最近状态文字 -->
                        <div v-else>
                          {{ item.last_channel }}
                        </div>
                      </td>
                      <td>{{ new Date(item.updated_at).toLocaleString() }}</td>
                      <td>
                        <div v-if="!item.isEditing">
                          <button @click="startEdit(item)">✏️ 编辑</button>
                          <button @click="viewLogs(item)">📋 查看日志</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 日志模态框 -->
              <div v-if="showLogModal" class="modal" @click="closeLogModal">
                <div class="modal-content" @click.stop>
                  <span class="close" @click="closeLogModal">&times;</span>
                  <h2>日志记录 - {{ currentLogItem.barcode }}</h2>
                  <div v-if="logs.length === 0" class="no-logs">
                    暂无日志记录
                  </div>
                  <ul v-else class="log-list">
                    <li v-for="log in logs" :key="log.id">
                      <strong>{{ log.target_channel }}</strong> - {{ new Date(log.scanned_at).toLocaleString() }}
                    </li>
                  </ul>
                </div>
              </div>

              <!-- 扫码弹窗 -->
<div v-if="showScanModal" class="modal" @click="closeScanModal">
  <div class="modal-content" @click.stop>
    <span class="close" @click="closeScanModal">&times;</span>
    <h2>条码确认与分流</h2>
    
    <!-- 这里的 input 只是用来显示或手动修改，去掉 @keyup.enter -->
    <input 
      type="text" 
      v-model="modalScanInput" 
      placeholder="扫码结果或手动输入"
      style="width: 100%; padding: 10px; margin-bottom: 15px; font-size: 18px; font-weight: bold; color: #2c3e50;"
    />
    
    <!-- 通道选择保留 -->
    <h3>选择分流道路</h3>
    <select v-model="selectedChannel" style="width: 100%; padding: 10px; margin-bottom: 20px; font-size: 16px;">
      <option value="">请确认通道...</option>
      <option v-for="channel in channels" :key="channel" :value="channel">{{ channel }}</option>
    </select>
    
    <!-- 强制必须点击这个按钮才能提交 -->
    <div style="display: flex; gap: 10px; justify-content: center;">
      <button @click="confirmScan" style="padding: 12px 30px; background: #2c3e50; color: #f1c40f; border: none; cursor: pointer; font-size: 18px; font-weight: bold;">
        ✅ 确认并下发指令
      </button>
      <button @click="closeScanModal" style="padding: 12px 30px; background: #e74c3c; color: white; border: none; cursor: pointer; font-size: 18px; font-weight: bold;">
        ❌ 取消
      </button>
    </div>
  </div>
</div>
            </div>
          </div>
  </div>
</template>
<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'

// Django 后端的地址
const serverIP = window.location.hostname;
const API_BASE_URL = `http://${serverIP}:8000/api`

// 响应式数据
const items = ref([])
const scanInput = ref('')
const scannerInput = ref(null)
const targetChannel = ref('')
const searchQuery = ref('')
const showLogModal = ref(false)
const currentLogItem = ref(null)
const logs = ref([])
const showScanModal = ref(false)
const modalScanInput = ref('')
const selectedChannel = ref('')
const channels = ref([])

// ====== WebSocket 逻辑 ======
let ws = null
const connectWebSocket = () => {
  ws = new WebSocket(`ws://${serverIP}:8000/ws/scan/`)
  ws.onopen = () => console.log('🔗 WebSocket 连接成功！')
  ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // 1. 如果是产线机器自动扫码发来的更新信号（不涉及人工确认）
  if (data.refresh_table) {
    fetchItems();
    return;
  }

  // 2. 员工位扫码逻辑
  if (showScanModal.value) {
    // 【弹窗已打开的情况】
    console.log('检测到第二次扫码，正在比对...');
    
    // 检查第二次扫码的内容是否与第一次一致
    if (data.barcode && data.barcode === modalScanInput.value) {
      console.log('条码一致，执行自动确认...');
      confirmScan(); // 自动调用确认函数，就像点击了确定按钮一样
    } else {
      console.log('条码不匹配或为空，忽略本次扫码，保持原有弹窗。');
      // 不做任何操作，弹窗不关闭，数据不更新
    }
  } else {
    // 【弹窗未打开的情况】
    console.log('检测到第一次扫码，打开弹窗...');
    modalScanInput.value = data.barcode;
    // 自动预选后端建议的通道
    selectedChannel.value = data.target_channel;
    showScanModal.value = true;
  }
};
  ws.onclose = () => {
    console.log('❌ WebSocket 断线，1秒后重连...')
    setTimeout(connectWebSocket, 1000)
  }
}

// ====== 数据获取逻辑 ======
const fetchItems = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/items/?barcode=${searchQuery.value}`)
    items.value = response.data.map(item => ({
      ...item,
      isEditing: false,
      // 【关键修改】：编辑框初始化使用 intended_target (纯数字/代号)，而不是 last_channel (长句子)
      editChannel: item.intended_target 
    }))
  } catch (error) {
    console.error('获取货物列表失败:', error)
  }
}

const fetchChannels = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/channels/`)
    channels.value = response.data
  } catch (error) {
    console.error('获取通道列表失败:', error)
  }
}

// ====== 编辑逻辑 ======
const startEdit = (item) => {
  item.isEditing = true
  // 确保点开编辑时，框里是干净的通道号
  item.editChannel = item.intended_target 
}

const cancelEdit = (item) => {
  item.isEditing = false
}

const saveEdit = async (item) => {
  if (!item.editChannel) {
    alert('请选择有效的分流通道')
    return
  }
  try {
    const response = await axios.post(`${API_BASE_URL}/update-channel/${item.id}/`, {
      target_channel: item.editChannel
    })
    item.isEditing = false
    alert('路径已实时修正，机械指令下发！')
    await fetchItems() // 重新获取数据刷新视图
  } catch (e) {
    console.error('更新失败:', e)
    alert('更新失败，请重试')
  }
}

// ====== 扫码/弹窗逻辑 ======
const openManualScan = () => {
  showScanModal.value = true
  modalScanInput.value = ''
  selectedChannel.value = ''
}

const confirmScan = async () => {
  if (!modalScanInput.value.trim() || !selectedChannel.value) {
    // 如果是第二次扫码自动触发，但通道还没选（比如规则库里没匹配到），则不能确认
    alert('请先选择分流通道再确认'); 
    return;
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/manual-scan/`, {
      barcode: modalScanInput.value.trim(),
      target_channel: selectedChannel.value
    });

    showScanModal.value = false; // 关键：确认后关闭弹窗
    await fetchItems();
    console.log(`条码 ${modalScanInput.value} 已自动确认并存库`);
    
    // 可选：加一个简短的通知，而不是 alert（alert 会阻塞操作）
    //notify(`登记成功！去往通道: ${selectedChannel.value}`);
  } catch (error) {
    alert('确认失败，请重试');
  }
};

const closeScanModal = () => {
  showScanModal.value = false
}

// ====== 日志逻辑 ======
const viewLogs = async (item) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/item-logs/${item.id}/`)
    currentLogItem.value = { barcode: response.data.barcode }
    logs.value = response.data.logs
    showLogModal.value = true
  } catch (error) {
    alert('获取日志失败')
  }
}

const closeLogModal = () => {
  showLogModal.value = false
}

// ====== 生命周期钩子 (只保留一份) ======
onMounted(() => {
  fetchItems()
  fetchChannels()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
.main-layout {
  display: flex;
}

.full-panel {
  width: 100%;
}

.modal {
  position: fixed;
  z-index: 1;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  overflow: auto;
  background-color: rgb(0,0,0);
  background-color: rgba(0,0,0,0.4);
}

.modal-content {
  background-color: #fefefe;
  margin: 15% auto;
  padding: 20px;
  border: 1px solid #888;
  width: 80%;
  max-width: 500px;
}

.close {
  color: #aaa;
  float: right;
  font-size: 28px;
  font-weight: bold;
}

.close:hover,
.close:focus {
  color: black;
  text-decoration: none;
  cursor: pointer;
}
</style>