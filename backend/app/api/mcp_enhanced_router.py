"""
MCP增强API路由 - 提供高级MCP调用方式
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
from app.services.mcp_service import MCPRequest, MCPResponse
from app.services.mcp_enhanced import mcp_enhanced
from app.utils.logger import get_logger
import json

logger = get_logger("MCPEnhancedAPI")

router = APIRouter(prefix="/api/mcp/enhanced", tags=["MCP-Enhanced"])


@router.post("/stream")
async def call_tool_stream(request: MCPRequest):
    """流式调用MCP工具
    
    实时返回工具执行进度，无需等待完成
    
    Args:
        request: 工具调用请求
        
    Returns:
        SSE流式响应
    """
    async def event_generator():
        async for chunk in mcp_enhanced.call_tool_stream(request):
            yield chunk
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.post("/batch", response_model=List[MCPResponse])
async def batch_call_tools(requests: List[MCPRequest]):
    """批量并行调用MCP工具
    
    同时调用多个工具，提升效率
    
    Args:
        requests: 工具调用请求列表
        
    Returns:
        工具调用响应列表
    """
    if not requests:
        raise HTTPException(status_code=400, detail="请求列表不能为空")
    
    responses = await mcp_enhanced.batch_call_tools(requests)
    return responses


@router.post("/chain", response_model=List[MCPResponse])
async def tool_chain(chain_requests: List[Dict[str, Any]]):
    """工具链调用
    
    顺序执行工具，前一个工具的结果作为下一个工具的输入
    支持参数引用：{{step_0.field}}
    
    Args:
        chain_requests: 工具链请求列表
        示例：
        [
            {"tool_name": "search", "arguments": {"query": "AI"}},
            {"tool_name": "llm_chat", "arguments": {"message": "总结：{{step_0.results}}"}}
        ]
        
    Returns:
        工具调用响应列表
    """
    if not chain_requests:
        raise HTTPException(status_code=400, detail="工具链不能为空")
    
    responses = await mcp_enhanced.tool_chain(chain_requests)
    return responses


@router.post("/quick-search")
async def quick_search(query: str, max_results: int = 5):
    """快速搜索 - 封装的便捷接口
    
    直接调用搜索工具，无需完整MCP请求格式
    
    Args:
        query: 搜索查询
        max_results: 最大结果数
        
    Returns:
        搜索结果
    """
    request = MCPRequest(
        tool_name="search",
        arguments={"query": query, "max_results": max_results}
    )
    
    response = await mcp_enhanced.batch_call_tools([request])
    
    if not response[0].success:
        raise HTTPException(status_code=400, detail=response[0].error)
    
    return response[0].data


@router.post("/quick-chat")
async def quick_chat(message: str, system_prompt: str = None):
    """快速对话 - 封装的便捷接口
    
    直接调用LLM工具，无需完整MCP请求格式
    
    Args:
        message: 用户消息
        system_prompt: 可选的系统提示词
        
    Returns:
        LLM响应
    """
    arguments = {"message": message}
    if system_prompt:
        arguments["system_prompt"] = system_prompt
    
    request = MCPRequest(
        tool_name="llm_chat",
        arguments=arguments
    )
    
    response = await mcp_enhanced.batch_call_tools([request])
    
    if not response[0].success:
        raise HTTPException(status_code=400, detail=response[0].error)
    
    return response[0].data
