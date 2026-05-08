"""
MCP增强服务 - 提供实时工具调用和流式输出
支持研究过程中动态调用工具，无需等待报告生成
"""
import asyncio
from typing import Dict, Any, List, AsyncGenerator
from app.services.mcp_service import mcp_service, MCPRequest, MCPResponse
from app.services.search_service import search_service
from app.services.llm_service import llm_service
from app.utils.logger import get_logger

logger = get_logger("MCPEnhanced")


class MCPEnhancedService:
    """MCP增强服务 - 支持流式和批量调用"""
    
    async def call_tool_stream(self, request: MCPRequest) -> AsyncGenerator[str, None]:
        """流式调用工具
        
        适用于需要长时间运行的工具调用，实时返回中间结果
        
        Args:
            request: 工具调用请求
        
        Yields:
            JSON格式的进度更新
        """
        tool_name = request.tool_name
        
        if tool_name not in mcp_service.handlers:
            yield f'{{"type": "error", "message": "工具不存在: {tool_name}"}}\n'
            return
        
        try:
            logger.info(f" 流式调用MCP工具: {tool_name}")
            
            # 发送开始信号
            yield f'{{"type": "start", "tool": "{tool_name}"}}\n'
            
            # 调用工具（支持流式输出）
            handler = mcp_service.handlers[tool_name]
            
            # 如果工具支持流式，则流式返回
            if hasattr(handler, '__aiter__'):
                async for chunk in handler(**request.arguments):
                    yield f'{{"type": "chunk", "data": {chunk}}}\n'
            else:
                # 否则一次性返回
                result = await handler(**request.arguments)
                yield f'{{"type": "result", "data": {result}}}\n'
            
            # 发送完成信号
            yield f'{{"type": "complete"}}\n'
            
        except Exception as e:
            logger.error(f" 流式工具调用失败 {tool_name}: {e}")
            yield f'{{"type": "error", "message": "{str(e)}"}}\n'
    
    async def batch_call_tools(self, requests: List[MCPRequest]) -> List[MCPResponse]:
        """批量并行调用工具
        
        适用于多个独立工具调用，并行执行提升效率
        
        Args:
            requests: 工具调用请求列表
        
        Returns:
            工具调用响应列表
        """
        logger.info(f" 批量调用 {len(requests)} 个MCP工具")
        
        # 并行执行所有工具调用
        tasks = [mcp_service.call_tool(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 工具 {requests[i].tool_name} 调用失败: {result}")
                responses.append(MCPResponse(
                    success=False,
                    error=str(result)
                ))
            else:
                responses.append(result)
        
        logger.info(f"✅ 批量工具调用完成，成功 {sum(1 for r in responses if r.success)}/{len(responses)}")
        return responses
    
    async def tool_chain(self, chain_requests: List[Dict[str, Any]]) -> List[MCPResponse]:
        """工具链调用 - 前一个工具的结果作为下一个工具的输入
        
        适用于需要顺序依赖的工具调用场景
        
        Args:
            chain_requests: 工具链请求列表
            格式: [{"tool_name": "search", "arguments": {"query": "xxx"}}, ...]
        
        Returns:
            工具调用响应列表
        """
        logger.info(f" 执行工具链，共 {len(chain_requests)} 步")
        
        results = []
        context = {}  # 上下文传递
        
        for i, req_dict in enumerate(chain_requests):
            try:
                # 构建请求，支持引用前一步结果
                tool_name = req_dict["tool_name"]
                arguments = req_dict.get("arguments", {}).copy()
                
                # 替换参数中的上下文引用（如 {{step_0.results}}）
                arguments = self._resolve_context(arguments, context)
                
                request = MCPRequest(tool_name=tool_name, arguments=arguments)
                response = await mcp_service.call_tool(request)
                
                if not response.success:
                    logger.error(f"❌ 工具链步骤 {i+1} 失败: {response.error}")
                    return results + [response]
                
                results.append(response)
                
                # 更新上下文
                context[f"step_{i}"] = response.data
                
                logger.info(f"✅ 工具链步骤 {i+1}/{len(chain_requests)} 完成")
                
            except Exception as e:
                logger.error(f"❌ 工具链步骤 {i+1} 异常: {e}")
                results.append(MCPResponse(success=False, error=str(e)))
                return results
        
        logger.info(f"✅ 工具链执行完成")
        return results
    
    def _resolve_context(self, arguments: Dict, context: Dict) -> Dict:
        """解析上下文引用
        
        将 {{step_0.field}} 替换为实际值
        
        Args:
            arguments: 参数字典
            context: 上下文字典
        
        Returns:
            解析后的参数字典
        """
        import re
        
        def replace_placeholder(match):
            path = match.group(1)  # 例如 "step_0.results.0.title"
            parts = path.split('.')
            
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list):
                    try:
                        value = value[int(part)]
                    except (ValueError, IndexError):
                        return match.group(0)  # 返回原字符串
                else:
                    return match.group(0)
                
                if value is None:
                    return match.group(0)
            
            return str(value)
        
        # 递归处理字典和列表
        def process_value(val):
            if isinstance(val, str):
                return re.sub(r'\{\{(.+?)\}\}', replace_placeholder, val)
            elif isinstance(val, dict):
                return {k: process_value(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [process_value(item) for item in val]
            else:
                return val
        
        return process_value(arguments)


# 全局单例
mcp_enhanced = MCPEnhancedService()
