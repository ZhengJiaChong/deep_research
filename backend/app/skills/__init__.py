"""
Skills加载器 - 从标准目录结构加载Skills
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List
from app.utils.logger import get_logger

logger = get_logger("SkillsLoader")


class SkillsLoader:
    """Skills加载器"""
    
    def __init__(self, skills_dir: str = None):
        """
        初始化
        
        Args:
            skills_dir: Skills目录路径
        """
        if skills_dir is None:
            # 默认使用 backend/app/skills 目录
            skills_dir = os.path.join(os.path.dirname(__file__), '..', 'skills')
        
        self.skills_dir = Path(skills_dir)
        self.skills_cache = {}
        
        logger.info(f"✅ Skills加载器已初始化，目录: {self.skills_dir}")
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的Skills
        
        Returns:
            Skills列表
        """
        if not self.skills_dir.exists():
            logger.warning(f"⚠️ Skills目录不存在: {self.skills_dir}")
            return []
        
        skills = []
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            
            # 解析SKILL.md获取元信息
            skill_info = self._parse_skill_md(skill_md)
            if skill_info:
                skills.append(skill_info)
        
        logger.info(f"📋 加载了 {len(skills)} 个Skills")
        return skills
    
    def _parse_skill_md(self, skill_md_path: Path) -> Dict[str, Any]:
        """
        解析SKILL.md文件（支持YAML frontmatter）
            
        Args:
            skill_md_path: SKILL.md文件路径
            
        Returns:
            Skill元信息
        """
        try:
            content = skill_md_path.read_text(encoding='utf-8')
                
            # 检查是否有YAML frontmatter
            if content.startswith('---'):
                # 解析YAML frontmatter
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    yaml_content = parts[1].strip()
                        
                    # 简单YAML解析（避免依赖pyyaml）
                    skill_info = {
                        "id": skill_md_path.parent.name,
                        "name": "",
                        "description": "",
                        "icon": "",
                        "color": "",
                        "version": "1.0.0"
                    }
                        
                    for line in yaml_content.split('\n'):
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                            
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                                
                            if key == 'name':
                                skill_info['name'] = value
                            elif key == 'description':
                                skill_info['description'] = value
                            elif key == 'license':
                                skill_info['license'] = value
                        
                    # 从metadata中读取icon和color
                    if 'metadata:' in yaml_content:
                        metadata_section = False
                        for line in yaml_content.split('\n'):
                            if line.strip() == 'metadata:':
                                metadata_section = True
                                continue
                                
                            if metadata_section:
                                if line.startswith('  '):
                                    key, value = line.strip().split(':', 1)
                                    key = key.strip()
                                    value = value.strip().strip('"').strip("'")
                                        
                                    if key == 'icon':
                                        skill_info['icon'] = value
                                    elif key == 'color':
                                        skill_info['color'] = value
                                    elif key == 'version':
                                        skill_info['version'] = value
                                else:
                                    metadata_section = False
                        
                    return skill_info
                
            # 回退到旧格式解析（兼容）
            skill_info = {
                "id": skill_md_path.parent.name,
                "name": "",
                "description": "",
                "icon": "",
                "color": "",
                "version": "1.0.0"
            }
                
            for line in content.split('\n'):
                line = line.strip()
                    
                if line.startswith('- **ID**:'):
                    skill_info['id'] = line.split('`')[1] if '`' in line else line.split(':')[1].strip()
                elif line.startswith('- **名称**:') or line.startswith('- **Name**:'): 
                    skill_info['name'] = line.split(':', 1)[1].strip()
                elif line.startswith('- **描述**:') or line.startswith('- **Description**:'): 
                    skill_info['description'] = line.split(':', 1)[1].strip()
                elif line.startswith('- **图标**:') or line.startswith('- **Icon**:'): 
                    skill_info['icon'] = line.split(':', 1)[1].strip()
                elif line.startswith('- **颜色**:') or line.startswith('- **Color**:'): 
                    skill_info['color'] = line.split(':', 1)[1].strip()
                elif line.startswith('- **版本**:') or line.startswith('- **Version**:'): 
                    skill_info['version'] = line.split(':', 1)[1].strip()
                
            return skill_info
                
        except Exception as e:
            logger.error(f"❌ 解析SKILL.md失败: {e}")
            return None
    
    async def execute_skill(self, skill_id: str, **kwargs) -> Dict[str, Any]:
        """
        执行指定的Skill
        
        Args:
            skill_id: Skill ID
            **kwargs: 传递给Skill的参数
        
        Returns:
            执行结果
        """
        skill_dir = self.skills_dir / skill_id
        
        if not skill_dir.exists():
            return {
                "success": False,
                "error": f"Skill不存在: {skill_id}"
            }
        
        script_path = skill_dir / "scripts" / f"{skill_id}.py"
        
        if not script_path.exists():
            return {
                "success": False,
                "error": f"Skill脚本不存在: {script_path}"
            }
        
        try:
            # 动态导入并执行
            import importlib.util
            spec = importlib.util.spec_from_file_location(skill_id, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 调用execute函数
            result = await module.execute(**kwargs)
            
            logger.info(f"✅ Skill执行成功: {skill_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Skill执行失败: {skill_id}, 错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 全局实例
skills_loader = SkillsLoader()
