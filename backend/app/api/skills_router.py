"""
Skills API路由
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services.skills_service import skills_service
from app.utils.logger import get_logger

logger = get_logger("SkillsAPI")

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.post("/optimize-outline")
async def optimize_outline(data: Dict[str, Any]):
    """大纲优化助手
    
    Args:
        data: {
            "outline": [...],  # 大纲列表
            "query": "..."     # 研究问题
        }
    
    Returns:
        优化建议和评分
    """
    try:
        outline = data.get('outline', [])
        query = data.get('query', '')
        
        if not outline:
            raise HTTPException(status_code=400, detail="大纲不能为空")
        if not query:
            raise HTTPException(status_code=400, detail="研究问题不能为空")
        
        result = await skills_service.optimize_outline(outline, query)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', '优化失败'))
        
        return result['data']
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 大纲优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-citations")
async def validate_citations(data: Dict[str, Any]):
    """引用链接验证器
    
    Args:
        data: {
            "citations": [...]  # 引用列表
        }
    
    Returns:
        验证结果
    """
    try:
        citations = data.get('citations', [])
        
        if not citations:
            raise HTTPException(status_code=400, detail="引用列表不能为空")
        
        result = await skills_service.validate_citations(citations)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', '验证失败'))
        
        return result['data']
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 引用验证失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate-search-results")
async def evaluate_search_results(data: Dict[str, Any]):
    """搜索结果质量评估器
    
    Args:
        data: {
            "results": [...],  # 搜索结果列表
            "query": "..."     # 搜索查询
        }
    
    Returns:
        评估结果
    """
    try:
        results = data.get('results', [])
        query = data.get('query', '')
        
        if not results:
            raise HTTPException(status_code=400, detail="搜索结果不能为空")
        if not query:
            raise HTTPException(status_code=400, detail="搜索查询不能为空")
        
        result = await skills_service.evaluate_search_results(results, query)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', '评估失败'))
        
        return result['data']
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 搜索评估失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_skills():
    """列出所有可用的Skills
    
    Returns:
        Skills列表
    """
    skills = [
        {
            "id": "outline_optimizer",
            "name": "大纲优化Skill",
            "description": "分析研究大纲的完整性、逻辑性和深度，提供优化建议",
            "icon": "📋",
            "color": "#409EFF"
        },
        {
            "id": "citation_validator",
            "name": "引用链接验证Skill",
            "description": "验证引用链接的有效性和内容匹配度",
            "icon": "🔗",
            "color": "#67C23A"
        },
        {
            "id": "search_evaluator",
            "name": "搜索结果质量评估Skill",
            "description": "评估搜索结果的相关性、可信度和时效性",
            "icon": "📊",
            "color": "#E6A23C"
        }
    ]
    
    return {
        "success": True,
        "data": skills
    }
