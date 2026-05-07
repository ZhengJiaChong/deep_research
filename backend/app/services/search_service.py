"""
搜索服务 - 封装Tavily Search API
"""
from tavily import TavilyClient
from typing import List, Dict, Any
from app.config import settings
from app.utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger("SearchService")

class SearchService:
    """搜索服务类"""
    
    def __init__(self):
        """初始化Tavily客户端"""
        # 显式传递API Key，避免Tavily SDK读取其他环境变量
        api_key = settings.TAVILY_API_KEY
        if not api_key:
            raise ValueError("TAVILY_API_KEY未配置")
        self.client = TavilyClient(api_key=api_key)
        logger.info(f"✅ Tavily搜索服务已初始化 (Key: {api_key[:15]}...)")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """执行搜索
        
        Args:
            query: 搜索查询词
            max_results: 最大结果数量
        
        Returns:
            搜索结果列表
        """
        if max_results is None:
            max_results = settings.TAVILY_MAX_RESULTS
        
        logger.info(f"🔍 搜索: {query[:50]}...")
        
        try:
            # 调用Tavily API
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",  # 深度搜索
                include_answer=False,
                include_raw_content=False
            )
            
            # 解析结果
            results = []
            for item in response.get('results', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'content': item.get('content', ''),
                    'score': item.get('score', 0.0)
                })
            
            logger.info(f"✅ 搜索完成，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def batch_search(self, queries: List[str], max_results: int = None) -> Dict[str, List[Dict]]:
        """批量搜索
        
        Args:
            queries: 查询词列表
            max_results: 每个查询的最大结果数
        
        Returns:
            {query: [results]}
        """
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

def deduplicate_results(results: List[Dict], threshold: float = 0.85) -> List[Dict]:
    """基于URL和内容去重
    
    Args:
        results: 搜索结果列表
        threshold: 相似度阈值
    
    Returns:
        去重后的结果列表
    """
    seen_urls = set()
    unique_results = []
    
    for result in results:
        url = result.get('url', '')
        
        # 基于URL去重
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(result)
    
    logger.info(f" 结果去重: {len(results)} -> {len(unique_results)}")
    return unique_results

# 全局单例
search_service = SearchService()
