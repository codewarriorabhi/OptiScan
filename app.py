import os
import uuid
import logging
import shutil
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from werkzeug.utils import secure_filename

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/webp', 'image/grip', 'image/bmp'}
MAX_FILE_SIZE = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['MAX_REQUEST_TIME'] = 300

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optiscan.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

rate_limit_storage = {}

def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.headers.get('X-Real-IP', request.remote_addr))

def rate_limit(max_requests=10, window=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = get_client_ip()
            now = datetime.now()
            
            if client_ip not in rate_limit_storage:
                rate_limit_storage[client_ip] = []
            
            rate_limit_storage[client_ip] = [
                req_time for req_time in rate_limit_storage[client_ip]
                if now - req_time < timedelta(seconds=window)
            ]
            
            if len(rate_limit_storage[client_ip]) >= max_requests:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            
            rate_limit_storage[client_ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_type(file):
    if not file:
        return False
    content_type = file.content_type
    if content_type in ALLOWED_MIME_TYPES:
        return True
    return allowed_file(file.filename)

def cleanup_old_files():
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        return
    
    now = datetime.now()
    for filename in os.listdir(upload_folder):
        filepath = os.path.join(upload_folder, filename)
        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if now - file_time > timedelta(hours=1):
                try:
                    os.remove(filepath)
                    logger.info(f"Cleaned up old file: {filename}")
                except Exception as e:
                    logger.error(f"Error cleaning up {filename}: {e}")

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

def perform_ocr(filepath):
    try:
        from PIL import Image
        import pytesseract
        
        pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
        
        img = Image.open(filepath)
        
        extracted_text = pytesseract.image_to_string(img, lang='eng')
        
        return extracted_text.strip()
        
    except ImportError as e:
        logger.error(f"Missing OCR dependency: {e}")
        return None
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def extract_text():
    if 'file' not in request.files:
        logger.warning("No file provided in request")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        logger.warning("Empty filename provided")
        return jsonify({'error': 'No file selected'}), 400
    
    if not validate_file_type(file):
        logger.warning(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, WEBP, GIF, BMP'}), 400
    
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes")
        return jsonify({'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
    
    unique_filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    temp_filepath = filepath
    
    @after_this_request
    def cleanup(request):
        try:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
                logger.info(f"Cleaned up temp file: {unique_filename}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        return request
    
    try:
        file.save(filepath)
        logger.info(f"File saved: {unique_filename}")
        
        result = perform_ocr(filepath)
        
        if result is None:
            logger.error("OCR processing failed")
            return jsonify({'error': 'OCR processing failed. Please try again.'}), 500
        
        if not result:
            logger.warning("No text extracted from image")
            return jsonify({'text': '', 'warning': 'No text detected in the image'}), 200
        
        logger.info(f"OCR successful for: {unique_filename}")
        return jsonify({'text': result}), 200
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/download', methods=['POST'])
def download_text():
    data = request.get_json()
    text = data.get('text', '')
    filename = data.get('filename', 'extracted-text.txt')
    
    if not text:
        return jsonify({'error': 'No text to download'}), 400
    
    safe_filename = secure_filename(filename)
    if not safe_filename.endswith('.txt'):
        safe_filename += '.txt'
    
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    @after_this_request
    def cleanup(request):
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
        return request
    
    return send_file(temp_path, as_attachment=True, download_name=safe_filename)

if __name__ == '__main__':
    logger.info("OptiScan application starting...")
    app.run(host='0.0.0.0', port=5000, debug=False)