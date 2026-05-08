"""
MCP API路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.services.mcp_service import mcp_service, MCPRequest, MCPTool, MCPResponse
from app.utils.logger import get_logger

logger = get_logger("MCPAPI")

router = APIRouter(prefix="/api/mcp", tags=["MCP"])


@router.get("/tools", response_model=List[MCPTool])
async def list_tools():
    """列出所有可用的MCP工具"""
    tools = mcp_service.list_tools()
    logger.info(f" 查询MCP工具列表，共 {len(tools)} 个工具")
    return tools


@router.post("/call", response_model=MCPResponse)
async def call_tool(request: MCPRequest):
    """调用MCP工具
    
    Args:
        request: 工具调用请求
        
    Returns:
        工具调用响应
    """
    logger.info(f" 收到MCP工具调用请求: {request.tool_name}")
    
    response = await mcp_service.call_tool(request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error)
    
    return response


@router.get("/schema/{tool_name}")
async def get_tool_schema(tool_name: str):
    """获取指定工具的schema
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具schema
    """
    schema = mcp_service.get_tool_schema(tool_name)
    
    if schema is None:
        raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")
    
    return schema
