import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def run_curated():
    load_dotenv()

    db_url = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/"
        f"{os.getenv('POSTGRES_DB')}"
    )

    engine = create_engine(db_url)

    with engine.begin() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS curated.dim_hosts;
            CREATE TABLE curated.dim_hosts AS
            SELECT
                id AS host_id,
                name AS host_name,
                is_superhost,
                created_at::date AS host_since
            FROM raw.hosts;
        """))

    print("✅ Curated layer created")
