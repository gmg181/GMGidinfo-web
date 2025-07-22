import os
import binascii
import tempfile
from flask import Flask, request, render_template, send_file

app = Flask(__name__)
pattern = b'\x08\xb5\x01\x18\x01\x38'

# Varint decoding
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

# Varint encoding
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
        if "file" not in request.files:
            return "No file uploaded.", 400
        file = request.files["file"]
        if not file.filename.endswith(".bytes"):
            return "Invalid file type. Only .bytes allowed.", 400

        file_path = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(file_path)

        with open(file_path, "rb") as f:
            content = f.read()

        index = content.find(pattern)
        if index == -1:
            return "Pattern not found in file.", 400

        varint_start = index + len(pattern)
        varint = bytearray()
        for b in content[varint_start:]:
            varint.append(b)
            if b < 0x80:
                break

        varint_hex = binascii.hexlify(varint).upper().decode()
        uid = decode_varint(varint_hex)

        return render_template("index.html", uid=uid, filename=file.filename)

    return render_template("index.html", uid=None)

@app.route("/edit", methods=["POST"])
def edit():
    new_uid = int(request.form["new_uid"])
    filename = request.form["filename"]
    file_path = os.path.join(tempfile.gettempdir(), filename)

    with open(file_path, "rb") as f:
        content = bytearray(f.read())

    index = content.find(pattern)
    if index == -1:
        return "Pattern not found.", 400

    varint_start = index + len(pattern)
    old_varint = bytearray()
    for b in content[varint_start:]:
        old_varint.append(b)
        if b < 0x80:
            break

    old_len = len(old_varint)
    new_varint = bytes.fromhex(encode_varint(new_uid))
    content[varint_start:varint_start+old_len] = new_varint

    new_path = file_path.replace(".bytes", "_updated.bytes")
    with open(new_path, "wb") as f:
        f.write(content)

    return send_file(new_path, as_attachment=True, download_name=os.path.basename(new_path))

if __name__ == "__main__":
    app.run(debug=True)
