<template>
  <div class="container">
    <h1>产线货物跟踪系统</h1>
    
    <!-- Tab 导航 -->
    <div class="tab-navigation">
      <button @click="currentTab = 'tracking'" :class="{ 'tab-active': currentTab === 'tracking' }" class="tab-btn">
        实时货物
      </button>
      <button @click="currentTab = 'logs'" :class="{ 'tab-active': currentTab === 'logs' }" class="tab-btn">
        历史日志
      </button>
      <button @click="currentTab = 'settings'" :class="{ 'tab-active': currentTab === 'settings' }" class="tab-btn">
        系统设置
      </button>
    </div>

    <div class="main-layout">
      <!-- ================= 实时货物标签页 ================= -->
      <div v-show="currentTab === 'tracking'" class="full-panel">
        <div class="data-table">
          <h2>实时货物状态（在线货物 {{ onlineItems.length }}）</h2>
          
          <!-- 操作栏 -->
          <div class="action-bar">
            <button @click="openManualScan" class="btn-manual">手动录入</button>
            <div class="global-preset">
              <label>强制预设下发通道：</label>
              <select v-model="globalSelectedChannel" class="select-preset">
                <option value="">-- 跟随系统自动规则 --</option>
                <option v-for="channel in channels" :key="channel" :value="channel">强制去往：{{ channel }}</option>
              </select>
              <button v-if="globalSelectedChannel" @click="globalSelectedChannel = ''" class="btn-clear">清除预设</button>
            </div>
            <span class="hint-text">提示：扫码枪扫码将自动弹出确认框。</span>
          </div>

          <!-- 搜索区 -->
          <div class="search-bar">
            <input type="text" v-model="searchQuery" @keyup.enter="searchAndReset" placeholder="输入条码搜索..." />
            <button @click="searchAndReset" class="btn-search">搜索</button>
            <button @click="searchQuery=''; searchAndReset()" class="btn-reset">重置</button>
          </div>

          <!-- 表格 -->
          <table>
            <thead>
              <tr>
                <th>二维码</th><th>下料通道</th><th>状态</th><th>位置</th><th>上线时间</th><th>更新时间</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in displayedOnlineItems" :key="item.id">
                <td>{{ item.barcode }}</td>
                <td>
                  <div v-if="item.isEditing" class="edit-cell">
                    <select v-model="item.editChannel" class="edit-select">
                      <option value="">请选择通道...</option>
                      <option v-for="channel in channels" :key="channel" :value="channel">{{ channel }}</option>
                    </select>
                  </div>
                  <div v-else>{{ item.intended_target || '未设定' }}</div>
                </td>
                <td><span :class="item.status === 'online' ? 'badge-green' : 'badge-gray'">{{ item.status === 'online' ? '在线' : '下线' }}</span></td>
                <td><span class="location-tag">{{ item.current_location || '未知' }}</span></td>
                <td>{{ new Date(item.created_at).toLocaleString() }}</td>
                <td>{{ new Date(item.updated_at).toLocaleString() }}</td>
                <td>
                  <div v-if="item.isEditing" class="edit-actions">
                    <button @click="saveEdit(item)" class="btn-save">保存</button>
                    <button @click="cancelEdit(item)" class="btn-cancel">取消</button>
                  </div>
                  <div v-else class="view-actions">
                    <button @click="startEdit(item)" v-if="item.status === 'online'" class="btn-edit">编辑</button>
                    <button @click="viewLogs(item)" class="btn-logs">日志</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- 分页导航 -->
          <div class="pagination">
            <button @click="goToPage(1)" :disabled="currentPage === 1">« 首页</button>
            <button @click="prevPage" :disabled="currentPage === 1">‹ 上一页</button>
            <span class="page-info">
              第 <input type="number" v-model.number="currentPage" min="1" :max="totalOnlinePages" style="width: 50px; text-align: center; padding: 4px; border: 1px solid #ddd; border-radius: 3px;" /> 页，共 {{ totalOnlinePages }} 页
            </span>
            <button @click="nextPage" :disabled="currentPage === totalOnlinePages">下一页 ›</button>
            <button @click="goToPage(totalOnlinePages)" :disabled="currentPage === totalOnlinePages">末页 »</button>
            <span class="page-info">显示 {{ displayedOnlineItems.length }} / {{ onlineItems.length }} 条 (每页 {{ itemsPerPage }})</span>
          </div>
        </div>
      </div> 
      <!-- ================= 实时货物标签页 结束 (这个闭合标签非常关键！) ================= -->


      <!-- ================= 历史日志标签页 开始 ================= -->
      <div v-show="currentTab === 'logs'" class="full-panel">
        <div class="log-page">
          <h2>货物历史日志查询</h2>
          
          <div class="log-search-bar">
            <input v-model="logSearchBarcode" placeholder="输入条码查询历史日志..." @keyup.enter="searchLogs" class="log-search-input" />
            <button @click="searchLogs" class="btn-search">查询</button>
            <button @click="clearLogSearch" class="btn-reset">清空</button>
          </div>

          <div v-if="logSearchLoading" class="log-loading">正在查询中...</div>
          <div v-else-if="logSearchResult" class="log-result">
            <h3>条码：{{ logSearchResult.barcode }} - 共 {{ logSearchResult.logs.length }} 条记录</h3>
            <div v-if="logSearchResult.logs && logSearchResult.logs.length === 0" class="no-logs">该条码没有找到任何日志记录</div>
            <ul v-else class="log-list-full">
              <li v-for="log in logSearchResult.logs" :key="log.id" class="log-item">
                <span class="log-time">{{ new Date(log.scanned_at).toLocaleString() }}</span>
                <span class="log-action">{{ log.action }}</span>
              </li>
            </ul>
          </div>
          <div v-else-if="logSearchError" class="log-error">错误 {{ logSearchError }}</div>

          <div v-else>
            <h3>全部货物日志</h3>
            <div v-if="allLogs.length > 0">
              <ul class="log-list-full">
                <li v-for="log in allLogs" :key="log.id" class="log-item">
                  <span class="log-time">{{ new Date(log.scanned_at).toLocaleString() }}</span>
                  <span class="log-barcode" style="font-weight: bold; margin-right: 15px;">【{{ log.barcode }}】</span>
                  <span class="log-action">{{ log.action }}</span>
                </li>
              </ul>
              <div class="pagination" style="margin-top: 20px;">
                <button @click="fetchAllLogs(1)" :disabled="logCurrentPage === 1">« 首页</button>
                <button @click="fetchAllLogs(logCurrentPage - 1)" :disabled="logCurrentPage === 1">‹ 上一页</button>
                <span class="page-info">第 {{ logCurrentPage }} / {{ logTotalPages }} 页 (共 {{ logTotalItems }} 条)</span>
                <button @click="fetchAllLogs(logCurrentPage + 1)" :disabled="logCurrentPage === logTotalPages">下一页 ›</button>
                <button @click="fetchAllLogs(logTotalPages)" :disabled="logCurrentPage === logTotalPages">末页 »</button>
              </div>
            </div>
            <div v-else class="no-logs">暂无任何日志记录</div>
          </div>
        </div>
      </div>
      <!-- ================= 历史日志标签页 结束 ================= -->

      <!-- ================= 系统设置标签页 开始 ================= -->
      <div v-show="currentTab === 'settings'" class="full-panel">
        <div class="settings-page">
          <h2>系统自动化配置</h2>
          <p class="description">在此上传 Excel 配置文件，可一键更新产线、工位地址及分流规则。</p>
          
          <div class="upload-section">
            <input type="file" @change="handleFileChange" accept=".xlsx, .xls" ref="fileInput" class="file-input" />
            <button @click="uploadConfigFile" :disabled="!selectedFile" class="btn-upload">
               上传并同步配置
            </button>
            <button @click="downloadTemplate" class="btn-template"> 下载模板</button>
          </div>

          <div v-if="uploadStatus" :class="uploadStatus.type" class="status-msg">
            {{ uploadStatus.text }}
          </div>
        </div>
      </div>
      <!-- ================= 系统设置标签页 结束 ================= -->

      <!-- 弹窗部分 (放在最外层，不属于任何 Tab) -->
      <div v-if="showLogModal" class="modal" @click="closeLogModal">
        <div class="modal-content" @click.stop>
          <span class="close" @click="closeLogModal">&times;</span>
          <h2>操作日志 - {{ currentLogItem.barcode }}</h2>
          <div v-if="logs.length === 0" class="no-logs">暂无记录</div>
          <ul v-else class="log-list">
            <li v-for="log in logs" :key="log.id">
              <span class="log-time">{{ new Date(log.scanned_at).toLocaleString() }}</span>
              <span class="log-msg">{{ log.action }}</span>
            </li>
          </ul>
        </div>
      </div>

      <div v-if="showScanModal" class="modal" @click="closeScanModal">
        <div class="modal-content" @click.stop>
          <span class="close" @click="closeScanModal">&times;</span>
          <h2>条码确认</h2>
          <div class="modal-body">
            <div class="input-group">
              <label>扫描条码：</label>
              <input type="text" v-model="modalScanInput" class="large-input" />
            </div>
            <div class="input-group">
              <label>目标分流通道：</label>
              <select v-model="selectedChannel" class="large-select">
                <option value="">请选择通道...</option>
                <option v-for="channel in channels" :key="channel" :value="channel">{{ channel }}</option>
              </select>
            </div>
            <p v-if="globalSelectedChannel" class="warn-text">当前处于“强制预设”模式</p>
          </div>
          <div class="modal-footer">
            <button @click="confirmScan" class="btn-confirm">确认下发 (或再次扫码)</button>
            <button @click="closeScanModal" class="btn-cancel">取消</button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'

const serverIP = window.location.hostname;
const API_BASE_URL = `http://${serverIP}:8000/api`

// 响应式数据
const items = ref([])
const searchQuery = ref('')
const showLogModal = ref(false)
const currentLogItem = ref(null)
const logs = ref([])
const showScanModal = ref(false)
const modalScanInput = ref('')
const selectedChannel = ref('')
const channels = ref([])
const globalSelectedChannel = ref('') // 主页面上的全局预选通道

// ====== Tab 页签相关 ======
const currentTab = ref('tracking') // 'tracking' 或 'logs' 或 'settings'

// ====== 历史日志查询相关 ======
const logSearchBarcode = ref('')
const logSearchResult = ref(null)
const logSearchLoading = ref(false)
const logSearchError = ref('')
const recentOfflineItems = ref([])

// ====== 系统设置相关 ======
const selectedFile = ref(null)
const uploadStatus = ref(null)
const fileInput = ref(null)

// ====== 全局日志分页相关 ======
const allLogs = ref([])
const logCurrentPage = ref(1)
const logTotalPages = ref(1)
const logTotalItems = ref(0)

// ====== 分页相关 ======
const itemsPerPage = ref(10) // 每页显示10条
const currentPage = ref(1) // 当前页

// 计算在线货物列表
const onlineItems = computed(() => {
  return items.value.filter(item => item.status === 'online')
})

// 计算下线货物列表（用于快速查询）
const offlineItems = computed(() => {
  return items.value.filter(item => item.status === 'offline').sort(
    (a, b) => new Date(b.updated_at) - new Date(a.updated_at)
  )
})

// 计算在线货物的分页数据
const displayedOnlineItems = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return onlineItems.value.slice(start, end)
})

const totalOnlinePages = computed(() => {
  return Math.ceil(onlineItems.value.length / itemsPerPage.value) || 1
})

// ====== WebSocket 逻辑 ======
let ws = null
const connectWebSocket = () => {
  ws = new WebSocket(`ws://${serverIP}:8000/ws/scan/`)
  ws.onopen = () => console.log('WebSocket 连接成功！')
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.refresh_table) {
      fetchItems();
      return;
    }

    if (showScanModal.value) {
      // 【弹窗已打开：执行双击确认逻辑】
      if (data.barcode && data.barcode === modalScanInput.value) {
        console.log('条码一致，执行自动确认...');
        confirmScan(); 
      }
    } else {
      // 【弹窗未打开：执行首次扫码逻辑】
      modalScanInput.value = data.barcode;
      
      // 优先级判断：如果主页选了预设，则用预设；否则用后端算的
      if (globalSelectedChannel.value) {
        selectedChannel.value = globalSelectedChannel.value;
      } else {
        selectedChannel.value = data.target_channel;
      }
      showScanModal.value = true;
    }
  };
  ws.onclose = () => {
    setTimeout(connectWebSocket, 1000)
  }
}

// ====== 数据获取 ======
const fetchItems = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/items/?barcode=${searchQuery.value}`)
    items.value = response.data.map(item => ({
      ...item,
      isEditing: false,
      editChannel: item.intended_target 
    }))
    // 更新最近下线的货物列表
    updateRecentOfflineItems()
  } catch (error) { console.error(error) }
}

const fetchChannels = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/channels/`)
    channels.value = response.data
  } catch (error) { console.error(error) }
}

// 获取所有日志（分页）
const fetchAllLogs = async (page = 1) => {
  logSearchLoading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/all-logs/?page=${page}`)
    allLogs.value = response.data.logs
    logCurrentPage.value = response.data.current_page
    logTotalPages.value = response.data.num_pages
    logTotalItems.value = response.data.total
  } catch (error) {
    logSearchError.value = '获取全部日志失败'
  } finally {
    logSearchLoading.value = false
  }
}

// ====== 业务逻辑 ======
const startEdit = (item) => {
  item.isEditing = true
  item.editChannel = item.intended_target 
}

const cancelEdit = (item) => { item.isEditing = false }

const saveEdit = async (item) => {
  if (!item.editChannel) return alert('请选择通道')
  try {
    await axios.post(`${API_BASE_URL}/update-channel/${item.id}/`, {
      target_channel: item.editChannel
    })
    item.isEditing = false
    alert('路径已实时修正！')
    await fetchItems()
  } catch (e) { alert('更新失败') }
}

// ====== 分页导航 ======
const goToPage = (page) => {
  if (page >= 1 && page <= totalOnlinePages.value) {
    currentPage.value = page
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalOnlinePages.value) {
    currentPage.value++
  }
}

// 搜索后重置到第一页
const searchAndReset = async () => {
  currentPage.value = 1
  await fetchItems()
}

// ====== 日志查询相关 ======
const searchLogs = async () => {
  if (!logSearchBarcode.value.trim()) {
    // 如果条码为空，则获取所有日志的第一页
    fetchAllLogs(1)
    return
  }
  
  logSearchLoading.value = true
  logSearchError.value = ''
  logSearchResult.value = null
  
  try {
    const barcode = logSearchBarcode.value.trim()
    console.log(`查询条码: ${barcode}`)
    const response = await axios.get(`${API_BASE_URL}/item-logs/${barcode}/`)
    console.log('查询结果:', response.data)
    logSearchResult.value = response.data
    logSearchError.value = ''
  } catch (error) {
    console.error('查询错误:', error)
    logSearchError.value = error.response?.data?.error || error.message || '查询失败'
    logSearchResult.value = null
  } finally {
    logSearchLoading.value = false
  }
}

const clearLogSearch = () => {
  logSearchBarcode.value = ''
  logSearchResult.value = null
  logSearchError.value = ''
}

// 初始化最近下线的货物
const updateRecentOfflineItems = () => {
  recentOfflineItems.value = offlineItems.value.slice(0, 10)
  console.log('更新最近下线的货物:', recentOfflineItems.value.map(item => item.barcode))
}

const openManualScan = () => {
  modalScanInput.value = ''
  // 手动录入同样遵循全局预设
  selectedChannel.value = globalSelectedChannel.value || ''
  showScanModal.value = true
}

const confirmScan = async () => {
  if (!modalScanInput.value.trim() || !selectedChannel.value) {
    alert('请确保条码不为空且已选择通道'); 
    return;
  }
  try {
    await axios.post(`${API_BASE_URL}/manual-scan/`, {
      barcode: modalScanInput.value.trim(),
      target_channel: selectedChannel.value
    });
    showScanModal.value = false;
    await fetchItems();
  } catch (error) { alert('确认失败') }
};

const closeScanModal = () => { showScanModal.value = false }

const viewLogs = async (item) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/item-logs/${item.barcode}/`)
    currentLogItem.value = { barcode: response.data.barcode }
    logs.value = response.data.logs
    showLogModal.value = true
  } catch (error) {
    alert('获取日志失败')
  }
}

const closeLogModal = () => { showLogModal.value = false }

// ====== 系统设置相关函数 ======
const handleFileChange = (e) => {
  selectedFile.value = e.target.files[0];
};

const uploadConfigFile = async () => {
  if (!selectedFile.value) return;
  
  const formData = new FormData();
  formData.append('file', selectedFile.value);
  
  uploadStatus.value = { type: 'info', text: '正在同步数据，请稍候...' };

  try {
    const response = await axios.post(`${API_BASE_URL}/upload-config/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    uploadStatus.value = { type: 'success', text: response.data.message };
    // 成功后刷新一下基础数据
    fetchItems();
    fetchChannels();
    // 清空文件选择
    selectedFile.value = null;
    fileInput.value.value = '';
  } catch (error) {
    const errorMsg = error.response?.data?.error || '上传失败';
    uploadStatus.value = { type: 'error', text: `❌ ${errorMsg}` };
  }
};

// 下载模板的功能（可选：你可以放一个静态文件在 backend/static 下）
const downloadTemplate = () => {
  // 直接跳转到后端静态文件地址
  // serverIP 是你之前定义的动态获取的当前服务器 IP
  const templateUrl = `http://${serverIP}:8000/static/config_template.xlsx`;
  
  // 创建一个隐藏的 a 标签模拟点击下载
  const link = document.createElement('a');
  link.href = templateUrl;
  link.setAttribute('download', '产线配置模板.xlsx');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

onMounted(() => {
  fetchItems()
  fetchChannels()
  connectWebSocket()
  fetchAllLogs() // 获取第一页日志
  // 初始化最近下线的货物
  updateRecentOfflineItems()
})

onUnmounted(() => { if (ws) ws.close() })
</script>

<style scoped>
/* 布局与基础样式 */
.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 20px;
  align-items: center;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  border-left: 5px solid #2c3e50;
}

.global-preset {
  display: flex;
  align-items: center;
  gap: 10px;
}

.select-preset {
  padding: 8px;
  border: 2px solid #2c3e50;
  font-weight: bold;
}

.btn-manual {
  padding: 10px 20px;
  background: #2c3e50;
  color: white;
  border: none;
  cursor: pointer;
  font-weight: bold;
}

/* 搜索与表格 */
.search-bar { margin-bottom: 15px; display: flex; gap: 10px; }
.search-bar input { padding: 8px; border: 1px solid #ddd; width: 250px; }
table { width: 100%; border-collapse: collapse; background: white; }
th { background: #2c3e50; color: white; padding: 12px; text-align: left; }
td { padding: 12px; border-bottom: 1px solid #eee; }

/* 弹窗样式 */
.modal {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; z-index: 1000;
}
.modal-content {
  background: white; padding: 30px; border-radius: 8px; width: 500px; position: relative;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
.close { position: absolute; right: 20px; top: 15px; font-size: 28px; cursor: pointer; color: #999; }
.input-group { margin-bottom: 20px; }
.input-group label { display: block; margin-bottom: 8px; font-weight: bold; }
.large-input, .large-select { width: 100%; padding: 12px; font-size: 18px; border: 2px solid #2c3e50; }
.warn-text { color: #e67e22; font-weight: bold; margin-top: -10px; margin-bottom: 15px; }

/* 按钮样式 */
.btn-confirm { background: #27ae60; color: white; border: none; padding: 12px 25px; font-size: 18px; cursor: pointer; font-weight: bold; width: 100%; margin-bottom: 10px; }
.btn-cancel { background: #95a5a6; color: white; border: none; padding: 12px 25px; font-size: 16px; cursor: pointer; width: 100%; }
.highlight-text { color: #e67e22; font-weight: bold; }

/* 日志列表样式 */
.log-list { list-style: none; padding: 0; max-height: 300px; overflow-y: auto; }
.log-list li { padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }
.log-time { color: #666; font-size: 13px; }

/* 编辑表格样式 */
.edit-cell {
  display: flex;
  gap: 8px;
}

.edit-select {
  padding: 6px;
  border: 2px solid #3498db;
  border-radius: 4px;
  font-size: 14px;
  flex: 1;
}

.view-actions, .edit-actions {
  display: flex;
  gap: 8px;
}

.btn-edit, .btn-logs, .btn-save, .btn-cancel {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}

.btn-edit {
  background: #3498db;
  color: white;
}

.btn-edit:hover {
  background: #2980b9;
}

.btn-logs {
  background: #9b59b6;
  color: white;
}

.btn-logs:hover {
  background: #8e44ad;
}

.btn-save {
  background: #27ae60;
  color: white;
}

.btn-save:hover {
  background: #229954;
}

.btn-cancel {
  background: #e74c3c;
  color: white;
}

.btn-cancel:hover {
  background: #c0392b;
}

/* 位置标签样式 */
.location-tag {
  display: inline-block;
  padding: 6px 12px;
  background: #f39c12;
  color: white;
  border-radius: 4px;
  font-weight: bold;
  font-size: 13px;
  text-align: center;
  min-width: 80px;
}

/* 系统设置样式 */
.settings-page {
  background: white;
  padding: 30px;
  border-radius: 8px;
  border: 1px solid #ddd;
}
.description { color: #666; margin-bottom: 20px; }
.upload-section {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: #f8f9fa;
  border: 2px dashed #ccc;
  border-radius: 8px;
}
.file-input { font-size: 16px; }
.btn-upload {
  background: #27ae60; color: white; border: none;
  padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;
}
.btn-upload:disabled { background: #bdc3c7; cursor: not-allowed; }
.btn-template {
  background: #34495e; color: white; border: none;
  padding: 10px 20px; border-radius: 4px; cursor: pointer;
}
.status-msg { margin-top: 20px; padding: 15px; border-radius: 4px; font-weight: bold; }
.success { background: #d4edda; color: #155724; }
.error { background: #f8d7da; color: #721c24; }
.info { background: #cce5ff; color: #004085; }

</style>