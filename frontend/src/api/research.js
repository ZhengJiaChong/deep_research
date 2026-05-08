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
    console.log('🔗 SSE连接URL:', url)
    const eventSource = new EventSource(url)
    
    eventSource.onopen = () => {
      console.log('✅ SSE连接已建立')
    }
    
    eventSource.onmessage = (event) => {
      console.log('📨 收到SSE原始数据:', event.data.substring(0, 100))
      try {
        const data = JSON.parse(event.data)
        console.log('📦 解析后的数据keys:', Object.keys(data))
        
        if (data.error) {
          console.error('❌ SSE错误:', data.error)
          onError(data.error)
          eventSource.close()
          return
        }
        
        // 处理searchResults数据（引用链接）
        if (data.searchResults) {
          console.log('📊 检测到searchResults字段')
          console.log('📊 onSearchResults回调是否存在:', typeof onSearchResults)
          console.log('📊 searchResults长度:', data.searchResults.length)
          
          if (onSearchResults) {
            console.log('📊 调用onSearchResults回调')
            onSearchResults(data.searchResults)
            console.log('✅ onSearchResults回调执行完成')
          } else {
            console.warn('⚠️ onSearchResults回调未定义')
          }
          return
        }
        
        onChunk(data.content)
        
        if (data.done) {
          console.log('✅ SSE流结束')
          eventSource.close()
          onDone()
        }
      } catch (e) {
        console.error('❌ 解析SSE数据失败:', e)
        console.error('原始数据:', event.data)
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
