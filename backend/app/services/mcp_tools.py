"""
MCP工具注册 - 将现有服务注册为MCP工具
"""
from app.services.mcp_service import mcp_service, MCPTool
from app.services.search_service import search_service
from app.services.llm_service import llm_service
from app.utils.logger import get_logger

logger = get_logger("MCPTools")


async def search_tool_handler(query: str, max_results: int = 5) -> dict:
    """搜索工具处理器
    
    Args:
        query: 搜索查询
        max_results: 最大结果数
    
    Returns:
        搜索结果字典
    """
    results = await search_service.search(query, max_results)
    return {
        "query": query,
        "count": len(results),
        "results": results
    }


async def llm_chat_tool_handler(message: str, system_prompt: str = None) -> dict:
    """LLM对话工具处理器
    
    Args:
        message: 用户消息
        system_prompt: 系统提示词
    
    Returns:
        LLM响应字典
    """
    # 使用generate_report_stream实现对话
    outline = [{"section": "回答", "content": message}]
    citations = {}
    
    response = ""
    async for chunk in llm_service.generate_report_stream(
        query=message,
        outline=outline,
        analyses=[],
        citations=citations
    ):
        response += chunk
    
    return {
        "message": message,
        "response": response
    }


def register_mcp_tools():
    """注册所有MCP工具"""
    logger.info(" 开始注册MCP工具...")
    
    # 注册搜索工具
    search_tool = MCPTool(
        name="search",
        description="执行网络搜索，返回相关网页信息",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询词"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大返回结果数",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    )
    mcp_service.register_tool(search_tool, search_tool_handler)
    
    # 注册LLM对话工具
    llm_tool = MCPTool(
        name="llm_chat",
        description="与AI模型对话，获取智能回复",
        input_schema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "用户消息"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "可选的系统提示词"
                }
            },
            "required": ["message"]
        }
    )
    mcp_service.register_tool(llm_tool, llm_chat_tool_handler)
    
    logger.info(f"✅ MCP工具注册完成，共注册 {len(mcp_service.tools)} 个工具")


# 自动注册
register_mcp_tools()
