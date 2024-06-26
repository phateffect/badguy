from psycopg import connect
from psycopg.rows import dict_row, class_row

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from .schemas import VenueResult


class Database(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BGUY_",
        extra="ignore"
    )

    dsn: PostgresDsn

    def connect(self):
        return connect(str(self.dsn))

    def upsert_ground_hours(self, conn, ground_hours):
        stmt = """
          INSERT INTO ground_hours (
            date, hour,
            venue_id, ground_id, ground_name,
            available, price
          ) VALUES (
            %(date)s, %(hour)s,
            %(venue_id)s, %(ground_id)s, %(ground_name)s,
            %(available)s, %(price)s
          ) ON CONFLICT (date, hour, venue_id, ground_id) DO UPDATE
          SET available = EXCLUDED.available
        """
        c_stmt = """
          UPDATE ground_hours
          SET available = FALSE
          WHERE 1=1
            AND date < CURRENT_DATE
            OR (date = CURRENT_DATE AND hour <= EXTRACT(hour from now()))
        """
        with conn.cursor() as cur:
            cur.executemany(stmt, ground_hours)
            cur.execute(c_stmt)

    def update_notification(self, conn, key, content):
        stmt = """
          INSERT INTO notifications (
            id, content
          ) VALUES (
            %(id)s, %(content)s
          ) ON CONFLICT (id) DO UPDATE
          SET sent = TRUE
          RETURNING sent
        """
        result = conn.execute(stmt, {"id": key, "content": content})
        return result.fetchone()[0]

    def find_venue(self, conn, hours):
        stmt = """
          WITH available_hours AS (
            SELECT
              venue_id, date,
              ARRAY_AGG(DISTINCT hour ORDER BY hour ASC) AS hours,
              ARRAY_AGG(id) AS ids
            FROM ground_hours
            WHERE available AND hour = ANY(%(hours)s)
            GROUP BY venue_id, date
          )
          SELECT
            MD5(STRING_AGG(id::TEXT, '|')) AS key,
            venue_id, date, ARRAY_AGG(DISTINCT hour ORDER BY hour ASC) AS hours,
            ARRAY_AGG(
              JSON_BUILD_OBJECT('hour', hour, 'name', ground_name)
              ORDER BY hour ASC, ground_name ASC
            ) AS grounds
          FROM ground_hours
          WHERE id IN (
            SELECT
              UNNEST(ids) AS id
            FROM available_hours
            WHERE hours @> %(hours)s
          )
          GROUP BY venue_id, date
          ORDER BY venue_id, date ASC
        """
        with conn.cursor(row_factory=class_row(VenueResult)) as cur:
            cur.execute(stmt, {"hours": hours})
            return cur.fetchall()
