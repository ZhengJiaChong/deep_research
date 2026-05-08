"""
Skills服务 - 提供大纲优化、引用验证、搜索评估等功能
"""
from typing import Dict, Any, List
from app.services.llm_service import llm_service
from app.services.search_service import search_service
from app.utils.logger import get_logger
import json
import re

logger = get_logger("SkillsService")


class SkillsService:
    """Skills服务类"""
    
    def __init__(self):
        """初始化Skills服务"""
        logger.info("✅ Skills服务已初始化")
    
    async def optimize_outline(self, outline: List[Dict], query: str) -> Dict[str, Any]:
        """大纲优化助手
        
        分析研究大纲的完整性、逻辑性和深度，提供优化建议
        
        Args:
            outline: 当前大纲列表
            query: 研究问题
        
        Returns:
            优化建议和评分
        """
        logger.info(f"📋 开始优化大纲，共 {len(outline)} 个方向")
        
        # 构建大纲文本
        outline_text = "\n".join([
            f"{i+1}. {item.get('title', '')}: {item.get('description', '')}"
            for i, item in enumerate(outline)
        ])
        
        prompt = f"""你是一个专业的研究大纲优化专家。请分析以下研究大纲并提供优化建议。

研究问题：{query}

当前大纲：
{outline_text}

请从以下维度评估（返回JSON格式）：
1. completeness（完整性 0-100）：是否覆盖了研究问题的所有重要方面
2. logic（逻辑性 0-100）：大纲结构是否合理，是否有逻辑递进关系
3. depth（深度 0-100）：研究方向是否足够深入
4. suggestions（建议）：具体的优化建议（数组，至少3条）
5. missing_topics（缺失主题）：建议补充的研究方向（数组）
6. redundant_topics（冗余主题）：建议合并或删除的主题（数组）
7. overall_score（综合评分 0-100）

仅返回JSON，不要其他内容。"""

        try:
            response = await llm_service.client.ainvoke([
                {"role": "system", "content": prompt}
            ])
            
            # 解析JSON
            result_text = response.content
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(result_text)
            
            logger.info(f"✅ 大纲优化完成，综合评分: {result.get('overall_score', 0)}")
            
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"❌ 大纲优化失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_citations(self, citations: List[Dict]) -> Dict[str, Any]:
        """引用链接验证器
        
        验证引用链接的有效性和内容匹配度
        
        Args:
            citations: 引用列表，每项包含url、title、content
        
        Returns:
            验证结果
        """
        logger.info(f"🔗 开始验证 {len(citations)} 个引用链接")
        
        results = []
        valid_count = 0
        invalid_count = 0
        
        for i, citation in enumerate(citations):
            try:
                url = citation.get('url', '')
                title = citation.get('title', '')
                content = citation.get('content', '')
                
                # 基础验证
                is_valid_url = url.startswith('http')
                has_title = len(title) > 0
                has_content = len(content) > 20
                
                # 内容质量评分
                content_score = 0
                if has_content:
                    # 内容长度评分
                    content_score += min(len(content) / 10, 40)
                    # 关键词密度评分（简单实现）
                    keywords = ['数据', '研究', '分析', '报告', '结果']
                    keyword_count = sum(1 for kw in keywords if kw in content)
                    content_score += keyword_count * 10
                
                is_valid = is_valid_url and has_title and content_score > 30
                
                if is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1
                
                results.append({
                    "index": i + 1,
                    "url": url,
                    "title": title,
                    "is_valid": is_valid,
                    "issues": [] if is_valid else [
                        issue for issue, condition in [
                            ("URL格式无效", not is_valid_url),
                            ("标题为空", not has_title),
                            ("内容质量低", content_score <= 30)
                        ] if condition
                    ],
                    "quality_score": min(content_score, 100)
                })
                
            except Exception as e:
                logger.error(f"❌ 验证引用 {i+1} 失败: {e}")
                invalid_count += 1
                results.append({
                    "index": i + 1,
                    "is_valid": False,
                    "issues": [f"验证失败: {str(e)}"],
                    "quality_score": 0
                })
        
        overall_score = (valid_count / len(citations) * 100) if citations else 0
        
        logger.info(f"✅ 引用验证完成: 有效 {valid_count}, 无效 {invalid_count}")
        
        return {
            "success": True,
            "data": {
                "total": len(citations),
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "overall_score": overall_score,
                "details": results
            }
        }
    
    async def evaluate_search_results(self, results: List[Dict], query: str) -> Dict[str, Any]:
        """搜索结果质量评估器
        
        评估搜索结果的相关性、可信度和时效性
        
        Args:
            results: 搜索结果列表
            query: 原始搜索查询
        
        Returns:
            评估结果和过滤建议
        """
        logger.info(f"📊 开始评估 {len(results)} 个搜索结果")
        
        evaluated_results = []
        high_quality = []
        medium_quality = []
        low_quality = []
        
        for i, result in enumerate(results):
            try:
                title = result.get('title', '')
                content = result.get('content', '')
                url = result.get('url', '')
                score = result.get('score', 0)
                
                # 1. 相关性评分（0-100）
                relevance_score = self._calculate_relevance(query, title, content)
                
                # 2. 可信度评分（0-100）
                credibility_score = self._calculate_credibility(url, content)
                
                # 3. 时效性评分（0-100）
                timeliness_score = self._calculate_timeliness(content)
                
                # 综合评分
                overall_score = (
                    relevance_score * 0.5 +
                    credibility_score * 0.3 +
                    timeliness_score * 0.2
                )
                
                evaluated_result = {
                    "index": i + 1,
                    "title": title,
                    "url": url,
                    "relevance_score": relevance_score,
                    "credibility_score": credibility_score,
                    "timeliness_score": timeliness_score,
                    "overall_score": overall_score,
                    "quality_level": "high" if overall_score >= 70 else ("medium" if overall_score >= 40 else "low")
                }
                
                evaluated_results.append(evaluated_result)
                
                if overall_score >= 70:
                    high_quality.append(evaluated_result)
                elif overall_score >= 40:
                    medium_quality.append(evaluated_result)
                else:
                    low_quality.append(evaluated_result)
                
            except Exception as e:
                logger.error(f"❌ 评估结果 {i+1} 失败: {e}")
        
        # 统计信息
        total = len(results)
        avg_score = sum(r['overall_score'] for r in evaluated_results) / total if total > 0 else 0
        
        logger.info(f"✅ 搜索评估完成: 高质量 {len(high_quality)}, 中等 {len(medium_quality)}, 低质量 {len(low_quality)}")
        
        return {
            "success": True,
            "data": {
                "total": total,
                "average_score": avg_score,
                "high_quality_count": len(high_quality),
                "medium_quality_count": len(medium_quality),
                "low_quality_count": len(low_quality),
                "high_quality": high_quality,
                "medium_quality": medium_quality,
                "low_quality": low_quality,
                "recommendations": {
                    "keep": [r['index'] for r in high_quality],
                    "review": [r['index'] for r in medium_quality],
                    "discard": [r['index'] for r in low_quality]
                }
            }
        }
    
    def _calculate_relevance(self, query: str, title: str, content: str) -> float:
        """计算相关性评分"""
        query_keywords = set(query.split())
        title_keywords = set(title.split())
        content_keywords = set(content.split()[:50])  # 只看前50个词
        
        # 标题匹配度
        title_match = len(query_keywords & title_keywords) / len(query_keywords) if query_keywords else 0
        
        # 内容匹配度
        content_match = len(query_keywords & content_keywords) / len(query_keywords) if query_keywords else 0
        
        # 综合相关性
        relevance = (title_match * 0.6 + content_match * 0.4) * 100
        return min(relevance, 100)
    
    def _calculate_credibility(self, url: str, content: str) -> float:
        """计算可信度评分"""
        score = 50  # 基础分
        
        # 域名可信度
        credible_domains = ['.edu', '.gov', '.org', 'wikipedia', 'academia', 'researchgate']
        if any(domain in url.lower() for domain in credible_domains):
            score += 30
        
        # 内容长度（越长越可信）
        if len(content) > 200:
            score += 10
        elif len(content) > 100:
            score += 5
        
        # 包含数据来源
        if any(word in content.lower() for word in ['数据', '研究', '报告', '统计']):
            score += 10
        
        return min(score, 100)
    
    def _calculate_timeliness(self, content: str) -> float:
        """计算时效性评分"""
        import re
        from datetime import datetime
        
        score = 50  # 基础分
        
        # 查找年份
        year_pattern = r'\b(202[0-9])\b'
        years = re.findall(year_pattern, content)
        
        if years:
            latest_year = max(int(y) for y in years)
            current_year = datetime.now().year
            
            # 年份越近分数越高
            year_diff = current_year - latest_year
            if year_diff == 0:
                score += 40
            elif year_diff == 1:
                score += 30
            elif year_diff <= 3:
                score += 20
            else:
                score += 10
        
        # 包含"最新"、"近期"等词
        if any(word in content for word in ['最新', '近期', '最近', '今年']):
            score += 10
        
        return min(score, 100)


# 全局单例
skills_service = SkillsService()
