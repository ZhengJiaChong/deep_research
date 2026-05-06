<template>
  <div class="home-split-layout">
    <!-- 左侧历史对话 -->
    <aside class="history-sidebar">
      <div class="sidebar-header">
        <el-icon class="logo-icon"><Search /></el-icon>
        <span class="app-title">深度研究</span>
      </div>
      
      <div class="new-chat-btn">
        <el-button type="primary" :icon="Plus" @click="startNewChat" block>
          新对话
        </el-button>
      </div>

      <div class="history-list">
        <div class="history-label">历史对话</div>
        <div 
          v-for="(chat, index) in chatHistory" 
          :key="chat.id || index"
          class="history-item"
          :class="{ active: currentChatIndex === index }"
          @click="loadChat(index)"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span class="history-text">{{ chat.query }}</span>
          <el-icon 
            class="delete-btn" 
            @click.stop="deleteHistoryChat(index, chat.id)"
          >
            <Close />
          </el-icon>
        </div>
        <div v-if="chatHistory.length === 0" class="empty-history">
          暂无历史记录
        </div>
      </div>
    </aside>

    <!-- 右侧聊天区 -->
    <main class="chat-main">
      <div class="chat-container">
        <!-- 消息列表 -->
        <div class="message-wrapper" ref="messageContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <div class="welcome-card">
              <h2>你好，我是深度研究助手</h2>
              <p>输入问题，我将进行深度联网搜索和专业分析</p>
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
              <!-- 加载中状态 -->
              <div v-if="!msg.content && msg.isLoading" class="streaming-status">
                <div class="thinking-dots">
                  <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                </div>
                <span class="status-text">{{ msg.statusText || 'AI 正在思考中...' }}</span>
              </div>
              
              <!-- 执行过程（可折叠） -->
              <div v-if="msg.nodeInfo && msg.nodeInfo.length > 0" class="process-section">
                <div class="process-header" @click="toggleProcess(msg)">
                  <el-icon><component :is="msg.showProcess ? 'ArrowDown' : 'ArrowRight'" /></el-icon>
                  <span>执行过程 ({{ msg.nodeInfo.length }}步)</span>
                </div>
                <div v-show="msg.showProcess" class="process-list">
                  <div 
                    v-for="(node, idx) in msg.nodeInfo" 
                    :key="idx"
                    class="process-item"
                    :class="[
                      `process-${node.type}`,
                      { 'keyword-line': node.keyword },
                      { 'results-line': node.search_results }
                    ]"
                  >
                    <span class="process-icon">{{ getNodeIcon(node.type) }}</span>
                    <div class="process-content">
                      <span class="process-message">{{ node.message }}</span>
                      <!-- 显示搜索结果列表 -->
                      <div v-if="node.search_results && node.search_results.length > 0" class="results-list">
                        <div v-for="(result, rIdx) in node.search_results" :key="rIdx" class="result-item">
                          <span class="result-index">{{ rIdx + 1 }}</span>
                          <span class="result-title">{{ result }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 报告内容 -->
              <div v-if="msg.content" class="message-content">
                <div class="report-header" v-if="msg.content">
                  <el-icon><Document /></el-icon>
                  <span>研究报告</span>
                </div>
                <div class="message-text" v-html="formatMessage(msg.content)"></div>
                <span v-if="msg.isStreaming" class="cursor-blink">▍</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部输入框 -->
        <div class="input-area">
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
          <div class="input-tip">按 Ctrl + Enter 发送</div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useResearchStore } from '../stores/research'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { 
  Promotion, Search, Plus, User, Service, Document, 
  ChatDotRound, ArrowDown, ArrowRight, Close
} from '@element-plus/icons-vue'
import api from '@/api/research'
import { saveChatToDB, getAllChats, updateChat, deleteChat } from '@/services/chatHistoryDB'

const router = useRouter()
const researchStore = useResearchStore()

const userInput = ref('')
const messages = ref([])
const isLoading = ref(false)
const messageContainer = ref(null)
const chatHistory = ref([])
const currentChatIndex = ref(-1)

// 页面加载时从数据库读取历史
onMounted(async () => {
  await loadHistoryFromDB()
})

// 格式化消息
const formatMessage = (content) => {
  if (!content) return ''
  
  // 使用marked库渲染Markdown
  try {
    return marked.parse(content, {
      breaks: true,  // 支持换行
      gfm: true,     // GitHub风格Markdown
    })
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return content
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

const scrollToBottom = async () => {
  await nextTick()
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
}

// 切换执行过程显示
const toggleProcess = (msg) => {
  msg.showProcess = !msg.showProcess
}

// 从数据库加载历史
const loadHistoryFromDB = async () => {
  try {
    const chats = await getAllChats()
    chatHistory.value = chats.map(chat => ({
      id: chat.id,
      query: chat.query,
      researchId: chat.researchId,
      messages: chat.messages || [],
      timestamp: chat.timestamp
    }))
  } catch (error) {
    console.error('加载历史失败:', error)
  }
}

// 删除历史对话
const deleteHistoryChat = async (index, chatId) => {
  try {
    // 从数据库删除
    if (chatId) {
      await deleteChat(chatId)
    }
    
    // 从本地状态删除
    chatHistory.value.splice(index, 1)
    
    // 如果删除的是当前对话，清空消息
    if (currentChatIndex.value === index) {
      startNewChat()
    } else if (currentChatIndex.value > index) {
      // 调整当前索引
      currentChatIndex.value--
    }
    
    ElMessage.success('已删除')
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

// 开始新对话
const startNewChat = () => {
  messages.value = []
  currentChatIndex.value = -1
  userInput.value = ''
  currentChatDBId = null  // 重置数据库ID
}

// 加载历史对话
const loadChat = (index) => {
  currentChatIndex.value = index
  const chat = chatHistory.value[index]
  
  // 恢复消息
  messages.value = chat.messages || []
  
  // 设置当前数据库ID（用于后续更新）
  currentChatDBId = chat.id || null
  
  // 如果研究未完成，继续轮询
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isLoading) {
    pollProgress(messages.value.length - 1, chat.researchId)
  }
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const userMessage = userInput.value.trim()
  
  // 新对话，重置数据库ID
  currentChatDBId = null
  
  // 添加用户消息
  messages.value.push({ 
    role: 'user', 
    content: userMessage,
    isLoading: false,
    isStreaming: false,
    nodeInfo: [],
    showProcess: true  // 默认展开执行过程
  })
  
  userInput.value = ''
  isLoading.value = true
  
  // 添加助手消息
  const assistantMsgIndex = messages.value.length
  messages.value.push({ 
    role: 'assistant', 
    content: '',
    isLoading: true,
    isStreaming: false,
    statusText: '开始分析您的问题...',
    nodeInfo: [],
    showProcess: true
  })
  
  await scrollToBottom()

  try {
    // 开始研究
    const response = await researchStore.startResearch(userMessage)
    const researchId = response.research_id
    
    // 更新助手消息
    messages.value[assistantMsgIndex].statusText = '研究已开始，正在执行工作流...'
    
    // 轮询进度
    await pollProgress(assistantMsgIndex, researchId)
    
    // 保存到历史记录
    await saveToHistory(userMessage, researchId)
    
  } catch (error) {
    console.error('研究失败:', error)
    messages.value[assistantMsgIndex].content = `研究失败：${error.message}`
    messages.value[assistantMsgIndex].isLoading = false
    
    // 即使失败也保存历史记录
    await saveToHistory(userMessage, researchId || 'failed')
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

// 当前研究的数据库ID（用于更新）
let currentChatDBId = null

// 保存到历史记录
const saveToHistory = async (query, researchId) => {
  console.log(' 准备保存历史记录:', { query, researchId })
  
  // 使用JSON序列化/反序列化清理不可克隆的对象
  const cleanMessages = JSON.parse(JSON.stringify(messages.value))
  
  const chatData = {
    query,
    researchId,
    messages: cleanMessages,
    timestamp: new Date().toISOString()
  }
  
  try {
    let id
    
    if (currentChatDBId) {
      // 更新已有记录
      console.log(' 更新已有历史记录，ID:', currentChatDBId)
      await updateChat(currentChatDBId, chatData)
      id = currentChatDBId
      
      // 更新本地状态
      const index = chatHistory.value.findIndex(c => c.id === currentChatDBId)
      if (index !== -1) {
        chatHistory.value[index] = { id, ...chatData }
      }
    } else {
      // 创建新记录
      id = await saveChatToDB(chatData)
      console.log('✅ 创建新历史记录，ID:', id)
      currentChatDBId = id
      
      // 更新本地状态
      chatHistory.value.unshift({
        id,
        ...chatData
      })
      
      // 限制历史记录数量（最多50条）
      if (chatHistory.value.length > 50) {
        const toRemove = chatHistory.value.pop()
        if (toRemove.id) {
          await deleteChat(toRemove.id)
        }
      }
    }
  } catch (error) {
    console.error('❌ 保存历史失败:', error)
  }
}

// 轮询进度
const pollProgress = async (assistantMsgIndex, researchId) => {
  const pollInterval = setInterval(async () => {
    try {
      const progress = await api.getProgress(researchId)
      
      // 更新节点信息
      if (progress.progress_logs && progress.progress_logs.length > 0) {
        messages.value[assistantMsgIndex].nodeInfo = progress.progress_logs
        
        // 更新状态文本
        const lastLog = progress.progress_logs[progress.progress_logs.length - 1]
        if (lastLog) {
          messages.value[assistantMsgIndex].statusText = lastLog.message
        }
      }
      
      await scrollToBottom()
      
      // 研究完成
      if (progress.status === 'completed') {
        clearInterval(pollInterval)
        messages.value[assistantMsgIndex].isLoading = false
        messages.value[assistantMsgIndex].isStreaming = true
        messages.value[assistantMsgIndex].statusText = '正在生成研究报告...'
        
        // 流式获取报告
        await streamReport(assistantMsgIndex, researchId)
        
        // 从消息中获取用户问题
        const userQuery = messages.value[assistantMsgIndex - 1]?.content || '未知问题'
        
        // 更新历史记录
        if (currentChatIndex.value >= 0) {
          const currentChat = chatHistory.value[currentChatIndex.value]
          if (currentChat && currentChat.id) {
            // 更新数据库中的消息
            await updateChat(currentChat.id, { messages: [...messages.value] })
          }
          chatHistory.value[currentChatIndex.value].messages = [...messages.value]
        }
      }
    } catch (error) {
      console.error('获取进度失败:', error)
      
      // 如果是404（研究不存在），停止轮询
      if (error.message && error.message.includes('研究不存在')) {
        console.warn('研究已被删除或服务器重启，停止轮询')
        clearInterval(pollInterval)
        messages.value[assistantMsgIndex].isLoading = false
        messages.value[assistantMsgIndex].statusText = '研究数据已丢失（服务器重启）'
      }
    }
  }, 1000)  // 改为1秒轮询一次，提供更流畅的流式体验
}

// 流式获取报告
const streamReport = async (assistantMsgIndex, researchId) => {
  return new Promise((resolve, reject) => {
    const eventSource = api.streamReport(
      researchId,
      // onChunk
      (content) => {
        if (content) {
          messages.value[assistantMsgIndex].content += content
          scrollToBottom()
        }
      },
      // onDone
      async () => {
        messages.value[assistantMsgIndex].isStreaming = false
        messages.value[assistantMsgIndex].statusText = '研究完成！'
        ElMessage.success('研究报告生成完成！')
        
        // 流式完成后，再次保存（包含完整报告）
        await saveToHistory(messages.value[0]?.content || '', researchId)
        
        resolve()
      },
      // onError
      (error) => {
        console.error('流式输出失败:', error)
        messages.value[assistantMsgIndex].isStreaming = false
        messages.value[assistantMsgIndex].statusText = '报告生成完成（流式失败）'
        reject(error)
      }
    )
  })
}
</script>

<!-- 隐藏全局滚动条 -->
<style>
html, body {
  overflow: hidden !important;
  scrollbar-width: none !important; /* Firefox */
  -ms-overflow-style: none !important; /* IE/Edge */
}

html::-webkit-scrollbar, body::-webkit-scrollbar {
  display: none !important; /* Chrome/Safari */
}

/* 确保标题完整显示 */
.sidebar-header {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  margin-bottom: 24px !important;
  color: #111827 !important;
  font-weight: 600 !important;
  font-size: 18px !important;
  white-space: nowrap !important;
  overflow: visible !important;
}

.app-title {
  flex: 1 !important;
  overflow: visible !important;
  text-overflow: initial !important;
  white-space: nowrap !important;
  min-width: 0 !important;
}

.logo-icon {
  flex-shrink: 0 !important;
  font-size: 24px !important;
  color: #667eea !important;
}
</style>

<style scoped>
.home-split-layout {
  display: flex;
  height: 100vh;
  background-color: #ffffff;
  overflow: hidden;
}

/* 左侧历史对话 */
.history-sidebar {
  width: 300px;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  padding: 16px;
  transition: width 0.3s ease;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
  color: #111827;
  font-weight: 600;
  font-size: 18px;
  white-space: nowrap;
}

.app-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logo-icon {
  font-size: 24px;
  color: #667eea;
}

.new-chat-btn {
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
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #4b5563;
  font-size: 14px;
  transition: all 0.2s;
  margin-bottom: 8px;
  position: relative;
}

.history-item:hover {
  background: #e5e7eb;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.history-item.active {
  background: #667eea;
  color: white;
}

.history-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  opacity: 0;
  font-size: 16px;
  color: #9ca3af;
  transition: all 0.2s;
  padding: 4px;
  border-radius: 4px;
}

.delete-btn:hover {
  color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}

.empty-history {
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
  padding: 40px 0;
}

/* 右侧主聊天区 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
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
}

.message-row.user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 流式输出状态 */
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

/* 执行过程区域 */
.process-section {
  margin-top: 16px;
  border-top: 1px solid #e5e7eb;
  padding-top: 12px;
}

.process-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
  transition: background 0.2s;
}

.process-header:hover {
  background: #e5e7eb;
}

.process-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.process-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
  animation: slideIn 0.3s ease;
}

/* 关键词行特殊样式 */
.process-item.keyword-line {
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  border-left: 3px solid #667eea;
  font-weight: 500;
}

/* 搜索结果行特殊样式 */
.process-item.results-line {
  background: linear-gradient(135deg, #10b98115 0%, #05966915 100%);
  border-left: 3px solid #10b981;
}

.process-content {
  flex: 1;
}

/* 搜索结果列表 */
.results-list {
  margin-top: 8px;
  padding-left: 24px;
}

.result-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
  color: #4b5563;
  line-height: 1.4;
}

.result-index {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  background: #10b981;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
}

.result-title {
  flex: 1;
  word-break: break-word;
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

.process-info {
  background-color: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.process-success {
  background-color: #f6ffed;
  border-left: 3px solid #52c41a;
}

.process-warning {
  background-color: #fffbe6;
  border-left: 3px solid #faad14;
}

.process-error {
  background-color: #fff2f0;
  border-left: 3px solid #ff4d4f;
}

.process-icon {
  flex-shrink: 0;
  font-size: 14px;
}

.process-message {
  flex: 1;
  color: #4b5563;
}

/* 报告头部 */
.report-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
  font-weight: 600;
  color: #667eea;
}

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
}

/* 输入区域 */
.input-area {
  padding: 24px;
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
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
@media (max-width: 1200px) {
  .history-sidebar {
    width: 260px;
  }
  
  .welcome-card h2 {
    font-size: 24px;
  }
}

@media (max-width: 768px) {
  /* 隐藏侧边栏，添加汉堡菜单按钮 */
  .history-sidebar { 
    display: none; 
  }
  
  .chat-container { 
    max-width: 100%; 
  }
  
  /* 消息气泡调整 */
  .message-bubble {
    max-width: 90%;
    padding: 12px 16px;
    font-size: 14px;
  }
  
  /* 欢迎卡片调整 */
  .welcome-card {
    padding: 0 20px;
  }
  
  .welcome-card h2 {
    font-size: 22px;
  }
  
  .welcome-card p {
    font-size: 14px;
  }
  
  /* 建议标签调整 */
  .suggestion-chips {
    gap: 8px;
  }
  
  .suggestion-tag {
    padding: 6px 12px;
    font-size: 13px;
  }
  
  /* 输入区域调整 */
  .input-area {
    padding: 16px;
  }
  
  .message-wrapper {
    padding: 20px 16px;
  }
}

@media (max-width: 480px) {
  /* 小屏幕进一步优化 */
  .welcome-card h2 {
    font-size: 20px;
  }
  
  .message-bubble {
    max-width: 95%;
    padding: 10px 14px;
    font-size: 13px;
  }
  
  .avatar {
    width: 32px;
    height: 32px;
  }
  
  .process-list {
    max-height: 200px;
  }
  
  .process-item {
    font-size: 12px;
    padding: 6px 10px;
  }
}
</style>
