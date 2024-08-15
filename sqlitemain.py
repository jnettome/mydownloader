import sqlite3
import os
import time
from datetime import datetime
import logging
from spotdl import Spotdl
import traceback

from dotenv import load_dotenv
load_dotenv()

# Spotify credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

youtube_cookies_path =  os.path.join(os.getcwd(), 'ytcookies.txt') # 'ytcookies.txt'

# Initialize Spotdl only once
spotdl = Spotdl(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database setup
def setup_database():
    try:
        conn = sqlite3.connect('spotify_downloader.db')
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS media_queue
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      spotify_url TEXT,
                      parsed_status INTEGER,
                      created_at TIMESTAMP,
                      updated_at TIMESTAMP,
                      media_type INTEGER,
                      download_started_at TIMESTAMP,
                      download_finished_at TIMESTAMP,
                      download_path TEXT)''')

        c.execute('''CREATE TABLE IF NOT EXISTS media_queue_items
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      media_queue_id INTEGER,
                      media_url TEXT,
                      parsed_status INTEGER,
                      created_at TIMESTAMP,
                      updated_at TIMESTAMP,
                      download_started_at TIMESTAMP,
                      download_finished_at TIMESTAMP,
                      download_path TEXT,
                      FOREIGN KEY (media_queue_id) REFERENCES media_queue(id))''')

        conn.commit()
        conn.close()
        logging.info("Database setup completed successfully.")
    except Exception as e:
        logging.error(f"Error setting up database: {str(e)}")
        logging.debug(traceback.format_exc())

# Media Queue processing
def add_to_media_queue(spotify_url):
    try:
        conn = sqlite3.connect('spotify_downloader.db')
        c = conn.cursor()

        now = datetime.now()
        c.execute("INSERT INTO media_queue (spotify_url, parsed_status, created_at, updated_at) VALUES (?, 0, ?, ?)",
                  (spotify_url, now, now))

        queue_id = c.lastrowid
        conn.commit()
        conn.close()

        logging.info(f"Added new item to media queue: ID {queue_id}, URL {spotify_url}")
        return queue_id
    except Exception as e:
        logging.error(f"Error adding to media queue: {str(e)}")
        logging.debug(traceback.format_exc())
        return None
def process_media_queue():
    try:
        conn = sqlite3.connect('spotify_downloader.db')
        c = conn.cursor()

        # Select unprocessed items and lock them for this process by setting parsed_status to 2 (in progress)
        c.execute("SELECT id, spotify_url FROM media_queue WHERE parsed_status = 0 LIMIT 1")
        item = c.fetchone()

        if item:
            queue_id, spotify_url = item
            logging.info(f"Processing media queue item: ID {queue_id}, URL {spotify_url}")

            # Mark this item as in progress
            c.execute("UPDATE media_queue SET parsed_status = 2, updated_at = ? WHERE id = ?",
                      (datetime.now(), queue_id))
            conn.commit()

            media_type = detect_media_type(spotify_url)

            if media_type == 0:  # playlist
                process_playlist(queue_id, spotify_url)
            elif media_type == 1:  # album
                process_album(queue_id, spotify_url)
            elif media_type == 2:  # single
                process_single(queue_id, spotify_url)

            # Mark this item as processed
            c.execute("UPDATE media_queue SET parsed_status = 1, media_type = ?, updated_at = ? WHERE id = ?",
                      (media_type, datetime.now(), queue_id))
            conn.commit()

            time.sleep(2)
        else:
            logging.info("No unprocessed items found in the media queue.")

        conn.close()
    except Exception as e:
        logging.error(f"Error processing media queue: {str(e)}")
        logging.debug(traceback.format_exc())

def detect_media_type(spotify_url):
    if 'playlist' in spotify_url:
        return 0
    elif 'album' in spotify_url:
        return 1
    else:
        return 2

def process_playlist(queue_id, spotify_url):
    try:
        songs = spotdl.search([spotify_url])
        logging.info(f"Processed playlist: ID {queue_id}, found {len(songs)} songs")
        add_to_media_queue_items(queue_id, songs)
    except Exception as e:
        logging.error(f"Error processing playlist: ID {queue_id}, URL {spotify_url}, Error: {str(e)}")
        logging.debug(traceback.format_exc())

def process_album(queue_id, spotify_url):
    try:
        songs = spotdl.search([spotify_url])
        logging.info(f"Processed album: ID {queue_id}, found {len(songs)} songs")
        add_to_media_queue_items(queue_id, songs)
    except Exception as e:
        logging.error(f"Error processing album: ID {queue_id}, URL {spotify_url}, Error: {str(e)}")
        logging.debug(traceback.format_exc())

def process_single(queue_id, spotify_url):
    try:
        songs = spotdl.search([spotify_url])
        logging.info(f"Processed single: ID {queue_id}, found {len(songs)} songs")
        add_to_media_queue_items(queue_id, songs)
    except Exception as e:
        logging.error(f"Error processing single: ID {queue_id}, URL {spotify_url}, Error: {str(e)}")
        logging.debug(traceback.format_exc())

def add_to_media_queue_items(queue_id, songs):
    try:
        conn = sqlite3.connect('spotify_downloader.db')
        c = conn.cursor()

        now = datetime.now()
        for song in songs:
            c.execute("INSERT INTO media_queue_items (media_queue_id, media_url, parsed_status, created_at, updated_at) VALUES (?, ?, 0, ?, ?)",
                      (queue_id, song.url, now, now))

        conn.commit()
        conn.close()
        logging.info(f"Added {len(songs)} items to media queue items for queue ID {queue_id}")
    except Exception as e:
        logging.error(f"Error adding to media queue items: Queue ID {queue_id}, Error: {str(e)}")
        logging.debug(traceback.format_exc())

# Download job
def download_job():
    try:
        conn = sqlite3.connect('spotify_downloader.db')
        c = conn.cursor()

        c.execute("SELECT id, media_queue_id, media_url FROM media_queue_items WHERE parsed_status = 0")
        items_to_download = c.fetchall()

        for item in items_to_download:
            item_id, queue_id, media_url = item

            c.execute("SELECT download_path FROM media_queue WHERE id = ?", (queue_id,))
            queue_download_path = c.fetchone()[0]

            if not queue_download_path:
                queue_download_path = create_download_folder(queue_id)
                c.execute("UPDATE media_queue SET download_path = ? WHERE id = ?", (queue_download_path, queue_id))

            c.execute("UPDATE media_queue_items SET parsed_status = 1, download_started_at = ?, updated_at = ? WHERE id = ?",
                      (datetime.now(), datetime.now(), item_id))
            conn.commit()

            try:
                # os.chdir(queue_queue_download_path)

                # check if youtube cookies
                if os.path.exists(youtube_cookies_path):
                    os.system(f"spotdl download {media_url} --format mp3 --output {queue_download_path} --cookie-file {youtube_cookies_path}")
                else:
                    os.system(f"spotdl download {media_url} --format mp3 --output {queue_download_path}")


                #     os.system(f"spotdl download 'https://open.spotify.com/album/{id}'")  # Download the entire album
                #     os.system(f"spotdl download 'https://open.spotify.com/track/{id}'")  # Download specific track
                # Move back to the Music directory after each iteration
                # os.chdir(music_directory)

                c.execute("UPDATE media_queue_items SET parsed_status = 3, download_finished_at = ?, updated_at = ?, download_path = ? WHERE id = ?",
                          (datetime.now(), datetime.now(), queue_download_path, item_id))
                conn.commit()

                logging.info(f"Successfully downloaded: Item ID {item_id}, URL {media_url}")

                check_queue_status(queue_id)
            except Exception as e:
                logging.error(f"Error downloading {media_url}: {str(e)}")
                logging.debug(traceback.format_exc())
                c.execute("UPDATE media_queue_items SET parsed_status = 9, updated_at = ? WHERE id = ?",
                          (datetime.now(), item_id))
                conn.commit()

        conn.close()
    except Exception as e:
        logging.error(f"Error in download job: {str(e)}")
        logging.debug(traceback.format_exc())

def create_download_folder(queue_id):
    try:
        folder_path = os.path.join("downloads", f"queue_{queue_id}")
        os.makedirs(folder_path, exist_ok=True)
        logging.info(f"Created download folder: {folder_path}")
        return folder_path
    except Exception as e:
        logging.error(f"Error creating download folder for queue ID {queue_id}: {str(e)}")
        logging.debug(traceback.format_exc())
        return None

def check_queue_status(queue_id):
    try:
        conn = sqlite3.connect('spotify_downloader.db')
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM media_queue_items WHERE media_queue_id = ? AND parsed_status != 3", (queue_id,))
        unfinished_items = c.fetchone()[0]

        if unfinished_items == 0:
            c.execute("UPDATE media_queue SET parsed_status = 3, download_finished_at = ?, updated_at = ? WHERE id = ?",
                      (datetime.now(), datetime.now(), queue_id))
            conn.commit()
            logging.info(f"All items in queue ID {queue_id} have been downloaded.")

            # move the downloaded folder to mounted directory
            os.system(f"mv downloads/queue_{queue_id} /media/")

        conn.close()
    except Exception as e:
        logging.error(f"Error checking queue status for queue ID {queue_id}: {str(e)}")
        logging.debug(traceback.format_exc())

# Main application loop
def main():
    logging.info("Starting Spotify Media Downloader")
    setup_database()

    while True:
        try:
            logging.info("Processing media queue...")
            process_media_queue()
            logging.info("Running download job...")
            download_job()
            logging.info("Waiting for 15 seconds before next iteration...")
            time.sleep(15)  # Wait for 60 seconds before the next iteration
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            logging.debug(traceback.format_exc())
            logging.info("Waiting for 5 seconds before retrying...")
            time.sleep(5)

if __name__ == "__main__":
    main()
