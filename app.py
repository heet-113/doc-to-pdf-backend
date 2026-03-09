import os
import subprocess
import tempfile
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import shutil

app = Flask(__name__)
CORS(app)  # Allow the static frontend to call this API from any origin

ALLOWED_EXTENSIONS = {'docx', 'csv'}

if shutil.which("soffice") is None:
    raise RuntimeError("LibreOffice is not installed in the environment.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file type. Only .docx and .csv are supported.'}), 400

    filename = file.filename
    base_name = filename.rsplit('.', 1)[0]
    ext = filename.rsplit('.', 1)[1].lower()

    # Use a temporary directory so files are automatically cleaned up
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, filename)
        file.save(input_path)

        # LibreOffice converts both .docx and .csv to PDF with perfect fidelity.
        # --headless: no GUI
        # --convert-to pdf: target format
        # --outdir: where the PDF will be written
        result = subprocess.run(
        [
            'soffice',
            '--headless',
            '--norestore',
            '--nodefault',
            '--nolockcheck',
            '--nofirststartwizard',
            '--convert-to', 'pdf',
            '--outdir', tmpdir,
            input_path
        ],
            env={**os.environ, "HOME": "/tmp"},
            capture_output=True,
            text=True,
            timeout=120
        )

        pdf_path = os.path.join(tmpdir, base_name + '.pdf')

        if not os.path.exists(pdf_path):
            error_detail = result.stderr or result.stdout or 'Unknown error'
            return jsonify({'error': 'Conversion failed', 'detail': error_detail}), 500

        # Read the file into memory before temp dir is deleted
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

    # Send as a downloadable PDF attachment
    import io
    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=base_name + '.pdf',
        mimetype='application/pdf'
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
