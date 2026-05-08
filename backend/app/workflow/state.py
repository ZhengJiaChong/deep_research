"""
工作流状态定义
"""
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime

class SearchResult(TypedDict, total=False):
    """搜索结果"""
    title: str
    url: str
    content: str
    score: float

class TaskData(TypedDict, total=False):
    """研究任务数据"""
    task_id: str
    title: str
    description: str
    status: str  # pending, running, completed, failed
    search_keywords: List[str]
    search_results: List[SearchResult]
    analysis: str
    start_time: Optional[str]
    end_time: Optional[str]

class OutlineItem(TypedDict, total=False):
    """大纲项目"""
    id: str
    title: str
    description: str
    order: int

class ResearchState(TypedDict, total=False):
    """研究工作流状态"""
    research_id: str
    query: str
    analysis: dict
    outline: List[OutlineItem]
    tasks: List[TaskData]
    current_task_index: int
    report: str
    progress_logs: List[Dict[str, Any]]  # 进度日志
    citations: Dict[int, Dict]  # 引用数据 {id: citation_data}
    status: str
    error: Optional[str]
    created_at: str
    updated_at: str
