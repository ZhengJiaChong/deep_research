"""
MCP (Model Context Protocol) 服务封装
提供标准化工具调用接口，支持AI模型与外部服务交互
"""
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.utils.logger import get_logger

logger = get_logger("MCPService")


class MCPTool(BaseModel):
    """MCP工具定义"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="输入参数schema")
    

class MCPRequest(BaseModel):
    """MCP请求模型"""
    tool_name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    

class MCPResponse(BaseModel):
    """MCP响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Any = Field(default=None, description="返回数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class MCPService:
    """MCP服务类 - 管理工具注册和调用"""
    
    def __init__(self):
        """初始化MCP服务"""
        self.tools: Dict[str, MCPTool] = {}
        self.handlers: Dict[str, callable] = {}
        logger.info("✅ MCP服务已初始化")
    
    def register_tool(self, tool: MCPTool, handler: callable):
        """注册工具
        
        Args:
            tool: 工具定义
            handler: 工具处理函数
        """
        self.tools[tool.name] = tool
        self.handlers[tool.name] = handler
        logger.info(f"🔧 注册MCP工具: {tool.name}")
    
    def list_tools(self) -> List[MCPTool]:
        """列出所有已注册的工具
        
        Returns:
            工具列表
        """
        return list(self.tools.values())
    
    async def call_tool(self, request: MCPRequest) -> MCPResponse:
        """调用工具
        
        Args:
            request: 工具调用请求
        
        Returns:
            工具调用响应
        """
        tool_name = request.tool_name
        
        # 检查工具是否存在
        if tool_name not in self.handlers:
            return MCPResponse(
                success=False,
                error=f"工具不存在: {tool_name}"
            )
        
        try:
            logger.info(f" 调用MCP工具: {tool_name}")
            logger.debug(f"参数: {request.arguments}")
            
            # 调用处理函数
            handler = self.handlers[tool_name]
            result = await handler(**request.arguments)
            
            logger.info(f"✅ 工具调用成功: {tool_name}")
            
            return MCPResponse(
                success=True,
                data=result,
                metadata={"tool_name": tool_name}
            )
            
        except Exception as e:
            logger.error(f"❌ 工具调用失败 {tool_name}: {e}")
            return MCPResponse(
                success=False,
                error=str(e)
            )
    
    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具schema
        
        Args:
            tool_name: 工具名称
        
        Returns:
            工具schema字典
        """
        if tool_name not in self.tools:
            return None
        
        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema
        }


# 全局单例
mcp_service = MCPService()
