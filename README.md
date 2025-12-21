# Image Resize Service

Simple Flask service that resizes JPG, PNG, and PDF uploads using Pillow (images) and PyMuPDF (PDFs).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

## Usage

```bash
curl -sS -X POST http://localhost:5000/resize \
  -F "file=@/path/to/image.jpg" \
  -F "max_side=800" \
  -o resized.jpg
```

PDF example:

```bash
curl -sS -X POST http://localhost:5000/resize \
  -F "file=@/path/to/document.pdf" \
  -F "max_side=800" \
  -o resized.pdf
```

## Endpoints

- `GET /health` returns service status.
- `POST /resize` accepts a multipart form field named `file` and an optional `max_side` integer.
