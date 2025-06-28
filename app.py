from flask import Flask, render_template, request, send_file, make_response
import subprocess, os, uuid, io, zipfile
from PIL import Image
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF

app = Flask(__name__)
BASE = os.path.dirname(__file__)
UPLOAD = os.path.join(BASE, "uploads")
OUT = os.path.join(BASE, "output")
os.makedirs(UPLOAD, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/compress", methods=["POST"])
def compress():
    f = request.files["pdf_file"]
    lvl = request.form.get("level", "/screen")
    kb = int(request.form.get("size_kb", 500))
    in_path = os.path.join(UPLOAD, secure_filename(f.filename))
    out_path = os.path.join(OUT, f"{uuid.uuid4().hex}_comp.pdf")
    f.save(in_path)
    subprocess.run([
        "gswin64c", "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4", f"-dPDFSETTINGS={lvl}",
        "-dNOPAUSE","-dQUIET","-dBATCH",
        f"-sOutputFile={out_path}", in_path
    ], check=True)
    return send_file(out_path, as_attachment=True,
                     download_name="compressed.pdf")

@app.route("/img-to-pdf", methods=["POST"])
def img_to_pdf():
    imgs = request.files.getlist("images[]")
    pil_imgs = [Image.open(i.stream).convert("RGB") for i in imgs]
    out_path = os.path.join(OUT, f"{uuid.uuid4().hex}_images.pdf")
    pil_imgs[0].save(out_path, save_all=True, append_images=pil_imgs[1:])
    return send_file(out_path, as_attachment=True,
                     download_name="from_images.pdf")

@app.route("/pdf-to-img", methods=["POST"])
def pdf_to_img():
    f = request.files["pdf_for_jpg"]
    doc = fitz.open(stream=f.read(), filetype="pdf")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i, pg in enumerate(doc, start=1):
            pix = pg.get_pixmap(dpi=150)
            zf.writestr(f"page_{i}.jpg", pix.tobytes("jpg"))
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers["Content-Type"] = "application/zip"
    resp.headers["Content-Disposition"] = 'attachment; filename=pdf_pages.zip'
    return resp

if __name__ == "__main__":
    app.run(debug=True)
