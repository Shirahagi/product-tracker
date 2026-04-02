<template>
  <div class="container">
    <!-- 顶部导航 -->
    <div class="tab-navigation">
      <button 
        @click="currentTab = 'tracking'" 
        :class="{ 'tab-active': currentTab === 'tracking' }" 
        class="tab-btn"
      >
        实时货物 (在线: {{ onlineItems.length }})
      </button>
      <button 
        @click="currentTab = 'logs'" 
        :class="{ 'tab-active': currentTab === 'logs' }" 
        class="tab-btn"
      >
        历史日志
      </button>
      <button 
        @click="currentTab = 'settings'" 
        :class="{ 'tab-active': currentTab === 'settings' }" 
        class="tab-btn"
      >
        系统设置
      </button>
    </div>

    <div class="main-layout">
      <!-- ================= 实时货物标签页 ================= -->
      <div v-show="currentTab === 'tracking'" class="full-panel">
        <div class="data-table">
          <div class="action-bar">
            <button @click="openManualScan" class="btn-manual">手动录入</button>
            <div class="preset-group">
              <label>强制预设：</label>
              <select v-model="globalSelectedChannel" class="select-preset">
                <option value="">跟随系统规则</option>
                <option v-for="channel in channels" :key="channel" :value="channel">通道 {{ channel }}</option>
              </select>
            </div>
            <div class="search-group">
              <input type="text" v-model="searchQuery" @keyup.enter="searchAndReset" placeholder="搜索二维码..." class="input-search"/>
              <button @click="searchAndReset" class="btn-search">搜索</button>
              <button @click="searchQuery=''; searchAndReset()" class="btn-reset">重置</button>
            </div>
            <span class="hint-text">提示：扫码枪扫描自动弹窗</span>
          </div>

          <table>
            <thead>
              <tr>
                <th>二维码</th><th>下料通道</th><th>状态</th><th>位置</th><th>上线时间</th><th>更新时间</th><th width="120">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in displayedOnlineItems" :key="item.id">
                <td class="bold">{{ item.barcode }}</td>
                <td>
                  <div v-if="item.isEditing" class="edit-cell">
                    <select v-model="item.editChannel" class="edit-select">
                      <option v-for="channel in channels" :key="channel" :value="channel">{{ channel }}</option>
                    </select>
                  </div>
                  <div v-else>{{ item.intended_target || '未设定' }}</div>
                </td>
                <td><span :class="item.status === 'online' ? 'badge-online' : 'badge-offline'">{{ item.status === 'online' ? '在线' : '下线' }}</span></td>
                <td><span class="location-tag">{{ item.current_location || '待定位' }}</span></td>
                <td>{{ formatTime(item.created_at) }}</td>
                <td>{{ formatTime(item.updated_at) }}</td>
                <td>
                  <div v-if="item.isEditing" class="btn-group-cell">
                    <button @click="saveEdit(item)" class="text-btn-save">保存</button>
                    <button @click="cancelEdit(item)" class="text-btn-cancel">取消</button>
                  </div>
                  <div v-else class="btn-group-cell">
                    <button @click="startEdit(item)" v-if="item.status === 'online'" class="text-btn-edit">编辑</button>
                    <button @click="viewLogs(item)" class="text-btn-logs">日志</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="pagination">
            <button @click="prevPage" :disabled="currentPage === 1">上一页</button>
            <span class="page-info">{{ currentPage }} / {{ totalOnlinePages }}</span>
            <button @click="nextPage" :disabled="currentPage === totalOnlinePages">下一页</button>
          </div>
        </div>
      </div>

      <!-- ================= 历史日志标签页 (修正) ================= -->
      <div v-show="currentTab === 'logs'" class="full-panel">
        <div class="log-page">
          <div class="log-search-bar">
            <input v-model="logSearchBarcode" placeholder="输入条码精确查询..." @keyup.enter="searchLogs" class="input-log-search" />
            <button @click="searchLogs" class="btn-search">查询</button>
            <button @click="clearLogSearch" class="btn-reset">重置/显示全部</button>
          </div>

          <div class="log-content">
            <!-- 情况A: 正在加载 -->
            <div v-if="logSearchLoading" class="log-info">正在从服务器读取日志数据...</div>

            <!-- 情况B: 查无结果 -->
            <div v-else-if="!logSearchLoading && (logSearchResult && logSearchResult.logs.length === 0)" class="log-info">
              未找到关于 [{{ logSearchBarcode }}] 的任何记录。
            </div>

            <!-- 情况C: 显示列表 (搜索结果 或 全部动态) -->
            <div v-else>
              <h3 class="log-subtitle">{{ logSearchResult ? '查询结果: ' + logSearchResult.barcode : '全线最新动态' }}</h3>
              <ul class="log-list-full">
                <li v-for="log in displayedLogs" :key="log.id" class="log-item">
                  <span class="time">{{ formatFullTime(log.scanned_at) }}</span>
                  <span class="barcode" v-if="!logSearchResult">[{{ log.barcode }}]</span>
                  <span class="action">{{ log.action }}</span>
                </li>
              </ul>

              <!-- 全量日志的分页器 (仅在非搜索模式下显示) -->
              <div v-if="!logSearchResult" class="pagination">
                <button @click="fetchAllLogs(logCurrentPage - 1)" :disabled="logCurrentPage === 1">上一页</button>
                <span class="page-info">第 {{ logCurrentPage }} 页 / 共 {{ logTotalPages }} 页</span>
                <button @click="fetchAllLogs(logCurrentPage + 1)" :disabled="logCurrentPage === logTotalPages">下一页</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ================= 系统设置标签页 ================= -->
      <div v-show="currentTab === 'settings'" class="full-panel">
        <div class="settings-page">
          <div class="upload-card">
            <h3>同步配置文件</h3>
            <p>请上传 Excel 文件同步系统参数。</p>
            <div class="upload-controls">
              <input type="file" @change="handleFileChange" accept=".xlsx, .xls" ref="fileInput" />
              <button @click="uploadConfigFile" :disabled="!selectedFile" class="btn-confirm">执行同步</button>
              <button @click="downloadTemplate" class="btn-reset">下载模板</button>
            </div>
            <div v-if="uploadStatus" :class="uploadStatus.type" class="status-box">{{ uploadStatus.text }}</div>
          </div>
        </div>
      </div>

      <!-- ================= 巨型扫码确认弹窗 ================= -->
      <div v-if="showScanModal" class="modal-overlay" @click="closeScanModal">
        <div class="modal-content-giant" @click.stop>
          <div class="modal-header">扫码内容确认</div>
          <div class="modal-body">
            <div class="giant-input-section">
              <label>条码内容</label>
              <input type="text" v-model="modalScanInput" class="giant-barcode-input" ref="modalInputRef" />
            </div>
            <div class="giant-input-section">
              <label>下发通道</label>
              <select v-model="selectedChannel" class="giant-select">
                <option value="">未选择通道</option>
                <option v-for="channel in channels" :key="channel" :value="channel">通道 {{ channel }}</option>
              </select>
            </div>
            <div v-if="globalSelectedChannel" class="preset-alert">当前处于【强制预设】模式，通道已自动锁定。</div>
          </div>
          <div class="modal-footer">
            <button @click="confirmScan" class="btn-confirm-big">确认下发指令</button>
            <button @click="closeScanModal" class="btn-cancel-big">取消返回</button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import axios from 'axios'

const serverIP = window.location.hostname;
const API_BASE_URL = `http://${serverIP}:8000/api`;

// 状态
const currentTab = ref('tracking');
const items = ref([]);
const searchQuery = ref('');
const channels = ref([]);
const globalSelectedChannel = ref('');
const currentPage = ref(1);
const itemsPerPage = ref(10);

// 弹窗
const showScanModal = ref(false);
const modalScanInput = ref('');
const selectedChannel = ref('');
const modalInputRef = ref(null);

// 日志
const showLogModal = ref(false);
const logs = ref([]);
const currentLogItem = ref(null);
const logSearchBarcode = ref('');
const logSearchResult = ref(null);
const logSearchLoading = ref(false);
const allLogs = ref([]);
const logCurrentPage = ref(1);
const logTotalPages = ref(1);

// 设置
const selectedFile = ref(null);
const uploadStatus = ref(null);
const fileInput = ref(null);

// ================= WebSocket =================
let ws = null;
const connectWebSocket = () => {
  ws = new WebSocket(`ws://${serverIP}:8000/ws/scan/`);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.refresh_table) { fetchItems(); fetchAllLogs(1); } // 刷新时也同步刷新日志
    else { handleIncomingScan(data); }
  };
  ws.onclose = () => setTimeout(connectWebSocket, 2000);
};

const handleIncomingScan = (data) => {
  if (showScanModal.value) {
    if (data.barcode === modalScanInput.value) confirmScan();
  } else {
    modalScanInput.value = data.barcode;
    selectedChannel.value = globalSelectedChannel.value || data.target_channel;
    showScanModal.value = true;
    nextTick(() => modalInputRef.value?.focus());
  }
};

// ================= 数据获取 =================
const fetchItems = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/items/?barcode=${searchQuery.value}`);
    items.value = res.data.map(i => ({ ...i, isEditing: false, editChannel: i.intended_target }));
  } catch (e) { console.error(e); }
};

const fetchChannels = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/channels/`);
    channels.value = res.data;
  } catch (e) { console.error(e); }
};

const fetchAllLogs = async (page = 1) => {
  if (logSearchResult.value) return; // 如果正在搜索特定条码，不刷新全量日志
  logSearchLoading.value = true;
  try {
    const res = await axios.get(`${API_BASE_URL}/all-logs/?page=${page}`);
    allLogs.value = res.data.logs;
    logCurrentPage.value = res.data.current_page;
    logTotalPages.value = res.data.num_pages;
  } catch (e) { console.error(e); }
  finally { logSearchLoading.value = false; }
};

// ================= 搜索逻辑 (核心修正) =================
const searchLogs = async () => {
  const barcode = logSearchBarcode.value.trim();
  if (!barcode) {
    clearLogSearch();
    return;
  }
  logSearchLoading.value = true;
  try {
    const res = await axios.get(`${API_BASE_URL}/item-logs/${barcode}/`);
    logSearchResult.value = res.data;
  } catch (e) { console.error(e); logSearchResult.value = { barcode, logs: [] }; }
  finally { logSearchLoading.value = false; }
};

const clearLogSearch = () => {
  logSearchBarcode.value = '';
  logSearchResult.value = null;
  fetchAllLogs(1);
};

// ================= 业务操作 =================
const openManualScan = () => {
  modalScanInput.value = '';
  selectedChannel.value = globalSelectedChannel.value || '';
  showScanModal.value = true;
  nextTick(() => modalInputRef.value?.focus());
};

const confirmScan = async () => {
  if (!modalScanInput.value || !selectedChannel.value) return alert("条码和通道不能为空");
  try {
    await axios.post(`${API_BASE_URL}/manual-scan/`, {
      barcode: modalScanInput.value,
      target_channel: selectedChannel.value
    });
    showScanModal.value = false;
    fetchItems();
    fetchAllLogs(1);
  } catch (e) { alert("录入失败"); }
};

const saveEdit = async (item) => {
  try {
    await axios.post(`${API_BASE_URL}/update-channel/${item.id}/`, { target_channel: item.editChannel });
    item.isEditing = false;
    fetchItems();
    fetchAllLogs(1);
  } catch (e) { alert("保存失败"); }
};

const startEdit = (item) => { item.isEditing = true; };
const cancelEdit = (item) => { item.isEditing = false; };
const closeScanModal = () => { showScanModal.value = false; };
const viewLogs = (item) => { currentTab.value = 'logs'; logSearchBarcode.value = item.barcode; searchLogs(); };
const handleFileChange = (e) => { selectedFile.value = e.target.files[0]; };
const uploadConfigFile = async () => {
  const fd = new FormData(); fd.append('file', selectedFile.value);
  try {
    const res = await axios.post(`${API_BASE_URL}/upload-config/`, fd);
    uploadStatus.value = { type: 'success', text: res.data.message };
    fetchChannels();
  } catch (e) { uploadStatus.value = { type: 'error', text: '同步失败' }; }
};
const downloadTemplate = () => window.open(`http://${serverIP}:8000/static/config_template.xlsx`);

// ================= 计算属性 =================
const onlineItems = computed(() => items.value.filter(i => i.status === 'online'));
const totalOnlinePages = computed(() => Math.ceil(onlineItems.value.length / itemsPerPage.value) || 1);
const displayedOnlineItems = computed(() => {
  const s = (currentPage.value - 1) * itemsPerPage.value;
  return onlineItems.value.slice(s, s + itemsPerPage.value);
});
const displayedLogs = computed(() => logSearchResult.value ? logSearchResult.value.logs : allLogs.value);

const prevPage = () => { if (currentPage.value > 1) currentPage.value--; };
const nextPage = () => { if (currentPage.value < totalOnlinePages.value) currentPage.value++; };
const searchAndReset = () => { currentPage.value = 1; fetchItems(); };

const formatTime = (t) => t ? new Date(t).toLocaleTimeString('zh-CN', {hour12: false}) : '--';
const formatFullTime = (t) => t ? new Date(t).toLocaleString() : '--';

onMounted(() => {
  fetchItems();
  fetchChannels();
  connectWebSocket();
  fetchAllLogs();
});
</script>

<style scoped>
.container { padding: 10px; font-family: sans-serif; background: #fff; }
.tab-navigation { display: flex; border-bottom: 2px solid #2c3e50; margin-bottom: 10px; }
.tab-btn { padding: 10px 20px; border: none; background: #eee; cursor: pointer; font-weight: bold; margin-right: 2px; }
.tab-active { background: #2c3e50; color: #fff; }

.action-bar { display: flex; align-items: center; gap: 15px; background: #f4f7f9; padding: 10px; border-radius: 4px; margin-bottom: 10px; }
.search-group { display: flex; border-left: 1px solid #ccc; padding-left: 15px; gap: 5px; }
.input-search { padding: 6px; width: 150px; border: 1px solid #ccc; }
.btn-manual { background: #2c3e50; color: white; border: none; padding: 8px 15px; cursor: pointer; font-weight: bold; }
.btn-search { background: #34495e; color: white; border: none; padding: 6px 12px; cursor: pointer; }
.btn-reset { background: #95a5a6; color: white; border: none; padding: 6px 12px; cursor: pointer; }
.hint-text { margin-left: auto; color: #7f8c8d; font-size: 13px; }

table { width: 100%; border-collapse: collapse; }
th { background: #2c3e50; color: #fff; padding: 10px; text-align: left; font-size: 14px; }
td { padding: 10px; border-bottom: 1px solid #eee; font-size: 14px; }
.bold { font-weight: bold; }
.badge-online { color: #27ae60; font-weight: bold; }
.location-tag { background: #f39c12; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px; }

.pagination { display: flex; justify-content: center; align-items: center; gap: 15px; padding: 15px; }

/* 日志页 */
.log-page { padding: 10px; background: #fff; min-height: 500px; }
.log-search-bar { display: flex; gap: 10px; margin-bottom: 20px; }
.input-log-search { padding: 10px; flex: 1; max-width: 400px; border: 2px solid #2c3e50; font-size: 16px; }
.log-info { padding: 40px; text-align: center; color: #999; border: 1px dashed #ddd; }
.log-subtitle { border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; color: #2c3e50; }
.log-list-full { list-style: none; padding: 0; }
.log-item { display: flex; gap: 20px; padding: 12px; border-bottom: 1px solid #f1f1f1; align-items: center; }
.log-item:nth-child(even) { background: #fafafa; }
.log-item .time { color: #666; font-size: 13px; min-width: 160px; }
.log-item .barcode { font-weight: bold; color: #2980b9; min-width: 100px; }

/* 巨型弹窗 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 999; }
.modal-content-giant { background: white; width: 80%; max-height: 90vh; border-radius: 8px; display: flex; flex-direction: column; overflow: hidden; }
.modal-header { background: #2c3e50; color: white; padding: 15px; font-size: 20px; font-weight: bold; text-align: center; }
.modal-body { flex: 1; padding: 30px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
.giant-barcode-input { width: 100%; padding: 15px; font-size: 60px; font-weight: bold; text-align: center; border: 3px solid #2c3e50; }
.giant-select { width: 100%; padding: 15px; font-size: 30px; border: 3px solid #2c3e50; }
.modal-footer { padding: 20px; display: flex; gap: 20px; }
.btn-confirm-big { flex: 2; padding: 20px; font-size: 24px; background: #27ae60; color: white; border: none; font-weight: bold; cursor: pointer; }
.btn-cancel-big { flex: 1; padding: 20px; font-size: 24px; background: #95a5a6; color: white; border: none; cursor: pointer; }

/* 按钮文字化 */
.text-btn-edit { color: #3498db; background: none; border: none; cursor: pointer; font-weight: bold; }
.text-btn-logs { color: #9b59b6; background: none; border: none; cursor: pointer; font-weight: bold; }
.text-btn-save { color: #27ae60; background: none; border: none; cursor: pointer; font-weight: bold; }
.text-btn-cancel { color: #e74c3c; background: none; border: none; cursor: pointer; font-weight: bold; }
</style>