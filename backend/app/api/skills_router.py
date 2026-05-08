"""
Skills API路由
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.skills import skills_loader
from app.utils.logger import get_logger

logger = get_logger("SkillsAPI")

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.post("/optimize-outline")
async def optimize_outline(data: Dict[str, Any]):
    """大纲优化助手"""
    try:
        outline = data.get('outline', [])
        query = data.get('query', '')
        
        if not outline:
            raise HTTPException(status_code=400, detail="大纲不能为空")
        if not query:
            raise HTTPException(status_code=400, detail="研究问题不能为空")
        
        result = await skills_loader.execute_skill(
            'outline_optimizer',
            outline=outline,
            query=query
        )
        
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
    """引用链接验证器"""
    try:
        citations = data.get('citations', [])
        
        if not citations:
            raise HTTPException(status_code=400, detail="引用列表不能为空")
        
        result = await skills_loader.execute_skill(
            'citation_validator',
            citations=citations
        )
        
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
    """搜索结果质量评估器"""
    try:
        results = data.get('results', [])
        query = data.get('query', '')
        
        if not results:
            raise HTTPException(status_code=400, detail="搜索结果不能为空")
        if not query:
            raise HTTPException(status_code=400, detail="搜索查询不能为空")
        
        result = await skills_loader.execute_skill(
            'search_evaluator',
            results=results,
            query=query
        )
        
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
    """列出所有可用的Skills"""
    skills = skills_loader.list_skills()
    
    return {
        "success": True,
        "data": skills
    }
