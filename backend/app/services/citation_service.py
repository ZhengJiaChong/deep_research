"""
引用链接服务 - DeepSeek风格
负责引用数据管理和Markdown标记生成
"""
import re
from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger("CitationService")


class CitationService:
    """引用链接服务"""
    
    def __init__(self):
        self.citations = {}  # {citation_id: citation_data}
        self.next_id = 1
    
    def reset(self):
        """重置引用数据（每次研究开始时调用）"""
        self.citations = {}
        self.next_id = 1
        logger.info("🔄 引用数据已重置")
    
    def add_citation(self, title: str, url: str, content: str = "", source: str = "") -> int:
        """
        添加引用并返回ID
        
        Args:
            title: 标题
            url: URL链接
            content: 内容摘要
            source: 来源网站
        
        Returns:
            引用ID
        """
        citation_id = self.next_id
        self.citations[citation_id] = {
            'id': citation_id,
            'title': title,
            'url': url,
            'content': content[:300] if content else "",
            'source': source or self._extract_domain(url)
        }
        self.next_id += 1
        logger.debug(f"✅ 添加引用[{citation_id}]: {title[:50]}")
        return citation_id
    
    def add_search_result_as_citation(self, result: Dict[str, Any]) -> int:
        """
        将搜索结果转换为引用
        
        Args:
            result: 搜索结果字典
        
        Returns:
            引用ID
        """
        return self.add_citation(
            title=result.get('title', ''),
            url=result.get('url', ''),
            content=result.get('content', ''),
            source=result.get('engine', '')
        )
    
    def generate_markdown_with_citations(self, text: str, citations: List[Dict]) -> str:
        """
        在文本中插入引用标记 [1], [2]
        
        Args:
            text: 原始文本
            citations: 引用映射列表 [{'keyword': '关键词', 'citation_id': 1}, ...]
        
        Returns:
            带引用标记的Markdown文本
        """
        result = text
        
        # 按关键词长度降序排序（避免短词覆盖长词）
        sorted_citations = sorted(citations, key=lambda x: len(x['keyword']), reverse=True)
        
        for citation in sorted_citations:
            keyword = citation['keyword']
            citation_id = citation['citation_id']
            
            # 直接替换关键词，使用标准Markdown引用格式 [1]
            if keyword in result:
                result = result.replace(keyword, f'{keyword}[{citation_id}]', 1)
        
        logger.debug(f"📝 生成引用标记，共 {len(sorted_citations)} 个")
        return result
    
    def get_all_citations(self) -> Dict[int, Dict]:
        """获取所有引用数据"""
        return self.citations.copy()
    
    def get_citation_by_id(self, citation_id: int) -> Dict:
        """根据ID获取单个引用"""
        return self.citations.get(citation_id, {})
    
    def _extract_domain(self, url: str) -> str:
        """从URL提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return ''
    
    def to_dict(self) -> Dict:
        """转换为字典格式（用于API返回）"""
        return {
            'citations': self.citations,
            'total': len(self.citations)
        }


# 全局单例
citation_service = CitationService()
