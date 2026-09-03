from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/contact", methods=["POST"])
def contact():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    print(f"[NUEVO MENSAJE] De: {name} <{email}> | Mensaje: {message}")

    if request.is_json:
        return jsonify({"status": "success", "message": "Mensaje recibido correctamente"}), 200

    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect(url_for("admin"))
    return render_template("login.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.htm"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)

