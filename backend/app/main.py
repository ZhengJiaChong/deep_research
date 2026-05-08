"""
FastAPI 应用入口
"""
import sys
import os

# 确保能加载到项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(BASE_DIR, "..")
sys.path.append(PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.research import router as research_router
from app.api.mcp_router import router as mcp_router
from app.api.mcp_enhanced_router import router as mcp_enhanced_router
from app.api.skills_router import router as skills_router
from app.utils.logger import get_logger

logger = get_logger("Main")

# 初始化 FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="智能问答：深度研究应用 API 服务"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册业务路由
app.include_router(research_router, prefix="/api", tags=["Research"])
app.include_router(mcp_router, tags=["MCP"])
app.include_router(mcp_enhanced_router, tags=["MCP-Enhanced"])
app.include_router(skills_router, tags=["Skills"])

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用深度研究API",
        "docs": "/docs",
        "version": settings.APP_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # 配置根logger级别
    logging.basicConfig(level=logging.INFO)
    
    logger.info(f"正在启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"  # 显式设置日志级别
    )
