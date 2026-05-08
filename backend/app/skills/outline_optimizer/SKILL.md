---
name: 大纲优化
description: 大纲优化Skill。分析研究大纲的完整性、逻辑性和深度，提供优化建议。
license: MIT
metadata:
  version: "1.0"
  category: research-quality
  icon: ""
  color: "#409EFF"
---

# Outline Optimizer

Analyze research outlines and provide structured optimization suggestions.

## When to Use

### ✅ Activate When
- Research outline just generated (automatic trigger)
- User explicitly asks "optimize this outline" or "improve the structure"
- Coverage analysis shows gaps in topic coverage
- Outline has fewer than 3 main sections (likely incomplete)

### ❌ Skip When
- Single-topic outlines (overkill for simple queries)
- Already optimized in previous iteration
- User explicitly says "skip optimization"

## Evaluation Dimensions

Evaluate outlines across four dimensions (0-100 scale):

### 1. Completeness (权重 30%)
Does the outline cover all important aspects of the research question?

**Checklist**:
- [ ] Market/industry analysis included?
- [ ] Technical background covered?
- [ ] Current state/trends addressed?
- [ ] Future outlook/predictions?
- [ ] Competitive landscape?
- [ ] Stakeholder perspectives?

**Scoring**:
- 90-100: Comprehensive coverage, no major gaps
- 70-89: Good coverage, minor gaps
- 50-69: Missing 1-2 key aspects
- <50: Significant gaps, needs restructuring

### 2. Logic Flow (权重 25%)
Is there clear progression and logical relationship between sections?

**Good Pattern**: Background → Current State → Analysis → Future → Recommendations
**Bad Pattern**: Random topic ordering, no clear narrative arc

**Check for**:
- Clear beginning, middle, end
- Each section builds on previous
- No redundant or circular content
- Smooth transitions between topics

### 3. Depth (权重 25%)
Are descriptions detailed enough to guide research?

**Indicators**:
- Vague: "Analyze the market" (too broad)
- Good: "Analyze NEV market size, growth rate, and regional distribution in China (2020-2025)"

**Requirements**:
- Each section has specific focus
- Clear scope boundaries
- Actionable research directions

### 4. Relevance (权重 20%)
Does every section directly support answering the research question?

**Red Flags**:
- Tangential topics not related to core question
- Overly broad sections that dilute focus
- Missing critical aspects of the question

## Output Format

Return JSON with this structure:

```json
{
  "overall_score": 75,
  "dimensions": {
    "completeness": 80,
    "logic": 70,
    "depth": 65,
    "relevance": 85
  },
  "suggestions": [
    "建议增加'市场竞争格局'章节，分析主要厂商市场份额",
    "建议细化'技术发展路线'部分，区分短期和长期趋势",
    "建议补充'政策法规影响'，特别是补贴政策变化"
  ],
  "missing_topics": [
    "消费者行为与偏好分析",
    "供应链与产业链结构",
    "国际市场竞争对比"
  ]
}
```

**Requirements**:
- `overall_score`: Average of four dimensions (integer 0-100)
- `suggestions`: At least 3 specific, actionable improvements
- `missing_topics`: List of important but absent topics (can be empty)

## Anti-Rationalization Table

| AI Excuse | Counter |
| --- | --- |
| "The outline is good enough" | Good enough ≠ optimal. Provide at least 3 specific improvements even for strong outlines. |
| "No major issues found" | Even good outlines can be refined. Suggest enhancements to depth, clarity, or structure. |
| "User didn't ask for optimization" | This skill was explicitly selected by user. Execute it regardless. |
| "The outline is too short to evaluate" | Short outlines need MORE optimization. Suggest expansion areas. |
| "I'm not sure what's missing" | Compare against standard research frameworks (PESTLE, SWOT, Porter's Five Forces). |

## Examples

### Example 1: Weak Outline

**Input**:
```
Query: "新能源汽车市场发展趋势"
Outline:
1. 技术背景
2. 市场规模
```

**Output**:
```json
{
  "overall_score": 45,
  "dimensions": {
    "completeness": 40,
    "logic": 50,
    "depth": 30,
    "relevance": 60
  },
  "suggestions": [
    "大纲过于简略，建议扩展到5-7个主要章节",
    "缺少'竞争格局'分析，应包含主要厂商对比",
    "缺少'政策环境'章节，新能源行业受政策影响大",
    "每个章节描述太简单，需要具体研究方向"
  ],
  "missing_topics": [
    "政策法规与补贴机制",
    "消费者接受度与行为",
    "充电基础设施发展",
    "国际市场竞争态势",
    "产业链上下游分析"
  ]
}
```

### Example 2: Strong Outline

**Input**:
```
Query: "人工智能在医疗领域的应用现状"
Outline:
1. 技术基础：AI核心算法与医疗数据特点
2. 应用场景：影像诊断、药物研发、个性化治疗
3. 案例分析：国内外典型应用案例对比
4. 挑战与风险：数据隐私、算法偏见、监管合规
5. 未来展望：技术演进方向与市场预测
```

**Output**:
```json
{
  "overall_score": 82,
  "dimensions": {
    "completeness": 85,
    "logic": 90,
    "depth": 75,
    "relevance": 80
  },
  "suggestions": [
    "建议在'应用场景'中增加'医院管理优化'（如排班、资源分配）",
    "建议在'挑战与风险'中补充'临床验证难度'和'医生接受度'",
    "可以在'技术基础'中简要说明不同AI技术（CV/NLP/ML）的适用场景"
  ],
  "missing_topics": [
    "医疗AI的商业模式与盈利路径",
    "医疗机构数字化转型现状"
  ]
}
```

## Implementation Notes

- Use LLM to analyze outline quality (temperature=0.7 for balanced creativity/consistency)
- Compare against research best practices and domain knowledge
- Be specific in suggestions - avoid vague advice like "make it better"
- Prioritize suggestions by impact (most important first)
- Keep tone constructive and helpful, not critical
