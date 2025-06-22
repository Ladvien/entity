from sqlalchemy import create_engine, text
from src.db.models import Base
from src.service.config import load_config


def create_schema_sync():
    config = load_config("config.yaml")

    db = config.database

    # Create a sync SQLAlchemy URL by replacing asyncpg with psycopg
    sync_url = f"postgresql+psycopg://{db.username}:{db.password}@{db.host}:{db.port}/{db.name}"

    engine = create_engine(sync_url, echo=True)

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(engine)
    print("Schema and extension created.")


if __name__ == "__main__":
    create_schema_sync()
