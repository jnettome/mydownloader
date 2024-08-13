# Media Queue Manager API Documentation

## Base URL

```
http://<your-server-address>:5000
```

## Endpoints

### 1. Add to Media Queue

**Endpoint**: `/add_to_media_queue.json`
**Method**: `POST`
**Description**: Adds a new media queue with a Spotify URL. The `parsed_status` is set to `0` by default.

**Request Body**:
```json
{
  "spotify_url": "https://open.spotify.com/track/example"
}
```

**Response**:
- `201 Created` on success.

**Example**:
```bash
curl -X POST http://<your-server-address>:5000/add_to_media_queue.json \
     -H "Content-Type: application/json" \
     -d '{"spotify_url": "https://open.spotify.com/track/example"}'
```

### 2. List All Media Queues

**Endpoint**: `/media_queue.json`
**Method**: `GET`
**Description**: Retrieves a list of all media queues.

**Response**:
- `200 OK` with a JSON array of media queues.

**Example**:
```bash
curl http://<your-server-address>:5000/media_queue.json
```

### 3. List Media Queue Items

**Endpoint**: `/media_queue/<int:queue_id>.json`
**Method**: `GET`
**Description**: Retrieves all media queue items for a specific media queue.

**Response**:
- `200 OK` with a JSON array of media queue items.
- `404 Not Found` if the media queue does not exist.

**Example**:
```bash
curl http://<your-server-address>:5000/media_queue/1.json
```

### 4. Reset Media Queue Item

**Endpoint**: `/media_queue_item/<int:media_queue_item_id>/reset.json`
**Method**: `POST`
**Description**: Resets the `parsed_status` of a specific media queue item to `0`.

**Response**:
- `200 OK` on success.

**Example**:
```bash
curl -X POST http://<your-server-address>:5000/media_queue_item/1/reset.json
```

### 5. Delete Media Queue Item

**Endpoint**: `/media_queue_item/<int:media_queue_item_id>.json`
**Method**: `DELETE`
**Description**: Deletes a specific media queue item. Attempts to delete the associated file if it exists and then removes the record from the database.

**Response**:
- `200 OK` on success.

**Example**:
```bash
curl -X DELETE http://<your-server-address>:5000/media_queue_item/1.json
```

### 6. List/Download Files from `/downloads/` Folder

**Endpoint**: `/downloads/` or `/downloads/<path>`
**Method**: `GET`
**Description**: Lists the contents of the `/downloads/` folder. If a directory is requested, it lists the contents; if a file is requested, it serves the file.

**Response**:
- `200 OK` with a JSON array of files and directories if a directory is requested.
- `200 OK` serving the file if a file is requested.
- `404 Not Found` if the path does not exist.

**Example**:
```bash
curl http://<your-server-address>:5000/downloads/
```
