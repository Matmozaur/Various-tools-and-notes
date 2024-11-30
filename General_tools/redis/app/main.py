from flask import Flask, request, jsonify
import redis
import os

# Initialize Flask app
app = Flask(__name__)

# Get Redis connection details from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Connect to Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

@app.route('/set', methods=['POST'])
def set_key():
    """
    Set a key-value pair in Redis.
    Expects JSON body: {"key": "key_name", "value": "value_data"}
    """
    data = request.get_json()
    if not data or 'key' not in data or 'value' not in data:
        return jsonify({"error": "Invalid request. 'key' and 'value' are required"}), 400

    key = data['key']
    value = data['value']

    redis_client.set(key, value)
    return jsonify({"message": f"Key '{key}' set successfully."}), 200

@app.route('/get/<key>', methods=['GET'])
def get_key(key):
    """
    Retrieve the value of a key from Redis.
    """
    value = redis_client.get(key)
    if value is None:
        return jsonify({"error": f"Key '{key}' not found."}), 404

    return jsonify({"key": key, "value": value.decode()}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
