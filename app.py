from flask import Flask, render_template, request, send_file
import os
import uuid
import subprocess
import fitz  # PyMuPDF
from PIL import Image

app = Flask(__name__)

# Folder paths
UPLOAD_FOLDER = "uploads"
COMPRESSED_FOLDER = "compressed"
PDF2JPEG_FOLDER = "pdf2jpeg"
JPEG2PDF_FOLDER = "jpeg2pdf"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)
os.makedirs(PDF2JPEG_FOLDER, exist_ok=True)
os.makedirs(JPEG2PDF_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/compress", methods=["POST"])
def compress_pdf():
    file = request.files.get("file")
    level = request.form.get("level", "/screen")
    size_kb = int(request.form.get("size_kb", 500))

    if not file:
        return "No PDF uploaded", 400

    file_id = uuid.uuid4().hex
    input_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_input.pdf")
    output_path = os.path.join(COMPRESSED_FOLDER, f"{file_id}_compressed.pdf")
    file.save(input_path)

    # Ghostscript command
    gs_command = [
        "gswin64c",  # use 'gs' if you're on Linux or macOS
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={level}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ]

    try:
        subprocess.run(gs_command, check=True)
        return send_file(output_path, as_attachment=True, download_name=file.filename)
    except subprocess.CalledProcessError:
        return "Compression failed", 500

@app.route("/pdf-to-jpeg", methods=["POST"])
def pdf_to_jpeg():
    file = request.files.get("file")
    if not file or not file.filename.endswith(".pdf"):
        return "No PDF uploaded", 400

    file_id = uuid.uuid4().hex
    input_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.pdf")
    output_path = os.path.join(PDF2JPEG_FOLDER, f"{file_id}_output.pdf")
    file.save(input_path)

    images = []
    try:
        pdf = fitz.open(input_path)
        for page in pdf:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img.convert("RGB"))
        pdf.close()
        if images:
            images[0].save(output_path, save_all=True, append_images=images[1:])
            return send_file(output_path, as_attachment=True, download_name="converted.pdf")
        else:
            return "No images found in PDF", 500
    except Exception as e:
        return f"Error converting PDF to images: {str(e)}", 500

@app.route("/jpeg-to-pdf", methods=["POST"])
def jpeg_to_pdf():
    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".jpg"):
        return "No JPG uploaded", 400

    file_id = uuid.uuid4().hex
    output_path = os.path.join(JPEG2PDF_FOLDER, f"{file_id}_output.pdf")

    try:
        image = Image.open(file.stream).convert("RGB")
        image.save(output_path, "PDF", resolution=100.0)
        return send_file(output_path, as_attachment=True, download_name="converted.pdf")
    except Exception as e:
        return f"Error converting JPG to PDF: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
