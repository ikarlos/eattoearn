from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str
    db_name: str
    #
    merchant_id: str
    salt_key: str
    salt_index: int
    #
    ui_redirect_url: str
    s2s_callback_url: str
    #
    upload_directory: str
    #
    model_config = SettingsConfigDict(env_file=".env")
