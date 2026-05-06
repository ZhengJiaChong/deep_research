"""
项目配置管理
"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 加载 .env 文件
load_dotenv()

class Settings(BaseSettings):
    """项目配置中心"""
    
    # --- 基础配置 ---
    APP_NAME: str = "Deep Research API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # --- 服务器配置 ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # --- 路径配置 ---
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT: str = os.path.join(BASE_DIR, "..")
    
    # --- OpenRouter 配置 ---
    OPENROUTER_API_KEY: str = os.getenv("JWZT_OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openrouter/free")
    STREAM_OUTPUT: bool = os.getenv("STREAM_OUTPUT", "true").lower() == "true"
    
    # --- Tavily 配置 ---
    TAVILY_API_KEY: str = os.getenv("JWZT_TAVILY_API_KEY")
    TAVILY_MAX_RESULTS: int = 5
    
    # --- 研究配置 ---
    MAX_TASKS_PER_RESEARCH: int = 10
    MAX_SEARCH_PER_TASK: int = 3
    MAX_RESULTS_PER_SEARCH: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

    def __init__(self):
        super().__init__()
        # 验证必需的API密钥
        if not self.OPENROUTER_API_KEY:
            raise ValueError(
                "未找到 JWZT_OPENROUTER_API_KEY 环境变量。"
                "请在 backend/.env 文件中配置或设置系统环境变量。"
            )
        if not self.TAVILY_API_KEY:
            raise ValueError(
                "未找到 JWZT_TAVILY_API_KEY 环境变量。"
                "请在 backend/.env 文件中配置或设置系统环境变量。"
            )

# 全局配置实例
settings = Settings()
