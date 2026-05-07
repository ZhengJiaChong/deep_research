"""
多引擎搜索服务 - 支持Tavily、DuckDuckGo、Brave等
自动降级策略：Tavily限额时切换其他引擎
"""
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("MultiSearchService")

class DuckDuckGoSearcher:
    """DuckDuckGo搜索引擎（免费，无需API Key）"""
    
    def __init__(self):
        try:
            # 尝试新包名 ddgs
            try:
                from ddgs import DDGS
                self.ddgs = DDGS()
                logger.info("✅ DuckDuckGo搜索引擎已初始化 (ddgs)")
            except ImportError:
                # 兼容旧包名 duckduckgo_search
                from duckduckgo_search import DDGS
                self.ddgs = DDGS()
                logger.info("✅ DuckDuckGo搜索引擎已初始化 (duckduckgo_search)")
            
            self.available = True
        except ImportError as e:
            self.available = False
            logger.warning(f"⚠️ DuckDuckGo不可用: {e}")
            logger.warning("请安装: pip install ddgs 或 pip install duckduckgo-search")
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """执行DuckDuckGo搜索"""
        if not self.available:
            return []
        
        try:
            logger.info(f"🦆 DuckDuckGo搜索: {query[:50]}...")
            
            # 使用同步方法，在事件循环中执行
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                lambda: list(self.ddgs.text(query, max_results=max_results))
            )
            
            formatted = []
            for item in results:
                formatted.append({
                    'title': item.get('title', ''),
                    'url': item.get('href', ''),
                    'content': item.get('body', ''),
                    'score': 0.8,  # DuckDuckGo无评分
                    'engine': 'duckduckgo'
                })
            
            logger.info(f"✅ DuckDuckGo搜索完成，找到 {len(formatted)} 个结果")
            return formatted
            
        except Exception as e:
            logger.error(f"❌ DuckDuckGo搜索失败: {e}")
            return []


class BraveSearcher:
    """Brave搜索引擎（每月2000次免费）"""
    
    def __init__(self):
        self.api_key = settings.BRAVE_API_KEY
        self.available = bool(self.api_key)
        if self.available:
            logger.info("✅ Brave搜索引擎已初始化")
        else:
            logger.warning("⚠️ Brave搜索引擎未配置API Key")
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """执行Brave搜索"""
        if not self.available:
            return []
        
        try:
            import httpx
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
                
        except Exception as e:
            logger.error(f"❌ Brave搜索失败: {e}")
            return []


class MultiSearchService:
    """多引擎搜索服务（自动降级）"""
    
    def __init__(self):
        # 按优先级初始化搜索引擎
        self.engines = []
        
        # 1. Tavily（唯一搜索引擎）
        try:
            from app.services.search_service import SearchService
            self.tavily = SearchService()
            self.engines.append(('tavily', self.tavily))
            logger.info("✅ 搜索引擎: Tavily")
        except Exception as e:
            logger.warning(f"⚠️ Tavily不可用: {e}")
        
        if not self.engines:
            logger.error("❌ 没有可用的搜索引擎！")
        
        logger.info(f"✅ 多引擎搜索服务已初始化，共 {len(self.engines)} 个引擎")
        
        # 添加重试机制
        self.max_retries = 2
    
    async def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """执行搜索（自动降级+重试）"""
        if max_results is None:
            max_results = settings.TAVILY_MAX_RESULTS
        
        logger.info(f" 多引擎搜索: {query[:50]}...")
        
        # 尝试每个引擎，支持重试
        for attempt in range(self.max_retries + 1):
            for engine_name, engine in self.engines:
                try:
                    if attempt > 0:
                        logger.info(f" 重试 {attempt}/{self.max_retries} - 使用: {engine_name}")
                    else:
                        logger.info(f"📌 尝试使用: {engine_name}")
                    
                    results = await engine.search(query, max_results)
                    
                    if results:
                        logger.info(f"✅ 使用 {engine_name} 搜索成功，找到 {len(results)} 个结果")
                        return results
                    
                    logger.warning(f"⚠️ {engine_name} 无结果")
                    
                except Exception as e:
                    logger.error(f"❌ {engine_name} 搜索失败: {e}")
                    continue
            
            if attempt < self.max_retries:
                logger.info(f"⏳ 等待 {attempt + 1} 秒后重试...")
                await asyncio.sleep(attempt + 1)
        
        logger.error(f"❌ 所有搜索引擎都失败了")
        return []
    
    async def batch_search(self, queries: List[str], max_results: int = None) -> Dict[str, List[Dict]]:
        """批量搜索"""
        logger.info(f"📦 开始批量搜索，共 {len(queries)} 个查询")
        
        results_dict = {}
        for query in queries:
            try:
                results = await self.search(query, max_results)
                results_dict[query] = results
            except Exception as e:
                logger.error(f"❌ 查询 '{query}' 搜索失败: {e}")
                results_dict[query] = []
        
        logger.info(f"✅ 批量搜索完成")
        return results_dict


# 全局单例
multi_search_service = MultiSearchService()
