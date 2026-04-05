# OptiScan

A modern web application for extracting text from images using OCR (Optical Character Recognition) technology.

## Features

- Drag & drop image upload
- Support for multiple image formats (JPG, PNG, JPEG, WEBP, GIF, BMP)
- Secure file handling with validation
- Rate limiting to prevent abuse
- Real-time text extraction statistics
- Copy to clipboard & download functionality
- Responsive design
- Automatic file cleanup

## Prerequisites

- Python 3.8+
- Tesseract OCR installed on system

### Install Tesseract

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download and install from https://github.com/UB-Mannheim/tesseract/wiki

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd OptiScan
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open browser at `http://localhost:5000`

## Docker Deployment

```bash
docker-compose up --build
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `FLASK_ENV` - Development or production
- `SECRET_KEY` - Flask secret key
- `MAX_FILE_SIZE` - Maximum upload size in bytes
- `RATE_LIMIT_MAX` - Maximum requests per window
- `RATE_LIMIT_WINDOW` - Time window in seconds

## API Endpoints

- `GET /` - Home page
- `POST /extract` - Extract text from image
- `POST /download` - Download extracted text

## License

MIT
