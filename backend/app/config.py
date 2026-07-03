from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://peoplecount:peoplecount@localhost:5432/peoplecount"

    camera_source: str = "0"
    yolo_model: str = "yolov8n.pt"
    yolo_device: str = "cuda:0"
    frame_width: int = 1280
    frame_height: int = 720

    cors_origins: str = "http://localhost:5173"
    position_flush_interval: float = 1.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
