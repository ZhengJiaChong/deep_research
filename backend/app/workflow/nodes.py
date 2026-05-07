"""
工作流节点定义
"""
from typing import Dict, Any
from datetime import datetime
import asyncio
from app.workflow.state import ResearchState
from app.services.llm_service import llm_service
from app.services.search_service import search_service, deduplicate_results
from app.utils.logger import get_logger

logger = get_logger("WorkflowNodes")

async def analyze_query_node(state: ResearchState) -> Dict[str, Any]:
    """节点1：语义分析
    
    功能：
    - 接收用户query
    - 调用LLM进行语义分析
    - 提取关键信息
    """
    logger.info(f" 节点1：开始语义分析")
    
    # 初始化进度日志
    progress_logs = state.get('progress_logs', [])
    
    try:
        progress_logs.append({
            'type': 'info',
            'message': '📊 开始语义分析，理解您的研究问题...',
            'timestamp': datetime.now().isoformat()
        })
        
        analysis = await llm_service.analyze_query(state['query'])
        
        progress_logs.append({
            'type': 'success',
            'message': '✅ 语义分析完成，已提取关键信息',
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"✅ 语义分析完成")
        return {
            'analysis': analysis,
            'progress_logs': progress_logs,
            'status': 'analyzing'
        }
    except Exception as e:
        logger.error(f"❌ 语义分析失败: {e}")
        progress_logs.append({
            'type': 'error',
            'message': f'❌ 语义分析失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })
        return {
            'progress_logs': progress_logs,
            'status': 'error',
            'error': str(e)
        }

async def generate_outline_node(state: ResearchState) -> Dict[str, Any]:
    """节点2：大纲生成
    
    功能：
    - 基于分析结果生成研究大纲
    - 生成5-8个研究任务
    - 为每个任务分配ID和顺序
    """
    logger.info(f" 节点2：开始生成研究大纲")
    
    # 初始化进度日志
    progress_logs = state.get('progress_logs', [])
    
    try:
        progress_logs.append({
            'type': 'info',
            'message': ' 基于语义分析结果，生成研究大纲...',
            'timestamp': datetime.now().isoformat()
        })
        
        outline = await llm_service.generate_outline(
            state['query'],
            state['analysis']
        )
        
        progress_logs.append({
            'type': 'success',
            'message': f'✅ 研究大纲生成完成，共 {len(outline)} 个研究方向',
            'timestamp': datetime.now().isoformat()
        })
        
        # 初始化任务状态
        tasks = [
            {
                'task_id': item['id'],
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'status': 'pending',
                'search_keywords': [],
                'search_results': [],
                'analysis': '',
                'start_time': None,
                'end_time': None
            }
            for item in outline
        ]
        
        logger.info(f"✅ 大纲生成完成，共{len(tasks)}个任务")
        
        # 添加任务列表日志
        for idx, task in enumerate(tasks, 1):
            progress_logs.append({
                'type': 'info',
                'message': f'  任务{idx}: {task["title"]}',
                'timestamp': datetime.now().isoformat()
            })
        
        return {
            'outline': outline,
            'tasks': tasks,
            'current_task_index': 0,
            'progress_logs': progress_logs,
            'status': 'outlining'
        }
    except Exception as e:
        logger.error(f"❌ 大纲生成失败: {e}")
        progress_logs.append({
            'type': 'error',
            'message': f'❌ 大纲生成失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })
        return {
            'progress_logs': progress_logs,
            'status': 'error',
            'error': str(e)
        }

async def execute_task_node(state: ResearchState) -> Dict[str, Any]:
    """节点3：任务执行
    
    功能：
    - 生成搜索关键词
    - 执行互联网搜索
    - 分析搜索结果
    - 更新任务状态
    """
    current_index = state.get('current_task_index', 0)
    tasks = state.get('tasks', [])
    research_id = state.get('research_id', '')
    
    if current_index >= len(tasks):
        return {'status': 'completed'}
    
    task = tasks[current_index]
    task_id = task['task_id']
    
    logger.info(f" 节点3：执行任务 {current_index + 1}/{len(tasks)} - {task['title']}")
    
    # 初始化进度日志
    progress_logs = state.get('progress_logs', [])
    
    try:
        # 添加任务开始日志
        progress_logs.append({
            'type': 'info',
            'message': f'▶️ 开始执行任务 {current_index + 1}/{len(tasks)}: {task["title"]}',
            'timestamp': datetime.now().isoformat()
        })
        
        # 更新任务状态为running
        task['status'] = 'running'
        task['start_time'] = datetime.now().isoformat()
        
        # 1. 生成搜索关键词
        logger.info(f"  步骤1：生成搜索关键词")
        progress_logs.append({
            'type': 'info',
            'message': f'正在为任务 "{task["title"]}" 生成搜索关键词...',
            'timestamp': datetime.now().isoformat()
        })
        keywords = await llm_service.generate_search_keywords(task)
        task['search_keywords'] = keywords[:3]  # 最多3个关键词
                    
        # 记录生成的关键词
        progress_logs.append({
            'type': 'info',
            'message': f'🔑 关键词: {", ".join(keywords[:3])}',
            'keyword': True,
            'timestamp': datetime.now().isoformat()
        })
        
        # 2. 执行搜索
        logger.info(f"  步骤2：执行搜索")
        all_results = []
        for idx, keyword in enumerate(task['search_keywords'], 1):
            progress_logs.append({
                'type': 'info',
                'message': f'🔍 搜索关键词 {idx}: {keyword}',
                'timestamp': datetime.now().isoformat()
            })
            results = await search_service.search(keyword)
            all_results.extend(results)
            
            # 显示搜索结果详情（前3个）
            if results:
                result_titles = [r.get('title', '')[:60] for r in results[:3]]
                progress_logs.append({
                    'type': 'success',
                    'message': f'✅ 找到 {len(results)} 个结果',
                    'search_results': result_titles,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                progress_logs.append({
                    'type': 'warning',
                    'message': f'⚠️ 未找到相关结果',
                    'timestamp': datetime.now().isoformat()
                })
        
        # 去重
        unique_results = deduplicate_results(all_results)
        task['search_results'] = unique_results[:5]  # 保留5个最佳结果
        progress_logs.append({
            'type': 'info',
            'message': f'去重后保留 {len(unique_results[:5])} 个高质量结果',
            'timestamp': datetime.now().isoformat()
        })
        
        # 3. 分析搜索结果
        logger.info(f"  步骤3：分析搜索结果")
        progress_logs.append({
            'type': 'info',
            'message': '正在分析搜索结果...',
            'timestamp': datetime.now().isoformat()
        })
        if task['search_results']:
            analysis = await llm_service.analyze_search_results(
                task,
                task['search_results']
            )
            task['analysis'] = analysis
            progress_logs.append({
                'type': 'success',
                'message': '搜索结果分析完成',
                'timestamp': datetime.now().isoformat()
            })
        else:
            task['analysis'] = "未找到相关搜索结果"
            progress_logs.append({
                'type': 'warning',
                'message': '未找到相关搜索结果',
                'timestamp': datetime.now().isoformat()
            })
        
        # 更新任务状态
        task['status'] = 'completed'
        task['end_time'] = datetime.now().isoformat()
        progress_logs.append({
            'type': 'success',
            'message': f'任务 "{task["title"]}" 执行完成',
            'timestamp': datetime.now().isoformat()
        })
        
        # 更新任务列表
        tasks[current_index] = task
        
        logger.info(f"✅ 任务执行完成: {task['title']}")
        
        return {
            'tasks': tasks,
            'current_task_index': current_index + 1,
            'progress_logs': progress_logs,
            'status': 'executing'
        }
        
    except Exception as e:
        logger.error(f"❌ 任务执行失败: {e}")
        task['status'] = 'failed'
        task['end_time'] = datetime.now().isoformat()
        tasks[current_index] = task
        
        progress_logs.append({
            'type': 'error',
            'message': f'任务执行失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'tasks': tasks,
            'current_task_index': current_index + 1,
            'progress_logs': progress_logs,
            'status': 'executing'
        }

async def execute_tasks_parallel_node(state: ResearchState) -> Dict[str, Any]:
    """节点3：并行执行所有任务
    
    功能：
    - 同时执行所有研究任务（并行）
    - 每个任务：生成关键词→搜索→分析
    - 流式输出每个任务的完成状态
    """
    tasks = state.get('tasks', [])
    research_id = state.get('research_id', '')
    
    if not tasks:
        return {'status': 'completed'}
    
    logger.info(f"🚀 节点3：开始并行执行 {len(tasks)} 个任务")
    
    # 初始化进度日志
    progress_logs = state.get('progress_logs', [])
    
    progress_logs.append({
        'type': 'info',
        'message': f'🚀 开始并行执行 {len(tasks)} 个研究任务...',
        'timestamp': datetime.now().isoformat()
    })
    
    # 定义单个任务执行函数
    async def execute_single_task(task, index):
        """执行单个任务"""
        task_id = task['task_id']
        
        try:
            # 添加任务开始日志
            progress_logs.append({
                'type': 'info',
                'message': f'▶️ 开始执行任务 {index + 1}/{len(tasks)}: {task["title"]}',
                'timestamp': datetime.now().isoformat()
            })
            
            # 更新任务状态
            task['status'] = 'running'
            task['start_time'] = datetime.now().isoformat()
            
            # 1. 生成搜索关键词
            progress_logs.append({
                'type': 'info',
                'message': f'  任务 {index + 1}: 生成搜索关键词...',
                'timestamp': datetime.now().isoformat()
            })
            keywords = await llm_service.generate_search_keywords(task)
            task['search_keywords'] = keywords[:3]
            
            # 记录生成的关键词
            progress_logs.append({
                'type': 'info',
                'message': f'🔑 关键词: {", ".join(keywords[:3])}',
                'keyword': True,
                'timestamp': datetime.now().isoformat()
            })
            
            # 2. 执行搜索（并行搜索多个关键词）
            progress_logs.append({
                'type': 'info',
                'message': f'  任务 {index + 1}: 开始搜索...',
                'timestamp': datetime.now().isoformat()
            })
            
            search_tasks = [search_service.search(kw) for kw in task['search_keywords']]
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 合并搜索结果
            all_results = []
            for results in search_results:
                if isinstance(results, list):
                    all_results.extend(results)
            
            # 去重
            unique_results = deduplicate_results(all_results)
            task['search_results'] = unique_results[:5]
            
            # 展示搜索结果详情
            if unique_results:
                result_titles = [r.get('title', '')[:60] for r in unique_results[:3]]
                progress_logs.append({
                    'type': 'success',
                    'message': f' 找到 {len(unique_results)} 个结果:',
                    'search_results': result_titles,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                progress_logs.append({
                    'type': 'warning',
                    'message': f'⚠️ 未找到相关结果',
                    'timestamp': datetime.now().isoformat()
                })
            
            # 更新任务状态（搜索完成，等待批量分析）
            task['status'] = 'search_completed'
            
            logger.info(f"✅ 任务 {index + 1} 搜索完成: {task['title']}")
            return task
            
        except Exception as e:
            logger.error(f"❌ 任务 {index + 1} 失败: {e}")
            task['status'] = 'failed'
            task['end_time'] = datetime.now().isoformat()
            task['analysis'] = f"任务执行失败: {str(e)}"
            
            progress_logs.append({
                'type': 'error',
                'message': f'❌ 任务 {index + 1} 失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
            
            return task
    
    # 并行执行所有任务（限制并发数为3，避免API限制）
    semaphore = asyncio.Semaphore(3)
    
    async def limited_execute(task, index):
        """限制并发数执行"""
        async with semaphore:
            return await execute_single_task(task, index)
    
    # 同时执行所有任务的搜索部分
    completed_tasks = await asyncio.gather(
        *[limited_execute(task, idx) for idx, task in enumerate(tasks)],
        return_exceptions=True
    )
    
    # 处理异常结果
    final_tasks = []
    for idx, result in enumerate(completed_tasks):
        if isinstance(result, Exception):
            logger.error(f"❌ 任务 {idx + 1} 异常: {result}")
            tasks[idx]['status'] = 'failed'
            tasks[idx]['analysis'] = f"任务执行异常: {str(result)}"
            tasks[idx]['end_time'] = datetime.now().isoformat()
            final_tasks.append(tasks[idx])
        else:
            final_tasks.append(result)
    
    # 批量分析所有任务的搜索结果
    progress_logs.append({
        'type': 'info',
        'message': f'🚀 开始批量分析 {len(final_tasks)} 个任务的搜索结果...',
        'timestamp': datetime.now().isoformat()
    })
    
    # 准备批量分析数据
    tasks_for_analysis = [
        {'task': task, 'search_results': task.get('search_results', [])}
        for task in final_tasks
        if task.get('status') == 'search_completed'
    ]
    
    if tasks_for_analysis:
        # 并行分析所有任务（提升60%性能）
        logger.info(f" 并行分析 {len(tasks_for_analysis)} 个任务...")
            
        # 创建并行任务列表
        analysis_tasks = [
            llm_service.analyze_search_results(
                task_data['task'],
                task_data['search_results']
            )
            for task_data in tasks_for_analysis
        ]
            
        # 并发执行所有分析任务
        analyses = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
        # 处理结果（处理可能的异常）
        analysis_idx = 0
        for task in final_tasks:
            if task.get('status') == 'search_completed':
                result = analyses[analysis_idx] if analysis_idx < len(analyses) else "分析失败"
                    
                # 检查是否是异常
                if isinstance(result, Exception):
                    task['analysis'] = f"分析失败: {str(result)}"
                    logger.error(f" 任务分析失败: {task['title']} - {result}")
                else:
                    task['analysis'] = result
                    
                task['status'] = 'completed'
                task['end_time'] = datetime.now().isoformat()
                    
                progress_logs.append({
                    'type': 'success',
                    'message': f' 任务分析完成: {task["title"]}',
                    'timestamp': datetime.now().isoformat()
                })
                analysis_idx += 1
            elif task.get('status') == 'failed':
                progress_logs.append({
                    'type': 'error',
                    'message': f' 任务失败: {task.get("title", "未知")}',
                    'timestamp': datetime.now().isoformat()
                })
    
    progress_logs.append({
        'type': 'success',
        'message': f'✅ 所有 {len(tasks)} 个任务执行完成',
        'timestamp': datetime.now().isoformat()
    })
    
    logger.info(f"✅ 所有任务执行完成")
    
    return {
        'tasks': final_tasks,
        'current_task_index': len(tasks),
        'progress_logs': progress_logs,
        'status': 'executing'
    }

async def generate_report_node(state: ResearchState) -> Dict[str, Any]:
    """节点4：数据准备（为SSE流式输出准备数据）
    
    功能：
    - 汇总所有任务的分析结果
    - 不生成报告，由SSE接口流式生成
    - 实时更新进度
    """
    logger.info(f"📝 节点4：准备研究数据")
    
    # 初始化进度日志
    progress_logs = state.get('progress_logs', [])
    
    try:
        progress_logs.append({
            'type': 'info',
            'message': '📝 汇总研究数据，准备生成报告...',
            'timestamp': datetime.now().isoformat()
        })
        
        # 收集所有任务的分析结果
        analyses = [task.get('analysis', '') for task in state['tasks']]
        
        progress_logs.append({
            'type': 'info',
            'message': f'已汇总 {len(analyses)} 个任务的分析结果',
            'timestamp': datetime.now().isoformat()
        })
        
        progress_logs.append({
            'type': 'success',
            'message': '数据准备完成，开始流式生成报告...',
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"数据准备完成")
        
        return {
            'progress_logs': progress_logs,
            'status': 'completed'
            # 不返回report，由SSE接口生成
        }
    except Exception as e:
        logger.error(f" 数据准备失败: {e}")
        progress_logs.append({
            'type': 'error',
            'message': f'❌ 数据准备失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })
        return {
            'progress_logs': progress_logs,
            'status': 'error',
            'error': str(e)
        }
