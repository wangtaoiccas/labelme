# MyProject - AI Polygon Annotation Tool

A lightweight, labelme-like web app with AI-assisted polygon segmentation.

## Features

- Upload and list images
- Canvas-based polygon editing (add, undo, close)
- Shift+Click AI assist via OpenCV flood fill and polygonization
- Save/load labelme-style JSON annotations

## Requirements

- Python 3.9+
- Linux/macOS/Windows

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run

```bash
export PYTHONPATH=$(pwd)
python -m backend.app
```

Open http://localhost:5000 in your browser.

## Usage

- Click the upload button to add images.
- Select an image and click Load, or click from the sidebar list.
- Click to place polygon points. Backspace to undo, Enter to close polygon.
- Shift+Click on the image to AI segment a region near the click; press Enter to add it as a polygon.
- Click Save to write `data/annotations/<image_basename>.json`.

## Notes

- This project is for learning; the AI assist is a simple flood-fill based proposal, not a full deep model.