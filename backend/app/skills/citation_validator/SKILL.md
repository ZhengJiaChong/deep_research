---
name: 引用验证
description: 引用链接验证Skill。检查研究引用链接的存活率、内容相关性和来源权威性。
license: MIT
metadata:
  version: "1.0"
  category: research-quality
  icon: ""
  color: "#67C23A"
---

# Citation Validator

Validate research citations for link accessibility, content relevance, and source authority.

## When to Use

### ✅ Activate When
- Research completed with citations (automatic trigger)
- User asks "verify these sources" or "check citation quality"
- Suspicious or broken links detected
- Need to improve report credibility
- Academic or professional research requiring high source quality

### ❌ Skip When
- No citations in the research
- Informal/internal research where source verification isn't critical
- User explicitly says "skip citation check"

## Validation Dimensions

### 1. Link Validity (Pass/Fail)
Can the URL be accessed?

**Checks**:
- HTTP status code (200 = valid, 404/500 = invalid)
- DNS resolution
- Timeout handling (max 5 seconds)

**Scoring**: Binary (valid/invalid)

### 2. Content Relevance (0-100)
Does the cited content support the research point?

**Evaluation Criteria**:
- Topic alignment with research question
- Information freshness (recent data preferred)
- Depth of coverage (superficial vs. comprehensive)
- Direct support for claims made

**LLM Assessment**:
```prompt
Evaluate this citation's relevance to the research topic:

Topic: {research_query}
Citation Title: {title}
Citation Content: {content_snippet}

Score 0-100 based on:
- How well does it address the topic?
- Is the information current and accurate?
- Does it provide substantive support?

Return only a number.
```

### 3. Source Authority (0-100)
Is the source credible and trustworthy?

**Domain Tier System**:
- **Tier 1** (+30 points): .gov, .edu, major academic journals (Nature, Science, IEEE)
- **Tier 2** (+20 points): Established media (Reuters, BBC, NYT), industry reports
- **Tier 3** (+10 points): Professional blogs, company websites
- **Tier 4** (+0 points): Personal blogs, forums, social media

**Content Quality Indicators**:
- Author credentials mentioned? (+10)
- References/citations provided? (+10)
- Publication date clear? (+5)
- Professional formatting? (+5)

### 4. Timeliness (0-100)
Is the information current enough?

**Year-Based Scoring** (for content with dates):
- Current year: 100
- 1 year old: 90
- 2 years old: 80
- 3 years old: 70
- 4+ years old: max(30, 70 - years_old × 10)

**No Date Found**: 50 (neutral)

## Output Format

```json
{
  "total_count": 15,
  "valid_count": 12,
  "invalid_count": 3,
  "overall_score": 80,
  "citations": [
    {
      "url": "https://example.com/article",
      "title": "Article Title",
      "is_valid": true,
      "quality_score": 85,
      "authority_tier": 2,
      "timeliness_score": 90,
      "issues": []
    },
    {
      "url": "https://broken-link.com",
      "title": "Broken Link",
      "is_valid": false,
      "quality_score": 0,
      "authority_tier": 0,
      "timeliness_score": 0,
      "issues": ["Link inaccessible (HTTP 404)"]
    }
  ],
  "recommendations": [
    "建议替换3个失效链接",
    "建议增加更多学术来源（当前仅2个Tier 1来源）",
    "2个引用内容过于陈旧（>3年），建议寻找更新数据"
  ]
}
```

**Calculation**:
```
overall_score = (valid_count / total_count) × 100
```

## Anti-Rationalization Table

| AI Excuse | Counter |
| --- | --- |
| "Most links are valid, no need to check all" | Even one broken link undermines credibility. Check ALL citations. |
| "The content looks relevant" | Verify programmatically. Don't assume - validate. |
| "This is just a blog post, authority doesn't matter" | For research, source quality matters. Flag low-authority sources. |
| "I can't access some URLs due to restrictions" | Mark as 'unknown' and note the limitation. Don't guess. |
| "The user didn't ask for detailed validation" | This skill was selected. Execute full validation. |

## Examples

### Example 1: Mixed Quality Citations

**Input**:
```json
{
  "citations": [
    {
      "url": "https://www.nature.com/articles/s41586-023-01234",
      "title": "Advances in Renewable Energy Technology",
      "content": "Recent breakthroughs in solar cell efficiency..."
    },
    {
      "url": "https://broken-site.com/old-article",
      "title": "Old Article",
      "content": ""
    },
    {
      "url": "https://blog.example.com/my-opinion",
      "title": "My Thoughts on Energy",
      "content": "I think renewable energy is the future..."
    }
  ]
}
```

**Output**:
```json
{
  "total_count": 3,
  "valid_count": 2,
  "invalid_count": 1,
  "overall_score": 67,
  "citations": [
    {
      "url": "https://www.nature.com/articles/s41586-023-01234",
      "title": "Advances in Renewable Energy Technology",
      "is_valid": true,
      "quality_score": 95,
      "authority_tier": 1,
      "timeliness_score": 100,
      "issues": []
    },
    {
      "url": "https://broken-site.com/old-article",
      "title": "Old Article",
      "is_valid": false,
      "quality_score": 0,
      "authority_tier": 0,
      "timeliness_score": 0,
      "issues": ["Link inaccessible (timeout after 5s)"]
    },
    {
      "url": "https://blog.example.com/my-opinion",
      "title": "My Thoughts on Energy",
      "is_valid": true,
      "quality_score": 35,
      "authority_tier": 4,
      "timeliness_score": 50,
      "issues": [
        "Low authority source (personal blog)",
        "Content lacks substantive data"
      ]
    }
  ],
  "recommendations": [
    "建议替换1个失效链接",
    "建议用学术期刊或官方报告替换个人博客引用",
    "当前仅1个Tier 1来源，建议增加至3个以上"
  ]
}
```

## Implementation Notes

- Use `aiohttp` for async HTTP checks (timeout=5s)
- Use LLM for content relevance scoring (temperature=0.3 for consistency)
- Cache domain authority ratings to avoid repeated lookups
- Handle rate limiting gracefully (respect robots.txt)
- Log validation results for debugging
