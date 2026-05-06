"""
Pydantic数据模型定义
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# 请求模型
class StartResearchRequest(BaseModel):
    """开始研究请求"""
    query: str = Field(..., description="研究问题", min_length=5, max_length=2000)

# 响应模型
class StartResearchResponse(BaseModel):
    """开始研究响应"""
    research_id: str
    status: str
    message: str

class OutlineItemResponse(BaseModel):
    """大纲项目响应"""
    id: str
    title: str
    description: str
    status: str
    order: int

class OutlineResponse(BaseModel):
    """大纲响应"""
    research_id: str
    query: str
    outline: List[OutlineItemResponse]
    created_at: str

class SearchResultResponse(BaseModel):
    """搜索结果响应"""
    title: str
    url: str
    content: str
    score: float

class TaskProgressResponse(BaseModel):
    """任务进度响应"""
    task_id: str
    title: str
    status: str
    search_keywords: List[str]
    search_results: List[SearchResultResponse]
    analysis: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]

class ResearchStatusResponse(BaseModel):
    """研究状态响应"""
    research_id: str
    status: str
    progress: float  # 0-100
    current_task: Optional[str]
    outline_count: int
    completed_tasks: int
    created_at: str
    progress_logs: Optional[List[Dict[str, Any]]] = []  # 进度日志

class ReportResponse(BaseModel):
    """报告响应"""
    research_id: str
    report: str
    word_count: int
    generated_at: str

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
