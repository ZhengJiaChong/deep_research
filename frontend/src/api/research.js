import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,  // 5分钟（研报生成需要较长时间）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API请求失败:', error.config?.url, error.response?.status, error.response?.data)
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// API方法
export default {
  // 开始研究
  startResearch(query) {
    console.log('🚀 前端发送研究请求:', query)
    console.log('🚀 请求URL: /api/research/start')
    return api.post('/research/start', { query })
      .then(response => {
        console.log('✅ 后端响应:', response)
        return response
      })
      .catch(error => {
        console.error('❌ 请求失败:', error.message)
        console.error('❌ 错误详情:', error.response?.status, error.response?.data)
        throw error
      })
  },
  
  // 获取大纲
  getOutline(researchId) {
    return api.get(`/research/${researchId}/outline`)
  },
  
  // 获取进度
  getProgress(researchId) {
    return api.get(`/research/${researchId}/progress`)
  },
  
  // 获取报告
  getReport(researchId) {
    return api.get(`/research/${researchId}/report`)
  },
  
  // 流式获取报告
  streamReport(researchId, onChunk, onDone, onError, onSearchResults) {
    const url = `/api/research/${researchId}/stream`  // EventSource需要完整路径
    const eventSource = new EventSource(url)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.error) {
          console.error('SSE错误:', data.error)
          onError(data.error)
          eventSource.close()
          return
        }
        
        // 处理searchResults数据（引用链接）
        if (data.searchResults) {
          if (onSearchResults) {
            onSearchResults(data.searchResults)
          }
          return
        }
        
        onChunk(data.content)
        
        if (data.done) {
          eventSource.close()
          onDone()
        }
      } catch (e) {
        console.error('解析SSE数据失败:', e)
      }
    }
    
    eventSource.onerror = (error) => {
      console.error('SSE连接错误:', error)
      onError('流式输出连接失败')
      eventSource.close()
    }
    
    return eventSource
  },
  
  // Skills相关API
  
  // 获取可用Skills列表
  getSkillsList() {
    return api.get('/skills/list')
  },
  
  // 大纲优化
  optimizeOutline(outline, query) {
    return api.post('/skills/optimize-outline', { outline, query })
  },
  
  // 引用验证
  validateCitations(citations) {
    return api.post('/skills/validate-citations', { citations })
  },
  
  // 搜索评估
  evaluateSearchResults(results, query) {
    return api.post('/skills/evaluate-search-results', { results, query })
  }
}
