import sqlite3
import psycopg2
from psycopg2 import sql
import os
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
print(os.getenv('POSTGRES_DB'))
# Database connection
def get_postgres_connection():
    return psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )

def get_sqlite_connection():
    return sqlite3.connect('spotify_downloader.db')

# Copy data from SQLite to PostgreSQL
def convert_data():
    try:
        sqlite_conn = get_sqlite_connection()
        sqlite_cursor = sqlite_conn.cursor()

        postgres_conn = get_postgres_connection()
        postgres_cursor = postgres_conn.cursor()

        # Transfer media_queue table
        sqlite_cursor.execute("SELECT * FROM media_queue")
        media_queue_data = sqlite_cursor.fetchall()

        for row in media_queue_data:
            postgres_cursor.execute("""
                INSERT INTO media_queue (id, spotify_url, parsed_status, created_at, updated_at, media_type, download_started_at, download_finished_at, download_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)
        
        postgres_conn.commit()
        logging.info(f"Transferred {len(media_queue_data)} rows from media_queue")

        # Transfer media_queue_items table
        sqlite_cursor.execute("SELECT * FROM media_queue_items")
        media_queue_items_data = sqlite_cursor.fetchall()

        for row in media_queue_items_data:
            postgres_cursor.execute("""
                INSERT INTO media_queue_items (id, media_queue_id, media_url, parsed_status, created_at, updated_at, download_started_at, download_finished_at, download_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, row)

        postgres_conn.commit()
        logging.info(f"Transferred {len(media_queue_items_data)} rows from media_queue_items")

        sqlite_conn.close()
        postgres_conn.close()
        logging.info("Data transfer completed successfully.")
    except Exception as e:
        logging.error(f"Error during data conversion: {str(e)}")
        logging.debug(traceback.format_exc())

if __name__ == "__main__":
    convert_data()

