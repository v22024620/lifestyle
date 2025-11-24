"""Application configuration settings using environment variables with sane defaults."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LCP_",
        case_sensitive=False,
        env_file=".env",
        populate_by_name=True,
        extra="ignore",
    )

    app_name: str = Field(default="lifestyle-commerce-partner")
    graphdb_endpoint: str = Field(default="http://localhost:7200/repositories/fibo")
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="")
    chroma_path: str = Field(default="./data/chroma")
    llm_endpoint: str = Field(default="https://api.openai.com/v1")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    cache_ttl_seconds: int = Field(default=300)


def get_settings() -> Settings:
    """Return singleton settings instance."""
    return Settings()