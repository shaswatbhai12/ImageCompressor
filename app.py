import os
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from PIL import Image
import uuid

app = Flask(__name__)
app.secret_key = 'shaswat'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['COMPRESSED_FOLDER'] ='compressed'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS ={'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rspllit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    for folder in [app.config['UPLOAD_FOLDER'], app.config['COMPRESSED_FOLDER']]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

def compress_image(input_path, output_path, reduction_percent):
    with Image.Open(input_path) as img:
        
        reduction_factor = (100 - reduction_percent) / 100
        new_width = int(img.width * reduction_factor)
        new_height = int(img.height * reduction_factor)

        # Resize image while maintaining aspect ratio
        Image_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save with high quality but smaller dimmensions
        if img_resized.mode in ('RGBA', 'LA', 'P'):
            img_resized = img_resized.convert('RGB')
        img_resized.save(output_path, 'JPEG', quality=95, optimize=True)

@app.route('/')
def index():
    cleanup_old_files()
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))

    file = request.files['file']
    input_reduction = int(request.form.get('reduction', 30))

    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        # Generate unique filename
        file_id = str(uuid.uuid4())
        original_filename = file.filename 
        file_extension = original_filename.rsplit('.',1)[1].lower()
        
        # Save Original file
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}.{file_extension}")
        file.save(original_path)

        # Compressed image
        compressed_filename = f"{file_id}_compressed.jpg"
        compressed_path = os.path.join(app.config['COMPRESSED_FOLDER'], compressed_filename)

        try:
            compress_image(original_path, compressed_path, input_reduction)

            # Get file sizes
            original_size = os.path.getsize(original_path)
            compressed_size = os.path.getsize(compressed_path)
            actual_reduction = ((original_size - compressed_size) / original_size) * 100

            return render_template('index.html',
                                   success=True,
                                   original_filename=original_filename,
                                   compressed_filename=compressed_filename,
                                   original_size=round(original_size / 1024, 2),
                                   compressed_size=round(compressed_size / 1024, 2),
                                   actual_reduction=round(actual_reduction, 1),
                                   compressed_filename_display=compressed_filename)        
        except Exception as e:
            flash(f'Error compressing image: {str(e)}')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload png, jpg, jpeg, gif, bmp, or WebP Files.')
        return redirect(url_for('index'))
    
@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['COMPRESSED_FOLDER'], filename), as_attachment=True)

@app.route('/preview/<filename>')
def preview_image(filename):
    return send_file(os.path.join(app.config['COMPRESSED_FOLDER'], filename))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['COMPRESSED_FOLDER'], exist_ok=True)
    app.run(debug=True)