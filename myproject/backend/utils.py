from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}


def allowed_file(filename: str) -> bool:
	return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def list_images(images_dir: str) -> List[str]:
	if not os.path.exists(images_dir):
		return []
	files = []
	for name in os.listdir(images_dir):
		path = os.path.join(images_dir, name)
		if os.path.isfile(path) and allowed_file(name):
			files.append(name)
	files.sort()
	return files


def image_path(images_dir: str, filename: str) -> str:
	return os.path.join(images_dir, filename)


def annotation_path(annotations_dir: str, basename: str) -> str:
	# Ensure .json suffix is present, strip if provided with extension
	if basename.endswith(".json"):
		basename = basename[:-5]
	return os.path.join(annotations_dir, f"{basename}.json")


def load_annotation(path: str) -> Optional[Dict[str, Any]]:
	if not os.path.exists(path):
		return None
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def save_annotation(path: str, data: Dict[str, Any]) -> None:
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)