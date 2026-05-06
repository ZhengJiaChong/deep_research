"""
大模型服务 - 封装OpenRouter API调用
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List, AsyncGenerator
import json
import re
from app.config import settings
from app.utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger("LLMService")

class LLMService:
    """大模型服务类"""
    
    def __init__(self):
        """初始化LLM客户端"""
        self.client = ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            temperature=0.7,
        )
        # 创建流式客户端
        self.stream_client = ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base=settings.OPENROUTER_BASE_URL,
            temperature=0.7,
            streaming=True,
        )
        logger.info(f"✅ LLM服务已初始化，模型: {settings.OPENROUTER_MODEL}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """语义分析 - 分析用户问题的意图和关键信息
        
        Args:
            query: 用户输入的研究问题
        
        Returns:
            分析结果字典
        """
        prompt = f"""你是一个专业的研究助手。请分析以下研究问题，提取关键信息：

研究问题：{query}

请分析并返回JSON格式（仅返回JSON，不要其他内容）：
{{
  "core_domain": "核心研究领域",
  "key_concepts": ["关键概念1", "关键概念2"],
  "research_dimensions": ["研究维度1", "研究维度2"],
  "question_type": "问题类型（如：市场分析、技术评估等）"
}}"""
        
        logger.info(f" 开始语义分析: {query[:50]}...")
        
        messages = [
            SystemMessage(content="你是一个专业的研究分析助手，擅长语义理解和问题分解。"),
            HumanMessage(content=prompt)
        ]
        
        response = await self.client.ainvoke(messages)
        content = response.content
        
        # 解析JSON
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                logger.info(f"✅ 语义分析完成")
                return result
            else:
                logger.warning("⚠️ 未找到JSON格式，返回原始内容")
                return {"raw_analysis": content}
        except Exception as e:
            logger.error(f"❌ JSON解析失败: {e}")
            return {"raw_analysis": content, "error": str(e)}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_outline(self, query: str, analysis: Dict) -> List[Dict[str, Any]]:
        """生成研究大纲
        
        Args:
            query: 原始问题
            analysis: 语义分析结果
        
        Returns:
            大纲任务列表
        """
        analysis_str = json.dumps(analysis, ensure_ascii=False)
        
        prompt = f"""基于以下研究问题和语义分析，生成一个详细的研究大纲：

研究问题：{query}
分析结果：{analysis_str}

要求：
1. 生成5-8个研究任务
2. 每个任务应具体明确，可独立研究
3. 任务之间应有逻辑关系
4. 按照合理的顺序排列

请返回JSON数组格式（仅返回JSON数组，不要其他内容）：
[
  {{
    "id": "task_001",
    "title": "任务标题",
    "description": "任务详细描述",
    "order": 1
  }}
]"""
        
        logger.info(f" 开始生成研究大纲")
        
        messages = [
            SystemMessage(content="你是一个专业的研究规划助手，擅长制定研究大纲。"),
            HumanMessage(content=prompt)
        ]
        
        response = await self.client.ainvoke(messages)
        content = response.content
        
        # 解析JSON
        try:
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                outline = json.loads(json_match.group())
                logger.info(f"✅ 生成{len(outline)}个研究任务")
                return outline
            else:
                logger.warning("⚠️ 未找到JSON数组")
                return [{"id": "task_001", "title": "综合分析", "description": "全面研究", "order": 1}]
        except Exception as e:
            logger.error(f"❌ 大纲JSON解析失败: {e}")
            return [{"id": "task_001", "title": "综合分析", "description": "全面研究", "order": 1}]
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_search_keywords(self, task: Dict[str, Any]) -> List[str]:
        """为研究任务生成搜索关键词
        
        Args:
            task: 研究任务信息
        
        Returns:
            搜索关键词列表
        """
        prompt = f"""为以下研究任务生成搜索关键词：

任务：{task.get('title', '')}
描述：{task.get('description', '')}

要求：
1. 生成3-5个搜索关键词
2. 关键词应具体、可搜索
3. 使用中文和英文关键词组合
4. 关键词之间用换行分隔

请直接返回关键词列表，每行一个关键词，不要其他内容。"""
        
        logger.info(f"🔑 为任务生成搜索关键词: {task.get('title', '')}")
        
        messages = [
            SystemMessage(content="你是一个专业的信息检索助手，擅长生成精准的搜索关键词。"),
            HumanMessage(content=prompt)
        ]
        
        response = await self.client.ainvoke(messages)
        content = response.content
        
        # 解析关键词
        keywords = [k.strip() for k in content.strip().split('\n') if k.strip()]
        logger.info(f"✅ 生成{len(keywords)}个关键词")
        return keywords[:5]  # 最多5个
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze_search_results(self, task: Dict[str, Any], search_results: List[Dict]) -> str:
        """分析搜索结果（精简版）
        
        Args:
            task: 研究任务
            search_results: 搜索结果列表
        
        Returns:
            分析结果文本
        """
        # 格式化搜索结果（只使用标题和前100字摘要）
        results_text = "\n\n".join([
            f"标题：{r.get('title', '')}\n"
            f"摘要：{r.get('content', '')[:100]}"  # 只取前100字
            for r in search_results[:3]  # 只分析前3个结果
        ])
        
        prompt = f"""请分析以下搜索结果，提取核心信息：

研究任务：{task.get('title', '')}

搜索结果：
{results_text}

请提供：
1. 核心发现（1-2句）
2. 关键数据（列举）

要求：
- 简洁明了
- 引用具体数据
- 用中文回答"""
        
        logger.info(f" 分析搜索结果（精简版），任务: {task.get('title', '')}")
        
        messages = [
            SystemMessage(content="你是一个专业的研究分析师，擅长从搜索结果中提取关键信息。"),
            HumanMessage(content=prompt)
        ]
        
        response = await self.client.ainvoke(messages)
        content = response.content
        
        logger.info(f"✅ 搜索结果分析完成")
        return content
    
    async def analyze_search_results_batch(self, tasks_data: List[Dict[str, Any]]) -> List[str]:
        """批量分析多个任务的搜索结果
        
        Args:
            tasks_data: 任务数据列表，每个包含task和search_results
        
        Returns:
            分析结果列表
        """
        if not tasks_data:
            return []
        
        # 格式化所有任务的数据
        batch_text = "\n\n".join([
            f"【任务 {idx + 1}】\n"
            f"标题：{item['task'].get('title', '')}\n"
            f"描述：{item['task'].get('description', '')}\n"
            f"\n搜索结果：\n" +
            "\n".join([
                f"  - {r.get('title', '')}: {r.get('content', '')[:100]}"
                for r in item['search_results'][:2]  # 每个任务只用2个结果
            ])
            for idx, item in enumerate(tasks_data)
        ])
        
        prompt = f"""请分析以下多个研究任务的搜索结果，为每个任务提取核心信息：

{batch_text}

请为每个任务提供：
1. 核心发现（1-2句）
2. 关键数据（列举）

返回格式（JSON数组）：
[
  "任务1的分析结果",
  "任务2的分析结果"
]

要求：
- 简洁明了
- 每个任务独立分析
- 用中文回答"""
        
        logger.info(f" 批量分析 {len(tasks_data)} 个任务的搜索结果")
        
        messages = [
            SystemMessage(content="你是一个专业的研究分析师，擅长批量分析多个研究任务的搜索结果。"),
            HumanMessage(content=prompt)
        ]
        
        response = await self.client.ainvoke(messages)
        content = response.content
        
        # 尝试解析JSON数组
        try:
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                analyses = json.loads(json_match.group())
                logger.info(f"✅ 批量分析完成，共 {len(analyses)} 个结果")
                return analyses
            else:
                # 如果解析失败，返回单个结果重复N次
                logger.warning("⚠️ JSON解析失败，返回默认结果")
                return [content] * len(tasks_data)
        except Exception as e:
            logger.error(f"❌ 批量分析JSON解析失败: {e}")
            return [f"分析失败: {str(e)}"] * len(tasks_data)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_report(self, query: str, outline: List[Dict], analyses: List[str]) -> str:
        """生成最终研究报告
        
        Args:
            query: 原始问题
            outline: 研究大纲
            analyses: 各任务的分析结果
        
        Returns:
            完整的研究报告
        """
        # 格式化大纲和分析结果
        outline_text = "\n".join([
            f"{i+1}. {task.get('title', '')}"
            for i, task in enumerate(outline)
        ])
        
        analyses_text = "\n\n".join([
            f"### {outline[i].get('title', '任务' + str(i+1))}\n{analysis}"
            for i, analysis in enumerate(analyses)
        ])
        
        prompt = f"""请基于以下研究过程和结果，生成一份完整、专业的研究报告：

原始问题：{query}

研究大纲：
{outline_text}

各任务分析结果：
{analyses_text}

要求：
1. 报告结构完整（引言、主体、结论）
2. 内容专业、深入
3. 逻辑清晰、条理分明
4. 使用Markdown格式
5. 包含具体数据和案例
6. 长度适中（2000-5000字）

请直接返回研究报告内容（Markdown格式）。"""
        
        logger.info(f"📝 开始生成最终研究报告")
        
        messages = [
            SystemMessage(content="你是一个专业的研究专家，擅长撰写深度研究报告。"),
            HumanMessage(content=prompt)
        ]
        
        response = await self.client.ainvoke(messages)
        content = response.content
        
        logger.info(f"✅ 研究报告生成完成，字数: {len(content)}")
        return content
    
    async def generate_report_stream(self, query: str, outline: List[Dict], analyses: List[str]) -> AsyncGenerator[str, None]:
        """流式生成最终研究报告
        
        Args:
            query: 原始问题
            outline: 研究大纲
            analyses: 各任务的分析结果
        
        Yields:
            流式输出的文本片段
        """
        # 格式化大纲和分析结果
        outline_text = "\n".join([
            f"{i+1}. {task.get('title', '')}"
            for i, task in enumerate(outline)
        ])
        
        analyses_text = "\n\n".join([
            f"### {outline[i].get('title', '任务' + str(i+1))}\n{analysis}"
            for i, analysis in enumerate(analyses)
        ])
        
        prompt = f"""请基于以下研究过程和结果，生成一份完整、专业的研究报告：

原始问题：{query}

研究大纲：
{outline_text}

各任务分析结果：
{analyses_text}

要求：
1. 报告结构完整（引言、主体、结论）
2. 内容专业、深入
3. 逻辑清晰、条理分明
4. 使用Markdown格式
5. 包含具体数据和案例
6. 长度适中（2000-5000字）

请直接返回研究报告内容（Markdown格式）。"""
        
        logger.info(f"📝 开始流式生成最终研究报告")
        
        messages = [
            SystemMessage(content="你是一个专业的研究专家，擅长撰写深度研究报告。"),
            HumanMessage(content=prompt)
        ]
        
        # 流式调用
        async for chunk in self.stream_client.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
        
        logger.info(f"✅ 研究报告流式生成完成")

# 全局单例
llm_service = LLMService()
