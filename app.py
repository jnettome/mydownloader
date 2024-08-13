from flask import Flask, request, jsonify, send_from_directory, abort
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
DATABASE = 'spotify_downloader.db'
DOWNLOAD_FOLDER = 'downloads'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/add_to_media_queue.json', methods=['POST'])
def add_to_media_queue():
    spotify_url = request.json.get('spotify_url')
    created_at = datetime.now()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO media_queue (spotify_url, parsed_status, created_at)
        VALUES (?, 0, ?)
    ''', (spotify_url, created_at))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Media queue added successfully'}), 201

@app.route('/media_queue.json', methods=['GET'])
def list_media_queues():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM media_queue')
    media_queues = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in media_queues]), 200

@app.route('/media_queue/<int:queue_id>.json', methods=['GET'])
def list_media_queue_items(queue_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM media_queue_items WHERE media_queue_id = ?', (queue_id,))
    media_queue_items = cursor.fetchall()
    conn.close()

    if not media_queue_items:
        return jsonify({'message': 'Media queue not found'}), 404

    return jsonify([dict(row) for row in media_queue_items]), 200

@app.route('/media_queue_item/<int:media_queue_item_id>/reset.json', methods=['POST'])
def reset_media_queue_item(media_queue_item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE media_queue_items SET parsed_status = 0 WHERE id = ?', (media_queue_item_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Media queue item {media_queue_item_id} reset successfully'}), 200

@app.route('/media_queue_item/<int:media_queue_item_id>.json', methods=['DELETE'])
def delete_media_queue_item(media_queue_item_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT download_path FROM media_queue_items WHERE id = ?', (media_queue_item_id,))
    item = cursor.fetchone()

    if item and item['download_path']:
        try:
            os.remove(item['download_path'])
        except FileNotFoundError:
            pass

    cursor.execute('DELETE FROM media_queue_items WHERE id = ?', (media_queue_item_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Media queue item {media_queue_item_id} deleted successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
