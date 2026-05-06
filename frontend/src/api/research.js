import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
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
    return api.post('/research/start', { query })
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
  streamReport(researchId, onChunk, onDone, onError) {
    const url = `/api/research/${researchId}/stream`
    const eventSource = new EventSource(url)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.error) {
          onError(data.error)
          eventSource.close()
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
  }
}
