"""
研究服务 - 管理研究状态和执行工作流
"""
from typing import Dict, Any, Optional
from datetime import datetime
from app.workflow.graph import research_graph
from app.utils.logger import get_logger
import uuid

logger = get_logger("ResearchService")

class ResearchService:
    """研究服务类"""
    
    def __init__(self):
        """初始化研究服务"""
        self.research_store = {}  # 研究数据存储
        logger.info("✅ 研究服务已初始化")
    
    def _generate_research_id(self) -> str:
        """生成研究ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"research_{timestamp}_{unique_id}"
    
    async def start_research(self, query: str) -> str:
        """开始研究
        
        Args:
            query: 用户输入的研究问题
        
        Returns:
            research_id: 研究ID
        """
        research_id = self._generate_research_id()
        logger.info(f"🚀 开始研究: {research_id}")
        
        # 初始化研究状态
        initial_state = {
            'research_id': research_id,
            'query': query,
            'analysis': {},
            'outline': [],
            'tasks': [],
            'current_task_index': 0,
            'report': '',
            'progress_logs': [],  # 进度日志
            'status': 'starting',
            'error': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # 存储研究
        self.research_store[research_id] = initial_state
        
        # 异步执行工作流
        import asyncio
        asyncio.create_task(self._run_research_workflow(research_id, initial_state))
        
        return research_id
    
    async def _run_research_workflow(self, research_id: str, initial_state: Dict):
        """执行研究工作流
        
        Args:
            research_id: 研究ID
            initial_state: 初始状态
        """
        try:
            logger.info(f"⚙️ 执行研究工作流: {research_id}")
            
            # 执行LangGraph工作流
            final_state = await research_graph.ainvoke(initial_state)
            
            # 更新研究状态
            self.research_store[research_id] = final_state
            
            logger.info(f"✅ 研究工作流执行完成: {research_id}")
            
        except Exception as e:
            logger.error(f"❌ 研究工作流执行失败: {research_id}, 错误: {e}")
            self.research_store[research_id]['status'] = 'error'
            self.research_store[research_id]['error'] = str(e)
    
    async def get_research(self, research_id: str) -> Optional[Dict]:
        """获取研究数据
        
        Args:
            research_id: 研究ID
        
        Returns:
            研究数据字典
        """
        return self.research_store.get(research_id)
    
    async def get_research_progress(self, research_id: str) -> Dict[str, Any]:
        """获取研究进度
        
        Args:
            research_id: 研究ID
        
        Returns:
            进度信息
        """
        research = self.research_store.get(research_id)
        
        if not research:
            return {
                'error': '研究不存在',
                'research_id': research_id
            }
        
        tasks = research.get('tasks', [])
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.get('status') == 'completed')
        
        # 计算进度百分比
        if total_tasks == 0:
            progress = 10 if research.get('status') in ['analyzing', 'outlining'] else 0
        else:
            # 基础进度（分析+大纲）占20%，任务执行占60%，报告生成占20%
            progress = 20 + int((completed_tasks / total_tasks) * 60)
            
            if research.get('status') == 'completed':
                progress = 100
        
        return {
            'research_id': research_id,
            'status': research.get('status', 'unknown'),
            'progress': progress,
            'current_task': tasks[research.get('current_task_index', 0)].get('title', '') if tasks and research.get('current_task_index', 0) < len(tasks) else '',
            'outline_count': total_tasks,
            'completed_tasks': completed_tasks,
            'created_at': research.get('created_at', ''),
            'updated_at': research.get('updated_at', '')
        }
    
    async def get_outline(self, research_id: str) -> Dict[str, Any]:
        """获取研究大纲
        
        Args:
            research_id: 研究ID
        
        Returns:
            大纲数据
        """
        research = self.research_store.get(research_id)
        
        if not research:
            return {'error': '研究不存在'}
        
        return {
            'research_id': research_id,
            'query': research.get('query', ''),
            'outline': research.get('outline', []),
            'created_at': research.get('created_at', '')
        }
    
    async def get_report(self, research_id: str) -> Dict[str, Any]:
        """获取最终报告
        
        Args:
            research_id: 研究ID
        
        Returns:
            报告数据
        """
        research = self.research_store.get(research_id)
        
        if not research:
            return {'error': '研究不存在'}
        
        if research.get('status') != 'completed':
            return {
                'error': '研究尚未完成',
                'status': research.get('status', 'unknown')
            }
        
        return {
            'research_id': research_id,
            'report': research.get('report', ''),
            'word_count': len(research.get('report', '')),
            'generated_at': research.get('updated_at', '')
        }

# 全局单例
research_service = ResearchService()
