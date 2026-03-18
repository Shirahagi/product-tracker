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
                         <!-- 如果正在编辑，显示输入框；否则显示文字 -->
                          <div v-if="item.isEditing">
                            <input v-model="item.editChannel" />
                          </div>
                        <div v-else>
                            {{ item.last_channel }}
                        </div>
                      </td>
                        <td>{{ new Date(item.updated_at).toLocaleString() }}</td>
                        <td>
                          <div v-if="item.isEditing">
                            <button @click="saveEdit(item)">保存</button>
                            <button @click="cancelEdit(item)">取消</button>
                          </div>
                          <div v-else>
                            <button @click="item.isEditing = true">✏️ 编辑</button>
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


import { ref, onMounted, onUnmounted, nextTick } from 'vue' // 确保引入 onUnmounted
import axios from 'axios'
// Django 后端的地址
const API_BASE_URL = 'http://127.0.0.1:8000/api'

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


// ====== 新增 WebSocket 连接逻辑 ======
let ws = null

const connectWebSocket = () => {
  // 连接后端的 WebSocket 频道
  ws = new WebSocket('ws://127.0.0.1:8000/ws/scan/')

  ws.onopen = () => {
    console.log('🔗 WebSocket 连接成功！')
  }

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  if (data.refresh_table) {
    fetchItems()
  } else {
    modalScanInput.value = data.barcode
    // 自动预选后端建议的通道 (比如 "1")
    selectedChannel.value = data.target_channel 
    showScanModal.value = true
  }
}

  ws.onclose = () => {
    console.log('❌ WebSocket 断线，1秒后尝试重连...')
    setTimeout(connectWebSocket, 1000) // 工业级断线重连机制
  }
}

// 在组件挂载时，启动 WebSocket
onMounted(() => {
  fetchItems()
  fetchChannels()
  connectWebSocket() // <--- 加上这一行
})

// 组件挂载时，启动全局监听
onMounted(() => {
  fetchItems()
  fetchChannels()
})

// 组件销毁时，移除监听（好习惯，防止内存泄漏）
onUnmounted(() => {
})
// 获取货物列表
const fetchItems = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/items/?barcode=${searchQuery.value}`)
    items.value = response.data.map(item => ({
      ...item,
      isEditing: false,
      editChannel: item.last_channel
    }))
  } catch (error) {
    console.error('获取货物列表失败:', error)
  }
}

// 获取分流通道列表
const fetchChannels = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/channels/`)
    channels.value = response.data
  } catch (error) {
    console.error('获取通道列表失败:', error)
  }
}

// 处理扫码
const handleScan = async () => {
  if (!scanInput.value.trim()) {
    alert('请输入条码')
    return
  }

  // 弹出弹窗，预填条码
  showScanModal.value = true
  modalScanInput.value = scanInput.value
  scanInput.value = ''
}

// 手动输入
const openManualScan = () => {
  showScanModal.value = true
  modalScanInput.value = ''
  selectedChannel.value = ''
}

// 确认扫码
const confirmScan = async () => {
  if (!modalScanInput.value.trim() || !selectedChannel.value) {
    alert('请输入条码和选择通道')
    return
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/manual-scan/`, {
      barcode: modalScanInput.value.trim(),
      target_channel: selectedChannel.value
    })

    alert(`扫码成功！请前往: ${response.data.target_channel}`)
    showScanModal.value = false
    modalScanInput.value = ''
    selectedChannel.value = ''
    await fetchItems()
  } catch (error) {
    console.error('扫码处理失败:', error)
    alert('扫码处理失败，请重试')
  }
}

// 关闭扫码弹窗
const closeScanModal = () => {
  showScanModal.value = false
  modalScanInput.value = ''
  selectedChannel.value = ''
}
// 保存编辑的分流通道
const saveEdit = async (item) => {
  if (!item.editChannel || !item.editChannel.trim()) {
    alert('请输入有效的分流通道')
    return
  }
  
  try {
    const response = await axios.post(`${API_BASE_URL}/update-channel/${item.id}/`, {
      target_channel: item.editChannel.trim()
    })
    item.isEditing = false
    item.last_channel = response.data.item.last_channel // 用返回的数据更新
    alert('机械指令已下发！')
  } catch (e) {
    console.error('更新失败:', e)
    alert('更新失败: ' + (e.response?.data?.detail || '请重试'))
  }
}

// 取消编辑
const cancelEdit = (item) => {
  item.isEditing = false
  item.editChannel = item.last_channel
}

// 查看日志
const viewLogs = async (item) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/item-logs/${item.id}/`)
    currentLogItem.value = { barcode: response.data.barcode }
    logs.value = response.data.logs
    showLogModal.value = true
  } catch (error) {
    console.error('获取日志失败:', error)
    alert('获取日志失败，请重试')
  }
}

// 关闭日志模态框
const closeLogModal = () => {
  showLogModal.value = false
  currentLogItem.value = null
  logs.value = []
}

// 组件挂载时获取数据
onMounted(() => {
  fetchItems()
  fetchChannels()
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