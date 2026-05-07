"""
备用搜索引擎 - 使用Brave Search API
免费额度：2000次/月
注册：https://brave.com/search/api/
"""
import httpx
from typing import List, Dict, Any
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("BraveSearch")

class BraveSearchService:
    """Brave搜索引擎"""
    
    def __init__(self):
        self.api_key = settings.BRAVE_API_KEY
        self.available = bool(self.api_key)
        if self.available:
            logger.info("✅ Brave搜索引擎已初始化")
        else:
            logger.warning("⚠️ Brave搜索引擎未配置API Key")
            logger.warning("请获取API Key: https://brave.com/search/api/")
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """执行Brave搜索"""
        if not self.available:
            logger.error("❌ Brave API Key未配置")
            return []
        
        try:
            logger.info(f"🦁 Brave搜索: {query[:50]}...")
            
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                'X-Subscription-Token': self.api_key,
                'Accept': 'application/json'
            }
            params = {
                'q': query,
                'count': max_results
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                results = data.get('web', {}).get('results', [])
                
                formatted = []
                for item in results:
                    formatted.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'content': item.get('description', ''),
                        'score': item.get('relevance_score', 0.8),
                        'engine': 'brave'
                    })
                
                logger.info(f"✅ Brave搜索完成，找到 {len(formatted)} 个结果")
                return formatted
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Brave HTTP错误: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logger.error(f" Brave搜索失败: {e}")
            return []


# 全局单例
brave_search = BraveSearchService()
