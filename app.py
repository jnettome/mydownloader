from flask import Flask, request, jsonify, send_from_directory, abort
import psycopg2
from datetime import datetime
import os

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )
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
        VALUES (%s, 0, %s)
    ''', (spotify_url, created_at))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Media queue added successfully'}), 201

@app.route('/media_queue.json', methods=['GET'])
def list_media_queues():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM media_queue ORDER BY parsed_status DESC, created_at ASC')
    media_queues = cursor.fetchall()
    conn.close()

    # Fetch column names
    colnames = [desc[0] for desc in cursor.description]
    return jsonify([dict(zip(colnames, row)) for row in media_queues]), 200

@app.route('/media_queue/<int:queue_id>.json', methods=['GET'])
def list_media_queue_items(queue_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM media_queue_items WHERE media_queue_id = %s ORDER BY parsed_status DESC, created_at ASC', (queue_id,))
    media_queue_items = cursor.fetchall()
    conn.close()

    if not media_queue_items:
        return jsonify({'message': 'Media queue not found'}), 404

    # Fetch column names
    colnames = [desc[0] for desc in cursor.description]
    return jsonify([dict(zip(colnames, row)) for row in media_queue_items]), 200

@app.route('/media_queue_item/<int:media_queue_item_id>/reset.json', methods=['POST'])
def reset_media_queue_item(media_queue_item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE media_queue_items SET parsed_status = 0 WHERE id = %s', (media_queue_item_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Media queue item {media_queue_item_id} reset successfully'}), 200

@app.route('/media_queue_item/<int:media_queue_item_id>.json', methods=['DELETE'])
def delete_media_queue_item(media_queue_item_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT download_path FROM media_queue_items WHERE id = %s', (media_queue_item_id,))
    item = cursor.fetchone()

    if item and item[0]:
        try:
            os.remove(item[0])
        except FileNotFoundError:
            pass

    cursor.execute('DELETE FROM media_queue_items WHERE id = %s', (media_queue_item_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Media queue item {media_queue_item_id} deleted successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
