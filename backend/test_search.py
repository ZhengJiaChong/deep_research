"""
测试免费在线搜索功能
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.multi_search_service import multi_search_service

async def test_search():
    """测试搜索功能"""
    print("=" * 60)
    print("🔍 测试免费在线搜索")
    print("=" * 60)
    
    # 测试查询
    test_queries = [
        "Python 3.12 新特性",
        "AI大模型最新进展 2024",
        "新能源汽车市场分析"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}/{len(test_queries)}: {query}")
        print(f"{'='*60}")
        
        try:
            results = await multi_search_service.search(query, max_results=3)
            
            print(f"\n✅ 找到 {len(results)} 个结果:")
            for j, result in enumerate(results, 1):
                print(f"\n[{j}] {result.get('title', '无标题')}")
                print(f"    URL: {result.get('url', '无链接')}")
                print(f"    摘要: {result.get('content', '无摘要')[:100]}...")
                print(f"    引擎: {result.get('engine', '未知')}")
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
    
    print(f"\n{'='*60}")
    print("✅ 测试完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(test_search())
