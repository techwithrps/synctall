import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

# Search paths to handle standard .env and Windows notepad-auto-saved .env.txt files
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
agent_dir = os.path.dirname(os.path.abspath(__file__))

# Prioritize agent_dir (local) over root_dir (global/desktop) to avoid loading wrong project's .env!
possible_paths = [
    os.path.join(agent_dir, ".env"),
    os.path.join(agent_dir, ".env.txt"),
    os.path.join(root_dir, ".env"),
    os.path.join(root_dir, ".env.txt"),
]

env_path = None
for path in possible_paths:
    if os.path.exists(path):
        env_path = path
        break

if not env_path:
    env_path = os.path.join(agent_dir, ".env")

# Pre-load the determined env path to ensure os.getenv works flawlessly in both blocks
load_dotenv(env_path)

class Settings(BaseSettings):
    """
    Application configurations. Loaded from environment variables or local .env file.
    """
    SUPABASE_URL: str = Field("https://placeholder.supabase.co", description="Supabase project API URL")
    SUPABASE_SERVICE_ROLE_KEY: str = Field("placeholder", description="Supabase service role secret key")
    TALLY_URL: str = Field("http://localhost:9000", description="Tally ERP localhost endpoint")
    TALLY_COMPANY: str = Field("100000", description="Tally Company Name or Code")
    TALLY_USERNAME: str = Field("", description="Tally basic auth username")
    TALLY_PASSWORD: str = Field("", description="Tally basic auth password")
    SYNC_INTERVAL_SECONDS: int = Field(60, description="Synchronization routine sleep duration (default: 60s)")
    LOG_LEVEL: str = Field("INFO", description="Console and file logger verbosity level")
    
    # Oracle DB
    DB_USER: str = Field("C##COLLEGETEST", description="Oracle Database Username")
    DB_PASSWORD: str = Field("COLLEGETEST_1250#", description="Oracle Database Password")
    DB_CONNECT_STRING: str = Field("103.234.185.186:1521/xe", description="Oracle Database connection string")
    DB_SCHEMA: str = Field("C##COLLAGETEST", description="Oracle Database Schema")
    DB_COMPANY_ID: int = Field(10, description="Oracle Company ID")
    
    # Sync switches
    DISABLE_TALLY_TO_DB: bool = Field(True, description="Disable Tally to DB student sync route")
    DISABLE_DB_TO_TALLY: bool = Field(True, description="Disable DB to Tally student sync route")
    DISABLE_TRANSACTION_SYNC: bool = Field(True, description="Disable transaction sync route")

    # DB Selection
    USE_ORACLE: bool = Field(True, description="Use Oracle database for synchronization")
    USE_SUPABASE: bool = Field(False, description="Use Supabase database for synchronization")

    model_config = SettingsConfigDict(
        env_file=env_path,
        env_file_encoding="utf-8",
        extra="ignore"
    )

try:
    settings = Settings()
except Exception as e:
    # Safe fallback loader using pre-loaded values if direct Pydantic initialization encounters validation blocks
    settings = Settings(
        SUPABASE_URL=os.getenv("SUPABASE_URL", "https://placeholder.supabase.co"),
        SUPABASE_SERVICE_ROLE_KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "placeholder"),
        TALLY_URL=os.getenv("TALLY_URL", "http://localhost:9000"),
        TALLY_COMPANY=os.getenv("TALLY_COMPANY", "100000"),
        TALLY_USERNAME=os.getenv("TALLY_USERNAME", ""),
        TALLY_PASSWORD=os.getenv("TALLY_PASSWORD", ""),
        SYNC_INTERVAL_SECONDS=int(os.getenv("SYNC_INTERVAL_SECONDS", "60")),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        DB_USER=os.getenv("DB_USER", "C##COLLEGETEST"),
        DB_PASSWORD=os.getenv("DB_PASSWORD", "COLLEGETEST_1250#"),
        DB_CONNECT_STRING=os.getenv("DB_CONNECT_STRING", "103.234.185.186:1521/xe"),
        DB_SCHEMA=os.getenv("DB_SCHEMA", "C##COLLAGETEST"),
        DB_COMPANY_ID=int(os.getenv("DB_COMPANY_ID", "10")),
        DISABLE_TALLY_TO_DB=os.getenv("DISABLE_TALLY_TO_DB", "True").lower() in ("true", "1", "yes"),
        DISABLE_DB_TO_TALLY=os.getenv("DISABLE_DB_TO_TALLY", "True").lower() in ("true", "1", "yes"),
        DISABLE_TRANSACTION_SYNC=os.getenv("DISABLE_TRANSACTION_SYNC", "True").lower() in ("true", "1", "yes"),
        USE_ORACLE=os.getenv("USE_ORACLE", "True").lower() in ("true", "1", "yes"),
        USE_SUPABASE=os.getenv("USE_SUPABASE", "False").lower() in ("true", "1", "yes")
    )


