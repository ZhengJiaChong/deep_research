/**
 * marked扩展：支持引用链接和悬浮预览
 */

import { marked } from 'marked'

// 创建自定义渲染器
export const createCitationRenderer = (searchResults = []) => {
  const renderer = {
    // 重写文本渲染（处理纯文本引用标记 [1]、[2]）
    text(token) {
      // token.text 是文本内容
      let text = token.text
      
      // 匹配引用标记 [1]、[2]、[3] 等
      text = text.replace(/\[(\d+)\]/g, (match, num) => {
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
      
      return text
    },
    
    // 重写链接渲染（处理Markdown链接）
    link(token) {
      const { href, title, text } = token
      
      // 检查是否是引用标记（如 [1], [2]）
      const citationMatch = text.match(/^\[?(\d+)\]?$/)
      if (citationMatch) {
        const index = parseInt(citationMatch[1]) - 1
        const result = searchResults[index]
        
        if (result) {
          return `<span class="citation-link" 
                        data-url="${result.url}" 
                        data-title="${result.title}"
                        data-content="${(result.content || '').substring(0, 200)}"
                        onclick="window.open('${result.url}', '_blank')"
                        onmouseenter="showCitationTooltip(event, this)"
                        onmouseleave="hideCitationTooltip()">
                    <span class="citation-number">${index + 1}</span>
                    <span class="citation-icon">🔗</span>
                  </span>`
        }
      }
      
      // 普通链接
      return `<a href="${href}" target="_blank" class="external-link">${text}</a>`
    }
  }
  
  return renderer
}

// 显示引用悬浮提示
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

// 隐藏引用悬浮提示
window.hideCitationTooltip = () => {
  const tooltip = document.getElementById('citation-tooltip')
  if (tooltip) {
    tooltip.remove()
  }
}

// 处理引用点击（滚动到对应引用）
window.handleCitationClick = (event, index) => {
  event.preventDefault()
  const targetElement = document.getElementById(`citation-${index + 1}`)
  
  if (targetElement) {
    // 移除之前的高亮
    document.querySelectorAll('.reference-item.highlight').forEach(el => {
      el.classList.remove('highlight')
    })
    
    // 滚动到目标
    targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    
    // 添加高亮效果
    setTimeout(() => {
      targetElement.classList.add('highlight')
    }, 300)
    
    // 2秒后移除高亮
    setTimeout(() => {
      targetElement.classList.remove('highlight')
    }, 2300)
  }
}

// 导出格式化函数
export const formatMessageWithCitations = (content, searchResults = []) => {
  if (!content) return ''
  
  try {
    const renderer = createCitationRenderer(searchResults)
    
    return marked.parse(content, {
      breaks: true,
      gfm: true,
      renderer: renderer,
    })
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return content
  }
}
