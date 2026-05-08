<template>
  <div class="chat-layout">
    <!-- 左侧导航栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <el-icon class="logo-icon"><Search /></el-icon>
        <span class="app-title">深度研究</span>
      </div>
      
      <div class="new-research-btn">
        <el-button type="primary" :icon="Plus" @click="startNewResearch" block>
          开启新研究
        </el-button>
      </div>

      <div class="history-list">
        <div class="history-label">快捷指令</div>
        <div 
          v-for="(action, index) in quickActions" 
          :key="index"
          class="history-item"
          @click="useQuickAction(action)"
        >
          <el-icon><component :is="action.icon" /></el-icon>
          <span>{{ action.label }}</span>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="model-badge">
          <el-icon><Cpu /></el-icon>
          <span>{{ currentModel }}</span>
        </div>
      </div>
    </aside>

    <!-- 右侧主聊天区 -->
    <main class="chat-main">
      <div class="chat-container">
        <!-- 消息列表 -->
        <div class="message-wrapper" ref="messageContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <div class="welcome-card">
              <h2>你好，我是深度研究助手</h2>
              <p>我可以帮你进行深度研究、联网搜索和生成专业报告。</p>
              <div class="suggestion-chips">
                <el-tag 
                  v-for="tag in ['环境检测未来发展如何', 'AI在医疗领域的应用', '新能源汽车市场分析']" 
                  :key="tag"
                  class="suggestion-tag"
                  @click="userInput = tag"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
          </div>

          <div 
            v-for="(msg, index) in messages" 
            :key="index" 
            class="message-row"
            :class="msg.role"
          >
            <div class="avatar">
              <el-icon v-if="msg.role === 'user'"><User /></el-icon>
              <el-icon v-else><Service /></el-icon>
            </div>
            <div class="message-bubble">
              <!-- 加载中显示状态指示器 -->
              <div v-if="!msg.content && msg.isLoading" class="streaming-status">
                <div class="thinking-dots">
                  <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                </div>
                <span class="status-text">{{ msg.statusText || 'AI 正在思考中...' }}</span>
              </div>
              
              <!-- 有内容时显示文字 -->
              <div v-else-if="msg.content" class="message-content">
                <div class="message-text" v-html="formatMessage(msg.content, msg.searchResults || [])"></div>
                
                <!-- 引用列表面板 -->
                <div v-if="msg.searchResults && msg.searchResults.length > 0" class="references-section">
                  <h3 class="references-title">参考资料</h3>
                  <div class="references-list">
                    <div 
                      v-for="(result, idx) in msg.searchResults" 
                      :key="idx"
                      :id="`citation-${idx + 1}`"
                      class="reference-item"
                    >
                      <div class="reference-header">
                        <span class="reference-number">{{ idx + 1 }}</span>
                        <a :href="result.url" target="_blank" rel="noopener" class="reference-link" @click.stop>
                          {{ result.title }}
                          <svg class="external-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                          </svg>
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
                
                <span v-if="msg.isStreaming" class="cursor-blink">▍</span>
              </div>
              
              <!-- 节点执行信息 -->
              <div v-if="msg.nodeInfo && msg.nodeInfo.length > 0" class="node-info-section">
                <div class="node-info-header">
                  <el-icon><Operation /></el-icon>
                  <span>执行过程</span>
                </div>
                <div class="node-info-list">
                  <div 
                    v-for="(node, idx) in msg.nodeInfo" 
                    :key="idx"
                    class="node-info-item"
                    :class="`node-${node.type}`"
                  >
                    <span class="node-icon">{{ getNodeIcon(node.type) }}</span>
                    <span class="node-message">{{ node.message }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部输入框 -->
        <div class="input-area">
          <!-- Skills选择菜单 -->
          <div v-if="availableSkills.length > 0" class="skills-menu">
            <div 
              v-for="skill in availableSkills" 
              :key="skill.id"
              class="skill-item"
              :class="{ 'skill-active': selectedSkills.includes(skill.id) }"
              @click="toggleSkill(skill.id)"
              :style="{ borderColor: skill.color }"
            >
              <span class="skill-icon">{{ skill.icon }}</span>
              <span class="skill-name">{{ skill.name }}</span>
              <el-icon v-if="selectedSkills.includes(skill.id)" class="skill-check"><Check /></el-icon>
            </div>
          </div>
          
          <div class="input-box">
            <el-input
              v-model="userInput"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 4 }"
              placeholder="输入研究问题..."
              @keyup.enter.ctrl="sendMessage"
              :disabled="isLoading"
              resize="none"
            />
            <el-button 
              type="primary" 
              circle 
              :icon="Promotion"
              @click="sendMessage"
              :loading="isLoading"
              :disabled="!userInput.trim()"
              class="send-btn"
            />
          </div>
          <div class="input-tip">按 Ctrl + Enter 发送 · 点击Skills启用辅助功能</div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Search, Plus, User, Service, Promotion, Cpu, Operation, Check
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/api/research'
import { useResearchStore } from '@/stores/research'
import { createCitationRenderer } from '@/utils/citationRenderer'
import '@/assets/citation.css'
import { marked } from 'marked'

const route = useRoute()
const router = useRouter()
const researchStore = useResearchStore()

const userInput = ref('')
const messages = ref([])
const isLoading = ref(false)
const messageContainer = ref(null)
const currentModel = ref('openrouter/free')
const researchId = ref(route.params.id)

// Skills相关状态
const availableSkills = ref([])
const selectedSkills = ref([])
const executedSkills = ref(new Set())  // 标记已执行的Skills

const quickActions = ref([
  { label: '环境检测', icon: 'Monitor', query: '环境检测未来发展如何' },
  { label: 'AI应用', icon: 'Cpu', query: 'AI在医疗领域的应用' },
  { label: '市场分析', icon: 'TrendCharts', query: '新能源汽车市场分析' },
  { label: '技术趋势', icon: 'DataAnalysis', query: '量子计算技术发展现状' },
])

// 格式化消息（支持Markdown和引用链接）
const formatMessage = (content, searchResults = []) => {
  if (!content) return ''
  
  try {
    let html
    
    // 使用marked渲染Markdown
    html = marked.parse(content)
    
    // 后处理：替换HTML中的所有引用标记 [1]、[2]、[3]
    if (searchResults.length > 0) {
      html = html.replace(/\[(\d+)\]/g, (match, num) => {
        const index = parseInt(num) - 1
        const result = searchResults[index]
        
        if (result) {
          return `<span class="citation-link" 
                        data-url="${result.url}" 
                        data-title="${result.title}"
                        data-content="${(result.content || '').substring(0, 200)}"
                        onclick="handleCitationClick(event, ${index})"
                        onmouseenter="showCitationTooltip(event, this)"
                        onmouseleave="hideCitationTooltip()">
                    <span class="citation-number">${num}</span>
                    <span class="citation-icon">🔗</span>
                  </span>`
        }
        return match // 如果没有对应的搜索结果，返回原样
      })
    }
    
    return html
  } catch (e) {
    console.error('格式化消息失败:', e)
    return content.replace(/\n/g, '<br>')
  }
}

// 获取节点图标
const getNodeIcon = (type) => {
  const iconMap = {
    'info': 'ℹ️',
    'success': '✅',
    'warning': '⚠️',
    'error': '❌'
  }
  return iconMap[type] || 'ℹ️'
}

// 打开引用链接
const openReference = (url) => {
  if (url) {
    window.open(url, '_blank')
  }
}

// 提取域名
const extractDomain = (url) => {
  try {
    const urlObj = new URL(url)
    return urlObj.hostname.replace('www.', '')
  } catch {
    return ''
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageContainer.value) {
    // 检查用户是否正在查看历史消息（不在底部）
    const isAtBottom = messageContainer.value.scrollHeight - messageContainer.value.scrollTop - messageContainer.value.clientHeight < 50
    
    // 只有用户在底部时才自动滚动
    if (isAtBottom) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  }
}

const startNewResearch = () => {
  executedSkills.value.clear()  // 重置已执行的Skills标记
  router.push({ name: 'home' })
}

const useQuickAction = (action) => {
  userInput.value = action.query
  sendMessage()
}

// Skills相关函数
const loadSkills = async () => {
  try {
    const response = await api.getSkillsList()
    if (response.success) {
      availableSkills.value = response.data
      console.log('✅ 加载Skills列表:', availableSkills.value)
    }
  } catch (error) {
    console.error('❌ 加载Skills失败:', error)
  }
}

const toggleSkill = (skillId) => {
  const index = selectedSkills.value.indexOf(skillId)
  if (index > -1) {
    selectedSkills.value.splice(index, 1)
    ElMessage.info('已禁用该Skill')
  } else {
    selectedSkills.value.push(skillId)
    ElMessage.success('已启用该Skill')
  }
  console.log('🔧 当前选中的Skills:', selectedSkills.value)
}

// 直接执行引用验证（不需要完整research对象）
const executeCitationValidatorDirect = async (citations) => {
  try {
    const response = await fetch('/api/skills/validate-citations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ citations })
    })
    
    const data = await response.json()
    return { skill: '引用链接验证Skill', success: true, data }
  } catch (error) {
    return { skill: '引用链接验证Skill', success: false, error: error.message }
  }
}

// 直接执行搜索评估（不需要完整research对象）
const executeSearchEvaluatorDirect = async (results, query) => {
  try {
    const response = await fetch('/api/skills/evaluate-search-results', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results, query })
    })
    
    const data = await response.json()
    return { skill: '搜索结果质量评估Skill', success: true, data }
  } catch (error) {
    return { skill: '搜索结果质量评估Skill', success: false, error: error.message }
  }
}

// 执行大纲优化
const executeOutlineOptimizer = async (data) => {
  try {
    const response = await fetch('/api/skills/optimize-outline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    
    const result = await response.json()
    return { skill: '大纲优化Skill', success: true, data: result }
  } catch (error) {
    return { skill: '大纲优化Skill', success: false, error: error.message }
  }
}

// 显示Skill结果
const displaySkillResults = (results) => {
  let skillMessage = '## 🔧 Skills分析结果\n\n'
  
  results.forEach((result, index) => {
    if (result.status === 'fulfilled') {
      const skillResult = result.value
      skillMessage += `### ${skillResult.skill}\n\n`
      
      if (skillResult.success) {
        const data = skillResult.data
        
        // 根据Skill类型显示不同内容
        if (skillResult.skill === '大纲优化Skill') {
          skillMessage += `- **综合评分**: ${data.overall_score}/100\n`
          skillMessage += `- **建议数量**: ${data.suggestions?.length || 0}条\n`
          skillMessage += `- **缺失主题**: ${data.missing_topics?.length || 0}个\n\n`
          
          if (data.suggestions && data.suggestions.length > 0) {
            skillMessage += '**优化建议**:\n'
            data.suggestions.slice(0, 3).forEach((suggestion, i) => {
              skillMessage += `${i + 1}. ${suggestion}\n`
            })
            skillMessage += '\n'
          }
        } else if (skillResult.skill === '引用链接验证Skill') {
          skillMessage += `- **有效引用**: ${data.valid_count}个\n`
          skillMessage += `- **无效引用**: ${data.invalid_count}个\n`
          skillMessage += `- **整体评分**: ${data.overall_score}%\n\n`
        } else if (skillResult.skill === '搜索结果质量评估Skill') {
          skillMessage += `- **平均评分**: ${data.average_score}/100\n`
          skillMessage += `- **结果总数**: ${data.total_results}个\n`
          skillMessage += `- **高质量结果**: ${data.high_quality_count}个\n\n`
        }
      } else {
        skillMessage += `❌ 执行失败: ${skillResult.error}\n\n`
      }
    } else {
      skillMessage += `❌ 执行异常: ${result.reason}\n\n`
    }
  })
  
  // 添加Skill结果到消息列表
  messages.value.push({
    role: 'assistant',
    content: skillMessage,
    isLoading: false,
    isStreaming: false,
    nodeInfo: [],
    showProcess: true,
    searchResults: []
  })
  
  scrollToBottom()
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const userMessage = userInput.value.trim()
  
  // 添加用户消息
  messages.value.push({ 
    role: 'user', 
    content: userMessage,
    isLoading: false,
    isStreaming: false,
    nodeInfo: []
  })
  
  userInput.value = ''
  isLoading.value = true
  
  // 添加助手消息（初始为空）
  const assistantMsgIndex = messages.value.length
  messages.value.push({ 
    role: 'assistant', 
    content: '',
    searchResults: [],  // 添加搜索结果数组
    isLoading: true,
    isStreaming: false,
    statusText: '开始分析您的问题...',
    nodeInfo: []
  })
  
  await scrollToBottom()

  try {
    // 开始研究
    const response = await researchStore.startResearch(userMessage)
    researchId.value = response.research_id
    
    // 更新助手消息状态
    messages.value[assistantMsgIndex].statusText = '研究已开始，正在执行工作流...'
    
    // 轮询获取进度和日志
    await pollProgress(assistantMsgIndex)
    
  } catch (error) {
    console.error('研究失败:', error)
    messages.value[assistantMsgIndex].content = `研究失败：${error.message}`
    messages.value[assistantMsgIndex].isLoading = false
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

// 轮询进度
const pollProgress = async (assistantMsgIndex) => {
  // 清理之前的轮询
  cleanupTasks()
  
  currentPollInterval = setInterval(async () => {
    try {
      const progress = await api.getProgress(researchId.value)
      
      // 更新节点信息
      if (progress.progress_logs && progress.progress_logs.length > 0) {
        messages.value[assistantMsgIndex].nodeInfo = progress.progress_logs
        
        // 根据最新日志更新状态文本
        const lastLog = progress.progress_logs[progress.progress_logs.length - 1]
        if (lastLog) {
          messages.value[assistantMsgIndex].statusText = lastLog.message
        }
      }
      
      await scrollToBottom()
      
      // 如果研究完成，停止轮询并获取报告
      if (progress.status === 'completed') {
        clearInterval(currentPollInterval)
        currentPollInterval = null
        messages.value[assistantMsgIndex].isLoading = false
        messages.value[assistantMsgIndex].isStreaming = true
        messages.value[assistantMsgIndex].statusText = '正在生成研究报告...'
        
        // 流式获取报告
        await streamReport(assistantMsgIndex)
      }
    } catch (error) {
      console.error('获取进度失败:', error)
    }
  }, 2000) // 每2秒轮询一次
}

// 流式获取报告
const streamReport = async (assistantMsgIndex) => {
  return new Promise((resolve, reject) => {
    // 清理之前的SSE连接
    cleanupTasks()
    
    currentEventSource = api.streamReport(
      researchId.value,
      // onChunk
      (content) => {
        if (content) {
          messages.value[assistantMsgIndex].content += content
          scrollToBottom()
        }
      },
      // onDone
      () => {
        messages.value[assistantMsgIndex].isStreaming = false
        messages.value[assistantMsgIndex].statusText = '研究完成！'
        currentEventSource = null  // 清理引用
        ElMessage.success('研究报告生成完成！')
        resolve()
      },
      // onError
      (error) => {
        console.error('流式输出失败:', error)
        messages.value[assistantMsgIndex].isStreaming = false
        messages.value[assistantMsgIndex].statusText = '报告生成完成（流式失败）'
        currentEventSource = null  // 清理引用
        reject(error)
      },
      // onSearchResults - 接收搜索结果数据
      (searchResults) => {
        console.log('📥 收到SSE searchResults事件')
        console.log('📥 searchResults类型:', typeof searchResults)
        console.log('📥 searchResults长度:', searchResults?.length)
        if (searchResults && searchResults.length > 0) {
          console.log('📥 第一条数据:', searchResults[0])
        }
        messages.value[assistantMsgIndex].searchResults = searchResults || []
        console.log('✅ 已存储searchResults:', messages.value[assistantMsgIndex].searchResults.length, '个')
      }
    )
  })
}

// 存储当前的异步任务引用
let currentPollInterval = null
let currentEventSource = null

// 清理所有异步任务
const cleanupTasks = () => {
  // 清理轮询定时器
  if (currentPollInterval) {
    clearInterval(currentPollInterval)
    currentPollInterval = null
  }
  
  // 清理SSE连接
  if (currentEventSource) {
    currentEventSource.close()
    currentEventSource = null
  }
}

// 监听路由变化，加载已有研究
watch(() => route.params.id, (newId, oldId) => {
  // 路由变化时，清理旧任务并清空消息
  if (oldId && newId !== oldId) {
    cleanupTasks()  // 清理异步任务
    messages.value = []
  }
  
  if (newId) {
    researchId.value = newId
    loadExistingResearch()
  }
}, { immediate: true })

const loadExistingResearch = async () => {
  if (!researchId.value) return
  
  try {
    const research = await researchStore.getProgress(researchId.value)
    
    // 添加用户消息
    messages.value.push({
      role: 'user',
      content: research.query,
      isLoading: false,
      isStreaming: false,
      nodeInfo: []
    })
    
    // 添加助手消息
    const assistantMsgIndex = messages.value.length
    messages.value.push({
      role: 'assistant',
      content: '',
      isLoading: research.status !== 'completed',
      isStreaming: false,
      statusText: research.status === 'completed' ? '研究已完成' : '研究进行中...',
      nodeInfo: research.progress_logs || []
    })
    
    // 如果已完成，加载报告
    if (research.status === 'completed') {
      messages.value[assistantMsgIndex].isLoading = false
      messages.value[assistantMsgIndex].isStreaming = true
      await streamReport(assistantMsgIndex)
    } else {
      // 否则继续轮询
      await pollProgress(assistantMsgIndex)
    }
  } catch (error) {
    console.error('加载研究失败:', error)
    ElMessage.error('加载研究失败')
  }
}

// 全局引用悬浮提示功能
if (typeof window !== 'undefined') {
  window.showCitationTooltip = (event, element) => {
    const url = element.dataset.url
    const title = element.dataset.title
    const content = element.dataset.content
    
    // 移除已存在的tooltip
    hideCitationTooltip()
    
    // 创建tooltip
    const tooltip = document.createElement('div')
    tooltip.id = 'citation-tooltip'
    tooltip.className = 'citation-tooltip'
    tooltip.innerHTML = `
      <div class="tooltip-header">
        <span class="tooltip-icon">🔗</span>
        <span class="tooltip-title">${title}</span>
      </div>
      <div class="tooltip-content">${content}...</div>
      <div class="tooltip-footer">
        <span class="tooltip-url">${url}</span>
      </div>
    `
    
    document.body.appendChild(tooltip)
    
    // 定位tooltip
    const rect = element.getBoundingClientRect()
    tooltip.style.position = 'fixed'
    tooltip.style.top = (rect.bottom + 8) + 'px'
    tooltip.style.left = rect.left + 'px'
    tooltip.style.zIndex = '10000'
  }

  window.hideCitationTooltip = () => {
    const tooltip = document.getElementById('citation-tooltip')
    if (tooltip) {
      tooltip.remove()
    }
  }
}

// 组件挂载时加载Skills
onMounted(() => {
  loadSkills()
})
</script>

<style scoped>
/* 隐藏全局滚动条 */
html, body {
  overflow: hidden !important;
  scrollbar-width: none !important;
  -ms-overflow-style: none !important;
}

html::-webkit-scrollbar, body::-webkit-scrollbar {
  display: none !important;
}

.chat-layout {
  display: flex;
  height: 100vh;
  background-color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
}

/* 左侧导航栏 */
.sidebar {
  width: 260px;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  padding: 20px;
  transition: all 0.3s;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
  color: #111827;
  font-weight: 600;
  font-size: 18px;
}

.logo-icon {
  font-size: 24px;
  color: #667eea;
}

.new-research-btn {
  margin-bottom: 24px;
}

.history-label {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #4b5563;
  font-size: 14px;
  transition: background 0.2s;
}

.history-item:hover {
  background: #e5e7eb;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.model-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6b7280;
  background: #fff;
  padding: 8px 12px;
  border-radius: 20px;
  border: 1px solid #e5e7eb;
}

/* 右侧主聊天区 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.chat-container {
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.message-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 40px 20px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.message-wrapper::-webkit-scrollbar {
  display: none;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.welcome-card {
  text-align: center;
  max-width: 600px;
}

.welcome-card h2 {
  font-size: 28px;
  color: #111827;
  margin-bottom: 12px;
}

.welcome-card p {
  color: #6b7280;
  margin-bottom: 32px;
}

.suggestion-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.suggestion-tag {
  cursor: pointer;
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 20px;
}

.message-row {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  flex-shrink: 0;
}

.message-row.user .avatar {
  background: #667eea;
  color: white;
}

.message-bubble {
  max-width: 85%;
  width: fit-content;
  padding: 16px 20px;
  border-radius: 12px;
  background: #f3f4f6;
  color: #1f2937;
  line-height: 1.6;
  font-size: 15px;
  overflow: hidden;
  word-wrap: break-word;
}

.message-row.user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 流式输出状态指示器 */
.streaming-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.thinking-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  animation: thinking 1.4s infinite ease-in-out both;
}

.thinking-dots .dot:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots .dot:nth-child(2) { animation-delay: -0.16s; }
.thinking-dots .dot:nth-child(3) { animation-delay: 0s; }

.status-text {
  color: #909399;
  font-size: 14px;
  font-style: italic;
}

@keyframes thinking {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 流式输出时的光标 */
.cursor-blink {
  display: inline-block;
  color: #667eea;
  font-weight: bold;
  font-size: 16px;
  line-height: 1;
  animation: blink 1s infinite;
  margin-left: 2px;
  vertical-align: text-bottom;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.message-text {
  word-wrap: break-word;
  line-height: 1.6;
  display: inline;
}

.message-content {
  display: inline;
}

/* 节点执行信息区域 */
.node-info-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.node-info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
}

.node-info-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.node-info-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.node-info {
  background-color: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.node-success {
  background-color: #f6ffed;
  border-left: 3px solid #52c41a;
}

.node-warning {
  background-color: #fffbe6;
  border-left: 3px solid #faad14;
}

.node-error {
  background-color: #fff2f0;
  border-left: 3px solid #ff4d4f;
}

.node-icon {
  flex-shrink: 0;
  font-size: 14px;
}

.node-message {
  flex: 1;
  color: #4b5563;
}

/* 输入区域 */
.input-area {
  padding: 24px;
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
}

/* Skills选择菜单 */
.skills-menu {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.skill-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 20px;
  border: 2px solid #e5e7eb;
  background: #f9fafb;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  color: #6b7280;
  user-select: none;
}

.skill-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background: #ffffff;
}

.skill-item.skill-active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  color: #667eea;
  font-weight: 600;
  border-width: 2px;
}

.skill-icon {
  font-size: 16px;
}

.skill-name {
  white-space: nowrap;
}

.skill-check {
  font-size: 14px;
  color: #667eea;
}

.input-box {
  position: relative;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 12px;
  background: #f9fafb;
  transition: all 0.2s;
}

.input-box:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  background: #fff;
}

.send-btn {
  position: absolute;
  right: 16px;
  bottom: 16px;
}

.input-tip {
  text-align: right;
  font-size: 12px;
  color: #9ca3af;
  margin-top: 8px;
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .chat-container { max-width: 100%; }
}
</style>
