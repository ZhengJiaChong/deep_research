"""
工作流图定义
"""
from langgraph.graph import StateGraph, END
from app.workflow.state import ResearchState
from app.workflow.nodes import (
    analyze_query_node,
    generate_outline_node,
    execute_tasks_parallel_node,
    generate_report_node
)
from app.utils.logger import get_logger

logger = get_logger("WorkflowGraph")

def create_research_graph():
    """创建研究工作流图
    
    流程：
    analyze_query → generate_outline → [execute_task_1, execute_task_2, ...] → generate_report
    """
    logger.info("🏗️ 创建研究工作流图")
    
    workflow = StateGraph(ResearchState)
    
    # 添加节点
    workflow.add_node('analyze_query', analyze_query_node)
    workflow.add_node('generate_outline', generate_outline_node)
    workflow.add_node('execute_tasks', execute_tasks_parallel_node)
    workflow.add_node('generate_report', generate_report_node)
    
    # 设置入口点
    workflow.set_entry_point('analyze_query')
    
    # 定义边
    workflow.add_edge('analyze_query', 'generate_outline')
    workflow.add_edge('generate_outline', 'execute_tasks')
    workflow.add_edge('execute_tasks', 'generate_report')
    
    # 设置终点
    workflow.add_edge('generate_report', END)
    
    # 编译工作流
    graph = workflow.compile()
    logger.info("✅ 研究工作流图创建完成")
    
    return graph

# 全局单例
research_graph = create_research_graph()
