import logging
from flask import Flask, jsonify
from .telegram import tg_bp
from .heygen import heygen_bp

app = Flask(__name__)

# Включаем Flask blueprints
app.register_blueprint(tg_bp)
app.register_blueprint(heygen_bp)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'ok': True}), 200

# Flask экспортирует 'app' для WSGI

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=5000)


