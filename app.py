from flask import Flask, render_template, request, send_file
import subprocess
import os
import uuid
from PIL import Image
import fitz  # PyMuPDF

app = Flask(__name__)
UPLOAD = "uploads"
OUTPUT = "output"
os.makedirs(UPLOAD, exist_ok=True)
os.makedirs(OUTPUT, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

def run_ghostscript(input_path, output_path, level):
    subprocess.run([
        "gswin64c" if os.name == "nt" else "gs",
        "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={level}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={output_path}", input_path
    ], check=True)

@app.route("/compress", methods=["POST"])
def compress():
    file = request.files.getlist("file")[0]
    level = request.form.get("level", "/screen")
    size_kb = request.form.get("size_kb", type=int)
    file_id = uuid.uuid4().hex
    in_path = os.path.join(UPLOAD, file_id + "_" + file.filename)
    out_path = os.path.join(OUTPUT, file_id + "_compressed.pdf")
    file.save(in_path)
    run_ghostscript(in_path, out_path, level)
    return send_file(out_path, as_attachment=True, download_name=file.filename)

@app.route("/pdf-to-jpeg", methods=["POST"])
def pdf_to_jpeg():
    file = request.files.getlist("file")[0]
    file_id = uuid.uuid4().hex
    in_path = os.path.join(UPLOAD, file_id + "_" + file.filename)
    file.save(in_path)
    doc = fitz.open(in_path)
    jpg_paths = []
    for i in range(len(doc)):
        pix = doc[i].get_pixmap()
        jpg_file = os.path.join(OUTPUT, f"{file_id}_page_{i+1}.jpg")
        pix.save(jpg_file)
        jpg_paths.append(jpg_file)
    # Return first page only for now
    return send_file(jpg_paths[0], as_attachment=True, download_name=os.path.splitext(file.filename)[0] + ".jpg")

@app.route("/jpeg-to-pdf", methods=["POST"])
def jpeg_to_pdf():
    file = request.files.getlist("file")[0]
    file_id = uuid.uuid4().hex
    in_path = os.path.join(UPLOAD, file_id + "_" + file.filename)
    out_pdf = os.path.join(OUTPUT, file_id + "_converted.pdf")
    img = Image.open(file.stream).convert("RGB")
    img.save(out_pdf, "PDF", resolution=100.0)
    return send_file(out_pdf, as_attachment=True, download_name=os.path.splitext(file.filename)[0] + ".pdf")

if __name__ == "__main__":
    app.run(debug=True)
