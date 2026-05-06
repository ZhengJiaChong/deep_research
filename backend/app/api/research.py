"""
研究API路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.api.models import (
    StartResearchRequest,
    StartResearchResponse,
    OutlineResponse,
    ResearchStatusResponse,
    ReportResponse
)
from app.services.research_service import research_service
from app.services.llm_service import llm_service
from app.config import settings
from app.utils.logger import get_logger
import json
import asyncio

logger = get_logger("ResearchAPI")

router = APIRouter(prefix="/research", tags=["research"])

@router.post("/start", response_model=StartResearchResponse)
async def start_research(request: StartResearchRequest):
    """开始研究
    
    Args:
        request: 研究请求
    
    Returns:
        研究ID和状态
    """
    try:
        logger.info(f"📥 收到研究请求: {request.query[:50]}...")
        
        # 开始研究
        research_id = await research_service.start_research(request.query)
        
        return StartResearchResponse(
            research_id=research_id,
            status="starting",
            message="研究已开始，正在分析问题..."
        )
    except Exception as e:
        logger.error(f"❌ 启动研究失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{research_id}/outline", response_model=OutlineResponse)
async def get_outline(research_id: str):
    """获取研究大纲
    
    Args:
        research_id: 研究ID
    
    Returns:
        研究大纲
    """
    try:
        outline_data = await research_service.get_outline(research_id)
        
        if 'error' in outline_data:
            raise HTTPException(status_code=404, detail=outline_data['error'])
        
        return OutlineResponse(**outline_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取大纲失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{research_id}/progress", response_model=ResearchStatusResponse)
async def get_progress(research_id: str):
    """获取研究进度
    
    Args:
        research_id: 研究ID
    
    Returns:
        研究进度信息
    """
    try:
        progress_data = await research_service.get_research_progress(research_id)
        
        if 'error' in progress_data:
            raise HTTPException(status_code=404, detail=progress_data['error'])
        
        # 添加进度日志
        research = await research_service.get_research(research_id)
        if research:
            progress_data['progress_logs'] = research.get('progress_logs', [])
        
        return ResearchStatusResponse(**progress_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取进度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{research_id}/report", response_model=ReportResponse)
async def get_report(research_id: str):
    """获取最终报告
    
    Args:
        research_id: 研究ID
    
    Returns:
        研究报告
    """
    try:
        report_data = await research_service.get_report(research_id)
        
        if 'error' in report_data:
            if report_data['error'] == '研究不存在':
                raise HTTPException(status_code=404, detail=report_data['error'])
            else:
                raise HTTPException(status_code=400, detail=report_data['error'])
        
        return ReportResponse(**report_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{research_id}/stream")
async def stream_report(research_id: str):
    """流式获取研究报告（SSE）
    
    Args:
        research_id: 研究ID
    
    Returns:
        SSE流式输出
    """
    async def generate():
        try:
            # 获取研究数据
            research = await research_service.get_research(research_id)
            if not research:
                yield f"data: {json.dumps({'error': '研究不存在'}, ensure_ascii=False)}\n\n"
                return
            
            if research.get('status') != 'completed':
                yield f"data: {json.dumps({'error': '研究尚未完成'}, ensure_ascii=False)}\n\n"
                return
            
            # 检查是否启用流式输出
            if not settings.STREAM_OUTPUT:
                # 如果未启用流式，直接返回完整报告
                report = research.get('report', '')
                yield f"data: {json.dumps({'content': report, 'done': True}, ensure_ascii=False)}\n\n"
                return
            
            # 方案B：直接使用工作流已生成的报告（分块发送）
            report = research.get('report', '')
                        
            if not report:
                # 如果没有预生成的报告，才调用流式生成
                query = research.get('query', '')
                outline = research.get('outline', [])
                analyses = [task.get('analysis', '') for task in research.get('tasks', []) if task.get('analysis')]
                            
                async for chunk in llm_service.generate_report_stream(query, outline, analyses):
                    yield f"data: {json.dumps({'content': chunk, 'done': False}, ensure_ascii=False)}\n\n"
            else:
                # 将完整报告分块发送（模拟流式效果）
                chunk_size = 100  # 每块100字
                for i in range(0, len(report), chunk_size):
                    chunk = report[i:i+chunk_size]
                    yield f"data: {json.dumps({'content': chunk, 'done': False}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.02)  # 更快的速度
            
            # 结束标记
            yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"❌ 流式输出失败: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用nginx缓冲
        }
    )
