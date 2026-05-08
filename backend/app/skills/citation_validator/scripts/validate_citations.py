"""
引用链接验证Skill - 执行脚本

验证引用链接的有效性和内容匹配度
"""
import json
from typing import Dict, Any, List


async def execute(citations: List[Dict]) -> Dict[str, Any]:
    """
    执行引用验证
    
    Args:
        citations: 引用列表，每个包含url, title, content
    
    Returns:
        验证结果
    """
    from app.services.llm_service import llm_service
    import aiohttp
    
    valid_count = 0
    invalid_count = 0
    citation_results = []
    
    for citation in citations:
        url = citation.get('url', '')
        title = citation.get('title', '')
        content = citation.get('content', '')
        
        # 检查URL有效性
        is_valid = True
        issues = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=5) as response:
                    if response.status >= 400:
                        is_valid = False
                        issues.append(f"HTTP {response.status}")
        except Exception as e:
            is_valid = False
            issues.append(f"无法访问: {str(e)}")
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
        
        # 使用LLM评估内容质量
        quality_score = 50  # 默认分数
        
        if content and len(content) > 100:
            prompt = f"""评估以下引用内容的质量（0-100分）：

标题：{title}
内容：{content[:500]}

评估标准：
- 相关性：是否与主题相关
- 权威性：来源是否可信
- 完整性：信息是否充分

只返回数字分数。
"""
            try:
                score_text = await llm_service.chat(prompt, temperature=0.3)
                quality_score = int(''.join(filter(str.isdigit, score_text)) or '50')
            except:
                pass
        
        citation_results.append({
            "url": url,
            "title": title,
            "is_valid": is_valid,
            "quality_score": quality_score,
            "issues": issues
        })
    
    # 计算整体评分
    total = len(citations)
    overall_score = int((valid_count / total * 100) if total > 0 else 0)
    
    # 生成建议
    recommendations = []
    if invalid_count > 0:
        recommendations.append(f"建议替换{invalid_count}个失效链接")
    
    low_quality = [c for c in citation_results if c['quality_score'] < 60]
    if low_quality:
        recommendations.append(f"建议优化{len(low_quality)}个低质量引用")
    
    return {
        "success": True,
        "data": {
            "total_count": total,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "overall_score": overall_score,
            "citations": citation_results,
            "recommendations": recommendations
        }
    }


if __name__ == "__main__":
    import asyncio
    
    test_citations = [
        {
            "url": "https://example.com/article",
            "title": "测试文章",
            "content": "这是一篇关于新能源汽车的文章..."
        }
    ]
    
    result = asyncio.run(execute(test_citations))
    print(json.dumps(result, ensure_ascii=False, indent=2))
