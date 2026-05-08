"""
MCP集成示例 - 在研究工作流中使用MCP工具

演示如何在研究过程中动态调用MCP工具，无需等待完整报告生成
"""
import sys
import os

# 添加项目根目录到路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))  # backend目录的父目录
sys.path.insert(0, PROJECT_ROOT)

from app.services.mcp_service import mcp_service, MCPRequest
from app.services.mcp_enhanced import mcp_enhanced
from app.utils.logger import get_logger

logger = get_logger("MCPIntegration")


async def example_1_direct_tool_call():
    """示例1：直接调用MCP工具（替代直接调用服务）
    
    传统方式：
        results = await search_service.search(query)
    
    MCP方式：
        request = MCPRequest(tool_name="search", arguments={"query": query})
        response = await mcp_service.call_tool(request)
        results = response.data["results"]
    
    优势：
    - 统一接口，易于切换底层实现
    - 支持工具热插拔
    - 便于监控和日志记录
    """
    logger.info("📌 示例1：直接调用MCP工具")
    
    # 调用搜索工具
    request = MCPRequest(
        tool_name="search",
        arguments={"query": "人工智能发展趋势", "max_results": 3}
    )
    
    response = await mcp_service.call_tool(request)
    
    if response.success:
        logger.info(f"✅ 找到 {response.data['count']} 条结果")
        return response.data["results"]
    else:
        logger.error(f"❌ 搜索失败: {response.error}")
        return []


async def example_2_parallel_search():
    """示例2：并行搜索多个关键词
    
    传统方式（串行）：
        results1 = await search_service.search(keyword1)
        results2 = await search_service.search(keyword2)
        results3 = await search_service.search(keyword3)
        # 耗时：3次API调用时间之和
    
    MCP方式（并行）：
        requests = [
            MCPRequest(tool_name="search", arguments={"query": kw})
            for kw in keywords
        ]
        responses = await mcp_enhanced.batch_call_tools(requests)
        # 耗时：最长的一次API调用时间
    """
    logger.info("📌 示例2：并行搜索多个关键词")
    
    keywords = ["人工智能", "机器学习", "深度学习"]
    
    # 构建批量请求
    requests = [
        MCPRequest(
            tool_name="search",
            arguments={"query": kw, "max_results": 2}
        )
        for kw in keywords
    ]
    
    # 并行执行
    responses = await mcp_enhanced.batch_call_tools(requests)
    
    # 处理结果
    all_results = []
    for i, response in enumerate(responses):
        if response.success:
            logger.info(f"✅ 关键词 '{keywords[i]}' 找到 {response.data['count']} 条结果")
            all_results.extend(response.data["results"])
        else:
            logger.error(f"❌ 关键词 '{keywords[i]}' 搜索失败: {response.error}")
    
    logger.info(f"📊 总共收集 {len(all_results)} 条结果")
    return all_results


async def example_3_tool_chain():
    """示例3：工具链 - 搜索后自动总结
    
    传统方式：
        # 步骤1：搜索
        results = await search_service.search(query)
        
        # 步骤2：手动提取内容
        content = "\n".join([r["content"] for r in results])
        
        # 步骤3：调用LLM总结
        summary = await llm_service.generate_summary(content)
    
    MCP方式（自动化）：
        chain_requests = [
            {"tool_name": "search", "arguments": {"query": query}},
            {"tool_name": "llm_chat", "arguments": {
                "message": f"请总结以下内容：{{{{step_0.results}}}}"
            }}
        ]
        responses = await mcp_enhanced.tool_chain(chain_requests)
    """
    logger.info("📌 示例3：工具链 - 搜索后自动总结")
    
    # 定义工具链
    chain_requests = [
        # 步骤1：搜索
        {
            "tool_name": "search",
            "arguments": {"query": "量子计算最新突破", "max_results": 3}
        },
        # 步骤2：基于搜索结果生成总结
        {
            "tool_name": "llm_chat",
            "arguments": {
                "message": "请根据以下搜索结果，用简洁的语言总结量子计算的最新突破：\n\n{{step_0.results}}"
            }
        }
    ]
    
    # 执行工具链
    responses = await mcp_enhanced.tool_chain(chain_requests)
    
    # 处理结果
    if len(responses) >= 2 and responses[1].success:
        summary = responses[1].data["response"]
        logger.info(f"✅ 自动生成总结:\n{summary[:200]}...")
        return summary
    else:
        logger.error("❌ 工具链执行失败")
        return None


async def example_4_streaming_search():
    """示例4：流式搜索 - 实时返回结果
    
    传统方式：
        # 等待所有结果返回
        results = await search_service.search(query, max_results=10)
        # 用户需要等待10秒才能看到第一个结果
    
    MCP方式（流式）：
        async for chunk in mcp_enhanced.call_tool_stream(request):
            # 每找到一个结果就立即返回
            display_result(chunk)
        # 用户1秒内就能看到第一个结果
    """
    logger.info("📌 示例4：流式搜索 - 实时返回结果")
    
    request = MCPRequest(
        tool_name="search",
        arguments={"query": "新能源汽车市场", "max_results": 5}
    )
    
    results = []
    async for chunk in mcp_enhanced.call_tool_stream(request):
        logger.info(f"  收到数据: {chunk}")
        # 这里可以实时推送给前端
        # yield chunk
        results.append(chunk)
    
    logger.info(f"✅ 流式搜索完成，共收到 {len(results)} 个数据包")
    return results


async def example_5_dynamic_tool_selection():
    """示例5：动态工具选择 - 根据问题类型自动选择工具
    
    根据用户问题的类型，智能选择合适的MCP工具
    """
    logger.info("📌 示例5：动态工具选择")
    
    questions = [
        ("什么是量子纠缠？", "llm_chat"),  # 知识问答 → LLM
        ("最新的AI新闻", "search"),          # 实时信息 → 搜索
        ("分析特斯拉财报", "search"),         # 数据分析 → 搜索
    ]
    
    for question, expected_tool in questions:
        # 简单规则：包含"最新"、"新闻"等词使用搜索，否则使用LLM
        if any(word in question for word in ["最新", "新闻", "财报", "市场"]):
            tool_name = "search"
        else:
            tool_name = "llm_chat"
        
        logger.info(f"  问题: {question}")
        logger.info(f"  选择工具: {tool_name} (预期: {expected_tool})")
        
        if tool_name == "search":
            request = MCPRequest(
                tool_name="search",
                arguments={"query": question, "max_results": 2}
            )
        else:
            request = MCPRequest(
                tool_name="llm_chat",
                arguments={"message": question}
            )
        
        response = await mcp_service.call_tool(request)
        
        if response.success:
            logger.info(f"  ✅ 成功获取结果")
        else:
            logger.error(f"  ❌ 失败: {response.error}")


async def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("MCP集成示例 - 打破'只能等待报告生成'的限制")
    print("="*70)
    
    # 示例1：直接调用
    print("\n【示例1】直接调用MCP工具")
    await example_1_direct_tool_call()
    
    # 示例2：并行搜索
    print("\n【示例2】并行搜索多个关键词")
    await example_2_parallel_search()
    
    # 示例3：工具链
    print("\n【示例3】工具链 - 搜索后自动总结")
    await example_3_tool_chain()
    
    # 示例4：流式搜索
    print("\n【示例4】流式搜索 - 实时返回结果")
    await example_4_streaming_search()
    
    # 示例5：动态工具选择
    print("\n【示例5】动态工具选择")
    await example_5_dynamic_tool_selection()
    
    print("\n" + "="*70)
    print("✅ 所有示例执行完成")
    print("="*70)


if __name__ == "__main__":
    import asyncio
    
    # 添加项目根目录到路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))  # backend目录的父目录
    sys.path.insert(0, PROJECT_ROOT)
    
    from app.services.mcp_tools import register_mcp_tools
    
    # 注册MCP工具
    register_mcp_tools()
    
    # 运行示例（添加异常处理和资源清理）
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Windows平台异步资源清理
        import sys
        if sys.platform == "win32":
            try:
                # 获取并关闭事件循环
                loop = asyncio.get_event_loop()
                if not loop.is_closed():
                    loop.close()
            except RuntimeError:
                pass  # 事件循环已关闭或不存在
