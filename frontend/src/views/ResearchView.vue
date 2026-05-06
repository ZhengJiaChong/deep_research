<template>
  <div class="research-container">
    <!-- 顶部查询区域 -->
    <div class="query-section" v-if="researchData">
      <div class="query-bubble">
        <p class="query-text">{{ researchData.query }}</p>
      </div>
      
      <!-- 研究状态提示 -->
      <div class="status-message" v-if="progressData">
        <el-icon class="status-icon">
          <component :is="progressData.status === 'completed' ? 'Check' : 'Loading'" />
        </el-icon>
        <span class="status-text">
          {{ progressData.status === 'completed' ? '深度研究已完成' : '深度研究进行中...' }}
          <span v-if="progressData.status !== 'completed'" class="progress-percent">
            （进度 {{ progressData.progress }}%）
          </span>
        </span>
      </div>
    </div>
    
    <!-- 主内容区：左右分栏 -->
    <div class="main-content">
      <!-- 左侧：进度和日志 -->
      <div class="left-panel">
        <!-- 执行过程日志 -->
        <div class="logs-section" v-if="progressLogs && progressLogs.length > 0">
          <div class="logs-container">
            <div
              v-for="(log, index) in progressLogs"
              :key="index"
              class="log-item"
              :class="`log-${log.type}`"
            >
              <span class="log-icon">{{ getLogIcon(log.type) }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
        
        <!-- 加载占位 -->
        <el-card v-if="loading" class="loading-card">
          <el-skeleton :rows="10" animated />
        </el-card>
      </div>
      
      <!-- 右侧：大纲和结果 -->
      <div class="right-panel">
        <!-- 研究大纲 -->
        <el-card class="outline-card" v-if="outlineData && outlineData.outline">
          <template #header>
            <div class="card-header">
              <el-icon><List /></el-icon>
              <span>研究大纲</span>
              <el-tag type="info" size="small">{{ outlineData.outline.length }} 个任务</el-tag>
            </div>
          </template>
          
          <el-collapse v-model="activeCollapse" accordion>
            <el-collapse-item
              v-for="(item, index) in outlineData.outline"
              :key="item.id"
              :title="item.title"
              :name="item.id"
            >
              <div class="outline-content">
                <p>{{ item.description }}</p>
                <el-tag size="small" :type="getTaskStatusType(item.status)">
                  {{ getTaskStatusText(item.status) }}
                </el-tag>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
        
        <!-- 搜索结果详情 -->
        <el-card class="results-card" v-if="researchData && researchData.tasks && researchData.tasks.length > 0">
          <template #header>
            <div class="card-header">
              <el-icon><Search /></el-icon>
              <span>研究详情</span>
            </div>
          </template>
          
          <div class="tasks-list">
            <div
              v-for="task in researchData.tasks"
              :key="task.task_id"
              class="task-card"
            >
              <div class="task-header">
                <el-icon class="task-icon">
                  <component :is="task.status === 'completed' ? 'CircleCheckFilled' : 'Loading'" />
                </el-icon>
                <span class="task-title">{{ task.title }}</span>
                <el-tag size="small" :type="getTaskStatusType(task.status)">
                  {{ getTaskStatusText(task.status) }}
                </el-tag>
              </div>
              
              <!-- 搜索关键词 -->
              <div v-if="task.search_keywords && task.search_keywords.length > 0" class="keywords-section">
                <div class="section-label">
                  <el-icon><Search /></el-icon>
                  <span>搜索关键词</span>
                </div>
                <div class="keywords-list">
                  <el-tag
                    v-for="keyword in task.search_keywords"
                    :key="keyword"
                    type="info"
                    size="small"
                    class="keyword-tag"
                  >
                    {{ keyword }}
                  </el-tag>
                </div>
              </div>
              
              <!-- 搜索结果 -->
              <div v-if="task.search_results && task.search_results.length > 0" class="results-section">
                <div class="section-label">
                  <el-icon><Link /></el-icon>
                  <span>搜索结果</span>
                </div>
                <div class="result-list">
                  <div
                    v-for="(result, rIndex) in task.search_results.slice(0, 3)"
                    :key="rIndex"
                    class="result-item"
                  >
                    <a :href="result.url" target="_blank" class="result-link">
                      <el-icon><TopRight /></el-icon>
                      {{ result.title }}
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- 最终报告 -->
        <el-card class="report-card" v-if="reportData && reportData.report">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>研究报告</span>
              <div class="header-actions">
                <el-tag size="small">{{ reportData.word_count }} 字</el-tag>
                <el-button size="small" @click="copyReport">
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="report-content" v-html="renderMarkdown(reportData.report)"></div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useResearchStore } from '../stores/research'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import api from '../api/research'

export default {
  name: 'ResearchView',
  setup() {
    const route = useRoute()
    const researchStore = useResearchStore()
    
    const researchId = route.params.id
    const progressData = ref(null)
    const outlineData = ref(null)
    const researchData = ref(null)
    const reportData = ref(null)
    const progressLogs = ref([])  // 进度日志
    const loading = ref(true)
    const activeCollapse = ref([])
    
    let pollTimer = null
    
    // Markdown渲染
    const renderMarkdown = (text) => {
      return marked(text)
    }
    
    // 获取状态类型
    const getStatusType = (status) => {
      const typeMap = {
        'starting': 'info',
        'analyzing': 'warning',
        'outlining': 'warning',
        'executing': 'primary',
        'completed': 'success',
        'error': 'danger'
      }
      return typeMap[status] || 'info'
    }
    
    // 获取状态文本
    const getStatusText = (status) => {
      const textMap = {
        'starting': '启动中',
        'analyzing': '分析中',
        'outlining': '生成大纲',
        'executing': '执行中',
        'completed': '已完成',
        'error': '错误'
      }
      return textMap[status] || status
    }
    
    // 获取任务状态类型
    const getTaskStatusType = (status) => {
      const typeMap = {
        'pending': 'info',
        'running': 'warning',
        'completed': 'success',
        'failed': 'danger'
      }
      return typeMap[status] || 'info'
    }
    
    // 获取任务状态文本
    const getTaskStatusText = (status) => {
      const textMap = {
        'pending': '待执行',
        'running': '进行中',
        'completed': '已完成',
        'failed': '失败'
      }
      return textMap[status] || status
    }
    
    // 获取日志图标
    const getLogIcon = (type) => {
      const iconMap = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
      }
      return iconMap[type] || 'ℹ️'
    }
    
    // 加载数据
    const loadData = async () => {
      try {
        // 获取进度
        progressData.value = await api.getProgress(researchId)
        
        // 更新进度日志
        if (progressData.value.progress_logs) {
          progressLogs.value = progressData.value.progress_logs
        }
        
        // 获取大纲
        if (!outlineData.value) {
          outlineData.value = await api.getOutline(researchId)
        }
        
        // 获取研究数据（包含任务详情）
        const research = await researchStore.getProgress(researchId)
        researchData.value = research
        
        // 如果研究完成，开始流式获取报告
        if (progressData.value.status === 'completed' && !reportData.value) {
          // 初始化报告数据
          reportData.value = {
            research_id: researchId,
            report: '',
            word_count: 0,
            generated_at: new Date().toISOString()
          }
          
          // 开始流式输出
          startStreamReport()
          
          // 停止轮询
          if (pollTimer) {
            clearInterval(pollTimer)
            pollTimer = null
          }
        }
      } catch (error) {
        ElMessage.error('加载数据失败：' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    // 开始轮询
    const startPolling = () => {
      pollTimer = setInterval(() => {
        loadData()
      }, 3000)  // 每3秒轮询一次
    }
    
    // 流式获取报告
    const startStreamReport = () => {
      const streamSource = api.streamReport(
        researchId,
        // onChunk - 接收数据块
        (content) => {
          if (content) {
            reportData.value.report += content
            reportData.value.word_count = reportData.value.report.length
          }
        },
        // onDone - 完成
        () => {
          ElMessage.success('报告生成完成！')
        },
        // onError - 错误
        (error) => {
          ElMessage.error('流式输出失败：' + error)
          // 如果流式失败，尝试普通方式获取
          loadReportFallback()
        }
      )
      
      // 保存引用以便关闭
      window.streamSource = streamSource
    }
    
    // 备用：普通方式获取报告
    const loadReportFallback = async () => {
      try {
        reportData.value = await api.getReport(researchId)
        ElMessage.success('报告加载完成！')
      } catch (error) {
        ElMessage.error('报告加载失败：' + error.message)
      }
    }
    
    // 复制报告
    const copyReport = () => {
      if (reportData.value && reportData.value.report) {
        navigator.clipboard.writeText(reportData.value.report)
          .then(() => {
            ElMessage.success('报告已复制到剪贴板')
          })
          .catch(() => {
            ElMessage.error('复制失败')
          })
      }
    }
    
    onMounted(() => {
      loadData()
      startPolling()
    })
    
    onUnmounted(() => {
      if (pollTimer) {
        clearInterval(pollTimer)
      }
    })
    
    return {
      researchId,
      progressData,
      outlineData,
      researchData,
      reportData,
      loading,
      activeCollapse,
      renderMarkdown,
      getStatusType,
      getStatusText,
      getTaskStatusType,
      getTaskStatusText,
      copyReport
    }
  }
}
</script>

<style scoped>
.research-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: calc(100vh - 60px);
}

/* 顶部查询区域 */
.query-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px;
  border-radius: 12px;
  color: white;
}

.query-bubble {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.query-text {
  margin: 0;
  font-size: 16px;
  line-height: 1.6;
  color: white;
}

.status-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.status-icon {
  font-size: 20px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.status-text {
  font-size: 14px;
  color: white;
}

.progress-percent {
  opacity: 0.9;
}

/* 主内容区：左右分栏 */
.main-content {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 20px;
  flex: 1;
  overflow: hidden;
}

/* 左侧面板 */
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

/* 右侧面板 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

/* 日志样式 */
.logs-section {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.logs-container {
  max-height: 600px;
  overflow-y: auto;
  padding: 10px;
}

.log-item {
  display: flex;
  align-items: flex-start;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.log-info {
  background-color: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.log-success {
  background-color: #f6ffed;
  border-left: 3px solid #52c41a;
}

.log-warning {
  background-color: #fffbe6;
  border-left: 3px solid #faad14;
}

.log-error {
  background-color: #fff2f0;
  border-left: 3px solid #ff4d4f;
}

.log-icon {
  margin-right: 8px;
  font-size: 14px;
  flex-shrink: 0;
}

.log-message {
  color: #303133;
  flex: 1;
}

/* 卡片样式 */
.outline-card,
.results-card,
.report-card,
.loading-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.card-header .el-icon {
  font-size: 18px;
  color: #409EFF;
}

/* 大纲样式 */
.outline-content {
  padding: 8px 0;
}

.outline-content p {
  margin: 0 0 12px 0;
  color: #606266;
  line-height: 1.6;
}

/* 任务卡片 */
.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-card {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.task-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.task-icon {
  font-size: 18px;
  color: #409EFF;
}

.task-icon.el-icon-loading {
  animation: rotate 1s linear infinite;
}

.task-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  flex: 1;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 12px 0 8px 0;
  color: #606266;
  font-size: 13px;
  font-weight: 500;
}

.section-label .el-icon {
  font-size: 14px;
}

/* 关键词样式 */
.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  cursor: default;
}

/* 搜索结果样式 */
.result-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s;
}

.result-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.result-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #409EFF;
  text-decoration: none;
  font-size: 13px;
  line-height: 1.5;
}

.result-link:hover {
  text-decoration: underline;
}

.result-link .el-icon {
  font-size: 12px;
}

/* 报告样式 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.report-content {
  line-height: 1.8;
  padding: 8px 0;
}

.report-content :deep(h1) {
  font-size: 24px;
  margin: 24px 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #409EFF;
  color: #303133;
}

.report-content :deep(h2) {
  font-size: 20px;
  margin: 20px 0 12px 0;
  color: #303133;
}

.report-content :deep(h3) {
  font-size: 18px;
  margin: 16px 0 10px 0;
  color: #303133;
}

.report-content :deep(p) {
  margin: 12px 0;
  color: #606266;
  text-align: justify;
}

.report-content :deep(ul),
.report-content :deep(ol) {
  padding-left: 24px;
  margin: 12px 0;
}

.report-content :deep(li) {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

/* 响应式 */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .left-panel {
    max-height: 300px;
  }
}
</style>
