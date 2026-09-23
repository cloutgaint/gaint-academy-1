from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name:str="GAINT Academy"
    app_env:str="development"
    database_url:str="postgresql+psycopg://gaint:change-me-local@postgres:5432/gaint_academy"
    redis_url:str="redis://redis:6379/0"
    seed_admin_email:str="gaintclout@gmail.com"
    seed_admin_password:str|None=None
    session_hours:int=8
    cookie_secure:bool=False
    cors_origins:list[str]=["http://localhost:3000"]
    payment_webhook_secret:str|None=None
    smtp_host:str|None=None
    smtp_port:int=587
    smtp_username:str|None=None
    smtp_password:str|None=None
    smtp_from_email:str|None=None
    smtp_use_tls:bool=True
    password_reset_otp_minutes:int=10
    login_max_attempts:int=5
    login_window_seconds:int=900
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")
settings=Settings()
