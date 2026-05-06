# 智能问答：深度研究应用

## 📋 项目概述

这是一个基于AI的深度研究应用，用户输入研究问题后，系统自动生成研究大纲（todo list），并针对每个大纲任务进行互联网检索和智能分析，最终生成完整研究报告。

## ️ 项目结构

```
case-deep_research/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── api/               # API路由
│   │   ├── services/          # 业务服务
│   │   ├── workflow/          # LangGraph工作流
│   │   ├── utils/             # 工具类
│   │   ├── config.py          # 配置管理
│   │   └── main.py            # FastAPI入口
│   └── requirements.txt       # Python依赖
│
├── frontend/                   # 前端项目
│   ├── src/
│   │   ├── api/               # API接口
│   │   ├── stores/            # Pinia状态管理
│   │   ├── views/             # 页面组件
│   │   ├── router/            # 路由配置
│   │   ├── App.vue            # 根组件
│   │   └── main.js            # 入口文件
│   ├── package.json           # Node依赖
│   └── vite.config.js         # Vite配置
│
└── docs/                       # 文档目录
    ── 项目详细文档.md         # 详细技术文档
```

## 🚀 快速开始

### 1. 后端启动

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m app.main
```

后端服务将运行在 http://localhost:8000

### 2. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将运行在 http://localhost:5173

## 🔧 技术栈

### 后端
- **框架**: FastAPI + Python 3.10+
- **AI框架**: LangChain + LangGraph
- **大模型**: OpenRouter (支持多种模型)
- **搜索引擎**: Tavily Search API
- **数据验证**: Pydantic

### 前端
- **框架**: Vue 3 + Composition API
- **构建工具**: Vite 5
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **Markdown渲染**: marked

## 📝 核心功能

### 1. 智能语义分析
- 理解用户研究问题的意图
- 提取关键概念和研究维度
- 自动识别问题类型

### 2. 研究大纲生成
- 根据语义分析生成5-8个研究任务
- 任务之间有清晰的逻辑关系
- 自动排序和分配任务ID

### 3. 并行研究执行
- 为每个任务生成搜索关键词
- 使用Tavily进行深度搜索
- 自动去重和筛选搜索结果

### 4. 智能分析
- 对搜索结果进行深度分析
- 提取关键信息和数据
- 生成专业见解

### 5. 报告生成
- 汇总所有任务的分析结果
- 生成结构化研究报告
- 支持Markdown格式导出

## 🔑 API密钥配置

项目要求通过环境变量配置API密钥，不支持硬编码。

### 配置步骤

**1. 创建.env文件**
```bash
cd backend
cp .env.example .env
```

**2. 编辑.env文件**
```bash
# OpenRouter API密钥（必填）
JWZT_OPENROUTER_API_KEY=你的密钥

# Tavily API密钥（必填）
JWZT_TAVILY_API_KEY=你的密钥
```

**3. 获取API密钥**
- OpenRouter：https://openrouter.ai/
- Tavily：https://tavily.com/

详见：[docs/环境变量配置指南.md](docs/环境变量配置指南.md)

## 📊 使用流程

1. **输入问题**: 在前端首页输入研究问题
2. **语义分析**: 系统分析问题意图
3. **生成大纲**: 自动创建研究大纲（5-8个任务）
4. **执行研究**: 逐个任务进行搜索和分析
5. **查看结果**: 实时查看研究进度和搜索结果
6. **获取报告**: 研究完成后查看完整报告

## 🔍 API接口

### POST /api/research/start
开始研究
```json
{
  "query": "研究问题"
}
```

### GET /api/research/{id}/outline
获取研究大纲

### GET /api/research/{id}/progress
获取研究进度

### GET /api/research/{id}/report
获取最终报告

## 💡 使用提示

- 输入具体、明确的研究问题可以获得更好的结果
- 研究过程可能需要几分钟时间，请耐心等待
- 所有搜索数据来源都会保留，可以点击查看详情
- 研究完成后可查看和复制完整的研究报告

## 📚 文档

详细技术文档请查看：[docs/项目详细文档.md](docs/项目详细文档.md)

## ️ 注意事项

- 确保网络连接正常（需要访问OpenRouter和Tavily API）
- 大模型调用可能较慢，请耐心等待
- 生产环境请修改API密钥和CORS配置

##  许可证

MIT License
