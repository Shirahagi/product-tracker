<template>
  <div class="container">
    <h1>产线货物跟踪系统</h1>
    
    <div class="control-panel">
      <div class="station-select">
        <label>当前工位设置：</label>
        <select v-model="currentStation">
          <option value="工位A_装配">工位A_装配</option>
          <option value="工位B_质检">工位B_质检</option>
          <option value="工位_包装">工位C_包装</option>
        </select>
      </div>

      <div class="scan-simulator">
        <label>扫码器输入区：</label>
        <!-- @keyup.enter 完美模拟了真实扫码枪扫码后自动回车的动作 -->
        <input 
          type="text" 
          v-model="scanInput" 
          @keyup.enter="handleScan" 
          placeholder="请扫码或输入条码按回车..."
          ref="scannerInput"
          autofocus
        />
        <button @click="handleScan">手动提交</button>
      </div>
    </div>

    <div class="data-table">
      <h2>实时货物状态</h2>
      <table>
        <thead>
          <tr>
            <th>条码</th>
            <th>当前工位</th>
            <th>最后更新时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="items.length === 0">
            <td colspan="3" style="text-align: center;">暂无数据，请扫码录入</td>
          </tr>
          <tr v-for="item in items" :key="item.id">
            <td>{{ item.barcode }}</td>
            <td class="highlight">{{ item.current_station }}</td>
            <td>{{ new Date(item.updated_at).toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'

// Django 后端的地址 (请确保运行 Django 的那个终端没被关掉)
const API_BASE_URL = 'http://127.0.0.1:8000/api'

// 响应式数据
const items = ref([])
const currentStation = ref('工位A_装配')
const scanInput = ref('')
const scannerInput = ref(null)

// 获取货物列表
const fetchItems = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/items/`)
    items.value = response.data
  } catch (error) {
    console.error('获取货物列表失败:', error)
  }
}

// 处理扫码
const handleScan = async () => {
  if (!scanInput.value.trim()) {
    alert('请输入条码')
    return
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/scan/`, {
      barcode: scanInput.value.trim(),
      station: currentStation.value
    })

    alert(response.data.message)
    scanInput.value = ''
    await fetchItems() // 重新获取列表

    // 聚焦输入框
    await nextTick()
    scannerInput.value.focus()
  } catch (error) {
    console.error('扫码处理失败:', error)
    alert('扫码处理失败，请重试')
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchItems()
})
</script>