---
name: 搜索评估
description: 搜索结果质量评估Skill。多维度评估搜索结果的相关性、可信度和时效性。
license: MIT
metadata:
  version: "1.0"
  category: research-quality
  icon: ""
  color: "#E6A23C"
---

# Search Result Evaluator

Assess search result quality and provide prioritization recommendations.

## When to Use

### ✅ Activate When
- Search completed with multiple results (automatic trigger)
- User asks "which sources are best?" or "filter low-quality results"
- Too many results (>15) and need prioritization
- Mixed quality detected (some obviously poor sources)
- Academic/professional research requiring high-quality sources

### ❌ Skip When
- Very few results (<3) - all should be reviewed manually
- User explicitly browsing all results
- Exploratory search where quantity matters more than quality

## Evaluation Algorithm

### Scoring Formula

```
Final Score = Relevance × 50% + Credibility × 30% + Timeliness × 20%
```

### 1. Relevance (0-100) - Weight 50%

How well does the result match the search query?

**Keyword Matching**:
```python
query_words = set(query.lower().split())
title_words = set(title.lower().split())
content_words = set(content.lower().split()[:100])

title_match = len(query_words & title_words) / max(len(query_words), 1)
content_match = len(query_words & content_words) / max(len(query_words), 1)

relevance_score = (title_match × 0.7 + content_match × 0.3) × 100
```

**Semantic Considerations** (LLM-enhanced):
- Synonym matching (e.g., "EV" = "electric vehicle")
- Context relevance (does it answer the core question?)
- Topic drift detection (tangential but related content)

**Scoring Guide**:
- 90-100: Directly answers query, high keyword overlap
- 70-89: Relevant, addresses main aspects
- 50-69: Partially relevant, some tangential content
- <50: Weak relevance, off-topic

### 2. Credibility (0-100) - Weight 30%

Is the source trustworthy and authoritative?

**Domain Authority Tiers**:
- **Tier 1** (+30 points): .gov, .edu, academic journals (Nature, Science, IEEE, ACM)
- **Tier 2** (+20 points): Major media (Reuters, AP, BBC, NYT), established industry reports
- **Tier 3** (+10 points): Professional blogs, company official sites, trade publications
- **Tier 4** (+0 points): Personal blogs, forums, social media, wikis

**Content Quality Signals**:
- Length >500 words: +15 points
- Length 200-500 words: +10 points
- Clear author attribution: +10 points
- Citations/references provided: +10 points
- Publication date visible: +5 points
- Professional formatting: +5 points

**Base Score**: 50 points

**Maximum**: 100 points (capped)

### 3. Timeliness (0-100) - Weight 20%

Is the information current enough for the research?

**Year Detection**:
```python
import re
years = re.findall(r'\b(20\d{2})\b', content)
if years:
    latest_year = max(int(y) for y in years)
    year_diff = current_year - latest_year
else:
    return 50  # No date found, neutral score
```

**Scoring**:
- Current year: 100
- 1 year old: 90
- 2 years old: 80
- 3 years old: 70
- 4+ years old: max(30, 70 - year_diff × 10)

**Context Matters**:
- For historical topics: older content may still be relevant
- For technology/trends: recency is critical
- Adjust based on research domain

## Recommendation Levels

Based on final score, categorize results:

| Score Range | Recommendation | Action |
| --- | --- | --- |
| ≥70 | **keep** | Prioritize these results |
| 40-69 | **review** | Review manually if needed |
| <40 | **discard** | Consider excluding from research |

## Output Format

```json
{
  "total_results": 15,
  "average_score": 68,
  "high_quality_count": 8,
  "medium_quality_count": 5,
  "low_quality_count": 2,
  "results": [
    {
      "url": "https://example.com/article",
      "title": "Article Title",
      "score": 85,
      "dimensions": {
        "relevance": 90,
        "credibility": 80,
        "timeliness": 75
      },
      "recommendation": "keep"
    }
  ],
  "recommendations": [
    "建议优先使用前8个高质量结果（评分≥70）",
    "2个低质量结果建议重新搜索替换",
    "整体质量良好，平均评分68/100"
  ]
}
```

## Anti-Rationalization Table

| AI Excuse | Counter |
| --- | --- |
| "All results look fine to me" | Objective scoring reveals quality differences. Evaluate systematically. |
| "I can't determine timeliness without dates" | Use neutral score (50) and note the limitation. Don't guess. |
| "This blog post seems informative" | Check authority tier. Personal blogs score lower regardless of content quality. |
| "The user will decide what's relevant" | Provide scored recommendations. User makes final decision with data. |
| "Too many results to evaluate thoroughly" | Use automated scoring first, then flag borderline cases for manual review. |

## Examples

### Example 1: Mixed Quality Results

**Input**:
```json
{
  "query": "新能源汽车市场发展趋势",
  "results": [
    {
      "url": "https://www.mckinsey.com/industries/automotive/our-insights/ev-market-2025",
      "title": "The Future of Electric Vehicles: 2025 Market Outlook",
      "content": "Comprehensive analysis of EV market growth, regional trends..."
    },
    {
      "url": "https://random-blog.com/my-thoughts-on-cars",
      "title": "Why I Think Electric Cars Are Cool",
      "content": "I bought a Tesla last year and I love it..."
    },
    {
      "url": "https://old-news-site.com/2019/ev-sales",
      "title": "EV Sales Data 2019",
      "content": "In 2019, electric vehicle sales reached..."
    }
  ]
}
```

**Output**:
```json
{
  "total_results": 3,
  "average_score": 62,
  "high_quality_count": 1,
  "medium_quality_count": 1,
  "low_quality_count": 1,
  "results": [
    {
      "url": "https://www.mckinsey.com/industries/automotive/our-insights/ev-market-2025",
      "title": "The Future of Electric Vehicles: 2025 Market Outlook",
      "score": 92,
      "dimensions": {
        "relevance": 95,
        "credibility": 95,
        "timeliness": 85
      },
      "recommendation": "keep"
    },
    {
      "url": "https://random-blog.com/my-thoughts-on-cars",
      "title": "Why I Think Electric Cars Are Cool",
      "score": 38,
      "dimensions": {
        "relevance": 40,
        "credibility": 20,
        "timeliness": 60
      },
      "recommendation": "discard"
    },
    {
      "url": "https://old-news-site.com/2019/ev-sales",
      "title": "EV Sales Data 2019",
      "score": 56,
      "dimensions": {
        "relevance": 70,
        "credibility": 60,
        "timeliness": 30
      },
      "recommendation": "review"
    }
  ],
  "recommendations": [
    "建议优先使用McKinsey报告（评分92，权威来源）",
    "建议替换个人博客引用（评分38，权威性不足）",
    "2019年数据已过时，建议寻找2023-2025年最新数据"
  ]
}
```

## Implementation Notes

- Use rule-based scoring for speed (no LLM needed for basic evaluation)
- Cache domain authority ratings to avoid repeated lookups
- Log scoring details for debugging and improvement
- Consider adding LLM-based semantic relevance for complex queries
- Batch process results for efficiency
