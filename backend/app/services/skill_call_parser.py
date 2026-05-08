"""
Skill调用解析器
解析LLM返回的[SKILL_CALL: name]标记并执行Skill
"""
import re
from typing import Dict, Any, List, Optional
from app.skills import skills_loader
from app.utils.logger import get_logger

logger = get_logger("SkillCallParser")


class SkillCallParser:
    """Skill调用解析器"""
    
    def __init__(self):
        """初始化解析器"""
        # Skill调用标记格式：[SKILL_CALL: skill_id]params[/SKILL_CALL]
        self.skill_call_pattern = re.compile(
            r'\[SKILL_CALL:\s*(\S+)\](.*?)\[/SKILL_CALL\]',
            re.DOTALL
        )
    
    def parse_skill_calls(self, text: str) -> List[Dict[str, Any]]:
        """解析文本中的Skill调用标记
        
        Args:
            text: LLM返回的文本
        
        Returns:
            List[Dict]: Skill调用列表
                [
                    {
                        "skill_id": "outline-optimizer",
                        "params": "{...}",
                        "position": 123  # 在文本中的位置
                    }
                ]
        """
        skill_calls = []
        
        for match in self.skill_call_pattern.finditer(text):
            skill_id = match.group(1).strip()
            params_str = match.group(2).strip()
            
            skill_calls.append({
                "skill_id": skill_id,
                "params": self._parse_params(params_str),
                "position": match.start(),
                "full_match": match.group(0)
            })
        
        return skill_calls
    
    def _parse_params(self, params_str: str) -> Dict[str, Any]:
        """解析Skill调用参数
        
        参数格式支持：
        1. JSON格式：{"outline": [...], "query": "..."}
        2. 简单键值对：outline=[...], query="..."
        3. 空参数：{}
        """
        try:
            # 尝试解析JSON
            import json
            if params_str.startswith('{'):
                return json.loads(params_str)
        except:
            pass
        
        # 简单解析：按逗号分割
        params = {}
        if params_str:
            parts = params_str.split(',')
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    params[key.strip()] = value.strip()
        
        return params
    
    async def execute_skill_calls(
        self,
        skill_calls: List[Dict[str, Any]],
        research_id: str = None
    ) -> List[Dict[str, Any]]:
        """执行Skill调用
        
        Args:
            skill_calls: Skill调用列表
            research_id: 研究ID（用于记录事件）
        
        Returns:
            List[Dict]: Skill执行结果
        """
        results = []
        
        for call in skill_calls:
            skill_id = call['skill_id']
            params = call['params']
            
            try:
                logger.info(f"🔧 执行Skill调用: {skill_id}, 参数: {params}")
                
                # 调用Skill
                result = await skills_loader.execute_skill(skill_id, **params)
                
                results.append({
                    "skill_id": skill_id,
                    "success": True,
                    "result": result
                })
                
                # 记录事件（如果提供了research_id）
                if research_id:
                    from app.services.research_service import research_service
                    research = research_service.research_store.get(research_id)
                    if research:
                        research['skill_call_events'].append({
                            "skill_id": skill_id,
                            "success": True,
                            "timestamp": __import__('datetime').datetime.now().isoformat()
                        })
                
            except Exception as e:
                logger.error(f"❌ Skill调用失败: {skill_id}, 错误: {e}")
                results.append({
                    "skill_id": skill_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def replace_skill_calls_with_results(
        self,
        text: str,
        skill_calls: List[Dict[str, Any]],
        results: List[Dict[str, Any]]
    ) -> str:
        """将Skill调用标记替换为结果说明
        
        Args:
            text: 原始文本
            skill_calls: Skill调用列表
            results: Skill执行结果
        
        Returns:
            str: 替换后的文本
        """
        modified_text = text
        
        # 从后往前替换（避免位置偏移）
        for call, result in zip(reversed(skill_calls), reversed(results)):
            if result['success']:
                replacement = f"\n[Skill执行结果: {call['skill_id']}] {self._format_result(result['result'])}\n"
            else:
                replacement = f"\n[Skill执行失败: {call['skill_id']}] {result.get('error', '未知错误')}\n"
            
            modified_text = modified_text.replace(call['full_match'], replacement)
        
        return modified_text
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """格式化Skill执行结果为简短说明
        
        Args:
            result: Skill执行结果
        
        Returns:
            str: 格式化后的结果说明
        """
        if not result:
            return "无结果"
        
        # 根据result类型格式化
        if isinstance(result, dict):
            # 提取关键信息
            suggestions = result.get('suggestions', [])
            if suggestions:
                return f"发现{len(suggestions)}个优化建议"
            
            score = result.get('overall_score')
            if score is not None:
                return f"评分: {score}/10"
            
            valid_count = result.get('valid_count')
            if valid_count is not None:
                return f"验证{result.get('total_checked', 0)}个链接，{valid_count}个有效"
        
        return str(result)[:200]  # 截断过长文本


# 全局单例
skill_call_parser = SkillCallParser()
