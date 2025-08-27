from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Tuple, Optional

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from .ai import segment_polygon
from .utils import (
	allowed_file,
	list_images,
	image_path,
	annotation_path,
	load_annotation,
	save_annotation,
)


# Resolve directories
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
ANNOTATIONS_DIR = os.path.join(DATA_DIR, "annotations")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(ANNOTATIONS_DIR, exist_ok=True)

app = Flask(
	__name__,
	static_folder=FRONTEND_DIR,
	static_url_path="",
)


@app.get("/api/health")
def health() -> Any:
	return jsonify({"status": "ok"})


@app.get("/api/images")
def get_images() -> Any:
	images = list_images(IMAGES_DIR)
	return jsonify({"images": images})


@app.post("/api/upload")
def upload_image() -> Any:
	if "file" not in request.files:
		return jsonify({"error": "No file part"}), 400
	file = request.files["file"]
	if file.filename == "":
		return jsonify({"error": "No selected file"}), 400
	if not allowed_file(file.filename):
		return jsonify({"error": "Unsupported file type"}), 400
	filename = secure_filename(file.filename)
	save_path = os.path.join(IMAGES_DIR, filename)
	file.save(save_path)
	return jsonify({"ok": True, "filename": filename})


@app.get("/api/image/<path:filename>")
def get_image(filename: str) -> Any:
	return send_from_directory(IMAGES_DIR, filename, as_attachment=False)


@app.get("/api/annotations/<path:basename>.json")
def get_annotation(basename: str) -> Any:
	ann_path = annotation_path(ANNOTATIONS_DIR, basename)
	data = load_annotation(ann_path)
	if data is None:
		return jsonify({"shapes": []}), 200
	return jsonify(data)


@app.post("/api/annotations/<path:basename>.json")
def post_annotation(basename: str) -> Any:
	try:
		payload = request.get_json(force=True)
	except Exception:
		return jsonify({"error": "Invalid JSON"}), 400
	ann_path = annotation_path(ANNOTATIONS_DIR, basename)
	save_annotation(ann_path, payload)
	return jsonify({"ok": True})


@app.post("/api/ai/segment")
def ai_segment() -> Any:
	try:
		payload = request.get_json(force=True)
		image_filename = payload.get("image")
		x = int(payload.get("x"))
		y = int(payload.get("y"))
		tolerance = int(payload.get("tolerance", 15))
	except Exception:
		return jsonify({"error": "Invalid payload"}), 400

	if not image_filename:
		return jsonify({"error": "Missing image filename"}), 400

	img_path = image_path(IMAGES_DIR, image_filename)
	if not os.path.exists(img_path):
		return jsonify({"error": "Image not found"}), 404

	points = segment_polygon(img_path, (x, y), tolerance=tolerance)
	return jsonify({"points": points})


# Frontend routes
@app.get("/")
def index_html() -> Any:
	return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:path>")
def serve_frontend(path: str) -> Any:
	# Serve static assets from frontend directory; fallback to index.html
	full_path = os.path.join(FRONTEND_DIR, path)
	if os.path.exists(full_path) and os.path.isfile(full_path):
		return send_from_directory(FRONTEND_DIR, path)
	return send_from_directory(FRONTEND_DIR, "index.html")


if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(host="0.0.0.0", port=port, debug=True)