"""
搜索结果质量评估Skill - 执行脚本

评估搜索结果的相关性、可信度和时效性
"""
import json
from typing import Dict, Any, List


def calculate_relevance(query: str, title: str, content: str) -> float:
    """计算相关性评分"""
    query_words = set(query.lower().split())
    title_words = set(title.lower().split())
    content_words = set(content.lower().split()[:100])
    
    # 标题匹配度（权重70%）
    title_match = len(query_words & title_words) / max(len(query_words), 1)
    
    # 内容匹配度（权重30%）
    content_match = len(query_words & content_words) / max(len(query_words), 1)
    
    return min(100, (title_match * 0.7 + content_match * 0.3) * 100)


def calculate_credibility(url: str, content: str) -> float:
    """计算可信度评分"""
    score = 50  # 基础分
    
    # 域名权威性
    authoritative_domains = ['.gov', '.edu', '.org', 'wikipedia', 'nature.com', 'science.org']
    for domain in authoritative_domains:
        if domain in url.lower():
            score += 20
            break
    
    # 内容长度
    if len(content) > 500:
        score += 15
    elif len(content) > 200:
        score += 10
    
    return min(100, score)


def calculate_timeliness(content: str) -> float:
    """计算时效性评分"""
    import re
    
    # 查找年份
    years = re.findall(r'\b(20\d{2})\b', content)
    
    if not years:
        return 50  # 无年份信息，给中等分
    
    latest_year = max(int(y) for y in years)
    current_year = 2026
    
    # 计算年份差
    year_diff = current_year - latest_year
    
    if year_diff == 0:
        return 100
    elif year_diff <= 1:
        return 90
    elif year_diff <= 2:
        return 80
    elif year_diff <= 3:
        return 70
    else:
        return max(30, 70 - year_diff * 10)


async def execute(results: List[Dict], query: str) -> Dict[str, Any]:
    """
    执行搜索结果评估
    
    Args:
        results: 搜索结果列表
        query: 搜索查询
    
    Returns:
        评估结果
    """
    evaluated_results = []
    high_quality = 0
    medium_quality = 0
    low_quality = 0
    
    for result in results:
        url = result.get('url', '')
        title = result.get('title', '')
        content = result.get('content', '')
        
        # 计算三个维度
        relevance = calculate_relevance(query, title, content)
        credibility = calculate_credibility(url, content)
        timeliness = calculate_timeliness(content)
        
        # 综合评分：相关性50% + 可信度30% + 时效性20%
        score = int(relevance * 0.5 + credibility * 0.3 + timeliness * 0.2)
        
        # 确定推荐级别
        if score >= 70:
            recommendation = "keep"
            high_quality += 1
        elif score >= 40:
            recommendation = "review"
            medium_quality += 1
        else:
            recommendation = "discard"
            low_quality += 1
        
        evaluated_results.append({
            "url": url,
            "title": title,
            "score": score,
            "dimensions": {
                "relevance": int(relevance),
                "credibility": int(credibility),
                "timeliness": int(timeliness)
            },
            "recommendation": recommendation
        })
    
    # 计算平均分
    total = len(results)
    average_score = int(sum(r['score'] for r in evaluated_results) / total) if total > 0 else 0
    
    # 生成建议
    recommendations = []
    if high_quality > 0:
        recommendations.append(f"建议优先使用前{high_quality}个高质量结果")
    if low_quality > total * 0.3:
        recommendations.append("低质量结果较多，建议重新搜索以获取更多优质信息")
    if average_score < 60:
        recommendations.append("整体质量偏低，建议优化搜索关键词")
    
    return {
        "success": True,
        "data": {
            "total_results": total,
            "average_score": average_score,
            "high_quality_count": high_quality,
            "medium_quality_count": medium_quality,
            "low_quality_count": low_quality,
            "results": evaluated_results,
            "recommendations": recommendations
        }
    }


if __name__ == "__main__":
    import asyncio
    
    test_results = [
        {
            "url": "https://example.com/article",
            "title": "新能源汽车市场分析",
            "content": "2025年新能源汽车市场持续增长..."
        }
    ]
    
    result = asyncio.run(execute(test_results, "新能源汽车市场"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
