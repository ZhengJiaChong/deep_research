"""
大纲优化Skill - 执行脚本

分析研究大纲的完整性、逻辑性和深度，提供优化建议
"""
import sys
import json
from typing import Dict, Any, List


async def execute(outline: List[Dict], query: str) -> Dict[str, Any]:
    """
    执行大纲优化
    
    Args:
        outline: 大纲列表
        query: 研究问题
    
    Returns:
        优化结果
    """
    from app.services.llm_service import llm_service
    
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
3. depth（深度 0-100）：各主题的描述是否足够详细
4. relevance（相关性 0-100）：大纲内容是否紧密围绕研究问题

同时提供：
- overall_score: 综合评分（四个维度的平均值）
- suggestions: 优化建议列表（至少3条）
- missing_topics: 缺失的重要主题列表

只返回JSON，不要其他文字。
"""
    
    try:
        response = await llm_service.chat(prompt, temperature=0.7)
        
        # 解析JSON响应
        result = json.loads(response)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # 测试代码
    import asyncio
    
    test_outline = [
        {"id": "task_1", "title": "技术背景", "description": "分析技术发展历史"},
        {"id": "task_2", "title": "市场现状", "description": "当前市场规模和格局"}
    ]
    
    result = asyncio.run(execute(test_outline, "新能源汽车发展趋势"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
