import os
import binascii
from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def decode_varint(hex_str):
    data = bytes.fromhex(hex_str)
    result = 0
    shift = 0
    for b in data:
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result

def encode_varint(uid: int) -> str:
    result = bytearray()
    while True:
        to_write = uid & 0x7F
        uid >>= 7
        if uid:
            result.append(to_write | 0x80)
        else:
            result.append(to_write)
            break
    return result.hex().upper()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.endswith(".bytes"):
            return "Invalid file. Please upload a `.bytes` file."

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        with open(filepath, "rb") as f:
            content = f.read()

        pattern = b'\x08\xb5\x01\x18\x01\x38'
        index = content.find(pattern)
        if index == -1:
            return "Pattern not found."

        varint_start = index + len(pattern)
        varint = bytearray()
        for b in content[varint_start:]:
            varint.append(b)
            if b < 0x80:
                break

        varint_hex = binascii.hexlify(varint).upper().decode()
        uid = decode_varint(varint_hex)

        return render_template("index.html", uid=uid, file=filename)

    return render_template("index.html", uid=None)

@app.route("/edit", methods=["POST"])
def edit():
    new_uid = int(request.form["new_uid"])
    filename = request.form["filename"]
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    with open(filepath, "rb") as f:
        content = bytearray(f.read())

    pattern = b'\x08\xb5\x01\x18\x01\x38'
    index = content.find(pattern)
    varint_start = index + len(pattern)

    varint = bytearray()
    for b in content[varint_start:]:
        varint.append(b)
        if b < 0x80:
            break

    old_len = len(varint)
    new_varint = bytes.fromhex(encode_varint(new_uid))
    content[varint_start:varint_start+old_len] = new_varint

    new_path = filepath.replace(".bytes", "_updated.bytes")
    with open(new_path, "wb") as f:
        f.write(content)

    return send_file(new_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
