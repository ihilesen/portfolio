# transform.py
# Contains transformations: raw -> curated -> optimised
from sqlalchemy import text

def run_transformations(engine):
    with engine.begin() as conn:
        # CURATED: basic transformations (examples)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS curated.listings AS
            SELECT
                l.listing_id,
                NULL::text as name,
                l.host_id,
                l.location AS neighbourhood,
                l.room_type,
                l.price,
                NULL::int as minimum_nights,
                0::int as number_of_reviews,
                NULL::date as last_review,
                0::int as availability_365
            FROM raw.listings l;
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS curated.hosts AS
            SELECT DISTINCT
                h.host_id,
                h.host_name,
                NULL::date as host_since,
                NULL::int as host_listings_count
            FROM raw.hosts h;
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS curated.reviews AS
            SELECT
                r.review_id,
                r.listing_id,
                r.reviewer_name,
                r.comments,
                NULL::date as date
            FROM raw.reviews r;
        """))

        # OPTIMISED: aggregates for BI (example)
        conn.execute(text("DROP TABLE IF EXISTS optimised.listing_metrics;"))
        conn.execute(text("""
            CREATE TABLE optimised.listing_metrics AS
            SELECT
                l.listing_id,
                l.name,
                l.host_id,
                l.neighbourhood,
                l.room_type,
                AVG(l.price) OVER (PARTITION BY l.listing_id) AS avg_price,
                COALESCE(l.number_of_reviews, 0) AS number_of_reviews,
                l.last_review,
                COALESCE(r.total_reviews, 0) AS reviews_count
            FROM curated.listings l
            LEFT JOIN (
                SELECT listing_id, COUNT(*) as total_reviews
                FROM curated.reviews
                GROUP BY listing_id
            ) r ON r.listing_id = l.listing_id;
        """))

        conn.execute(text("DROP TABLE IF EXISTS optimised.host_metrics;"))
        conn.execute(text("""
            CREATE TABLE optimised.host_metrics AS
            SELECT
                h.host_id,
                h.host_name,
                COUNT(DISTINCT l.listing_id) as listing_count,
                AVG(l.price) as avg_price,
                SUM(COALESCE(l.number_of_reviews,0)) as total_listing_reviews
            FROM curated.hosts h
            LEFT JOIN curated.listings l ON l.host_id = h.host_id
            GROUP BY h.host_id, h.host_name;
        """))

    print("Transformations completed.")

