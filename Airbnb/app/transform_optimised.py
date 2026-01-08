import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def run_optimised():
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
            DROP TABLE IF EXISTS optimised.host_metrics;
            CREATE TABLE optimised.host_metrics AS
            SELECT
                l.host_id,
                COUNT(*) AS total_listings
            FROM curated.dim_listings l
            GROUP BY l.host_id;
        """))

    print("✅ Optimised layer created")
