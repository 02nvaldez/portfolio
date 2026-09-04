import os
import sqlite3
import hashlib
from datetime import datetime, timezone, timedelta
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# ── Timezone & Date Formatting (Colombia UTC-5) ─────────────────────────────────
COLOMBIA_TZ = timezone(timedelta(hours=-5))
MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def now_colombia():
    """Retorna un datetime con la hora actual de Colombia (UTC-5)."""
    return datetime.now(COLOMBIA_TZ)


def format_colombia_date(dt_input):
    """
    Formatea una fecha como: día, mes (3 letras), año y hora:min con a.m. o p.m.
    Ejemplo: '4 Sep, 2026 - 12:04 p.m.'
    Soporta strings SQLite ('YYYY-MM-DD HH:MM:SS') y objetos datetime en hora colombiana.
    """
    if not dt_input:
        return ""

    if isinstance(dt_input, str):
        cleaned = dt_input.split(".")[0].split("+")[0].strip()
        try:
            dt = datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return dt_input
    elif isinstance(dt_input, datetime):
        if dt_input.tzinfo is not None:
            dt = dt_input.astimezone(COLOMBIA_TZ)
        else:
            dt = dt_input
    else:
        return str(dt_input)

    mes = MESES_ES[dt.month - 1]
    hora_12 = dt.strftime("%I:%M").lstrip("0")
    if not hora_12.startswith(("10:", "11:", "12:")) and len(hora_12) == 4:
        # por si quedó como '9:05'
        pass
    periodo = "a.m." if dt.hour < 12 else "p.m."
    return f"{dt.day} {mes}, {dt.year} - {hora_12} {periodo}"


# ── App Configuration ──────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Registrar filtro Jinja para formatear fechas directamente si se desea
app.jinja_env.filters["format_date"] = format_colombia_date

# Registrar filtro urlencode para strings
from urllib.parse import quote as _url_quote
app.jinja_env.filters["urlencode"] = lambda s: _url_quote(str(s))


# ── Uploads Configuration ───────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "svg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Database ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "portfolio.db")


def get_db():
    """Abre una conexión a la base de datos."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea las tablas necesarias y siembra datos iniciales si no existen."""
    with get_db() as conn:
        # Tabla de usuarios
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL
            )
        """)

        # Tabla de proyectos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT NOT NULL,
                category     TEXT NOT NULL,
                year         TEXT NOT NULL,
                accent_color TEXT DEFAULT '#149CEA',
                image_url    TEXT NOT NULL,
                description  TEXT NOT NULL,
                tags         TEXT NOT NULL,
                project_url  TEXT,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de mensajes de contacto
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                email      TEXT NOT NULL,
                whatsapp   TEXT,
                message    TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de habilidades (skills)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                category   TEXT NOT NULL,
                name       TEXT NOT NULL,
                order_num  INTEGER DEFAULT 0
            )
        """)

        # Tabla de visualizaciones de la página
        conn.execute("""
            CREATE TABLE IF NOT EXISTS page_views (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_hash    TEXT,
                user_agent TEXT,
                path       TEXT DEFAULT '/',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Crear usuario admin por defecto si la tabla está vacía
        existing = conn.execute("SELECT id FROM users LIMIT 1").fetchone()
        if not existing:
            default_password = generate_password_hash("admin123")
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                ("admin", default_password),
            )
            conn.commit()
            print("[DB] Usuario admin creado con contraseña: admin123")

        # Sembrar habilidades iniciales si la tabla está vacía
        existing_skills = conn.execute("SELECT id FROM skills LIMIT 1").fetchone()
        if not existing_skills:
            seed_skills = [
                # Lenguajes de Programación
                ("Lenguajes de Programación", "Python", 1),
                ("Lenguajes de Programación", "PHP", 2),
                ("Lenguajes de Programación", "JavaScript (ES6+)", 3),
                ("Lenguajes de Programación", "HTML5 / CSS3", 4),
                # Frameworks & Tecnologías Web
                ("Frameworks & Tecnologías Web", "Flask", 1),
                ("Frameworks & Tecnologías Web", "Bootstrap / Tailwind CSS", 2),
                ("Frameworks & Tecnologías Web", "Manipulación del DOM y AJAX", 3),
                # Bases de Datos
                ("Bases de Datos", "MariaDB", 1),
                ("Bases de Datos", "MySQL", 2),
                # Herramientas & Entorno
                ("Herramientas & Entorno", "Git / GitHub (Control de versiones)", 1),
                ("Herramientas & Entorno", "Visual Studio Code", 2),
                ("Herramientas & Entorno", "Linux (Entornos Mint / Bash)", 3),
                ("Herramientas & Entorno", "VirtualBox (Virtualización)", 4),
            ]
            conn.executemany(
                "INSERT INTO skills (category, name, order_num) VALUES (?, ?, ?)",
                seed_skills,
            )
            conn.commit()
            print("[DB] 13 habilidades iniciales sembradas correctamente.")

        # Sembrar proyectos iniciales de la plantilla si la tabla está vacía
        existing_projects = conn.execute("SELECT id FROM projects LIMIT 1").fetchone()
        if not existing_projects:
            seed_projects = [
                (
                    "Meridian Design System",
                    "Sistema de Diseño · React",
                    "2024",
                    "#149CEA",
                    "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&h=450&fit=crop&auto=format",
                    "Librería de componentes utilizada por 12 equipos de producto. Redujo la inconsistencia visual en un 80% y el tiempo de handoff de diseño a desarrollo de 3 días a medio día.",
                    "React, TypeScript, Storybook, Figma",
                    None,
                ),
                (
                    "Cartograph Analytics",
                    "Visualización de Datos · Full Stack",
                    "2024",
                    "#4ecdc4",
                    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=450&fit=crop&auto=format",
                    "Plataforma de análisis geoespacial en tiempo real que procesa más de 2M de eventos por hora. Desarrollé un renderizador WebGL propio que redujo el tiempo de render de 4.2s a 180ms.",
                    "Next.js, WebGL, PostgreSQL, Redis",
                    None,
                ),
                (
                    "Folio CMS",
                    "SaaS · Backend",
                    "2023",
                    "#f7c06e",
                    "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&h=450&fit=crop&auto=format",
                    "CMS headless con constructor visual de consultas. 340 equipos de pago, $42k MRR. Construido en solitario en 8 meses, posteriormente adquirido por una startup de infraestructura de contenido.",
                    "Node.js, GraphQL, React, AWS",
                    None,
                ),
                (
                    "Pulse Notification Engine",
                    "Infraestructura · Open Source",
                    "2023",
                    "#ff6b9d",
                    "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&h=450&fit=crop&auto=format",
                    "Sistema de orquestación de notificaciones multicanal. 4.7k estrellas en GitHub, usado en producción por más de 200 empresas que envían 50M+ notificaciones al mes.",
                    "Go, Kafka, Docker, Kubernetes",
                    None,
                ),
            ]
            conn.executemany(
                """
                INSERT INTO projects (title, category, year, accent_color, image_url, description, tags, project_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                seed_projects,
            )
            conn.commit()
            print("[DB] 4 proyectos iniciales sembrados correctamente.")


# Inicializar la base de datos al arrancar
with app.app_context():
    init_db()

# ── Flask-Login ─────────────────────────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Debes iniciar sesión para acceder al panel."


class User(UserMixin):
    """Modelo de usuario cargado desde la base de datos."""

    def __init__(self, id, username):
        self.id = id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    with get_db() as conn:
        row = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    if row:
        return User(row["id"], row["username"])
    return None


def record_page_view(path="/"):
    """Registra una visualización de página evitando bots comunes y administradores logueados."""
    try:
        # Si el usuario es el administrador autenticado, no inflar métricas
        if current_user.is_authenticated:
            return

        user_agent = request.headers.get("User-Agent", "")
        # Filtrar bots obvios
        ua_lower = user_agent.lower()
        if any(bot in ua_lower for bot in ["bot", "spider", "crawl", "lighthouse", "preview"]):
            return

        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
        if "," in ip:
            ip = ip.split(",")[0].strip()
        ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16] if ip else "unknown"

        now_str = now_colombia().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            conn.execute(
                "INSERT INTO page_views (ip_hash, user_agent, path, created_at) VALUES (?, ?, ?, ?)",
                (ip_hash, user_agent[:255], path, now_str),
            )
            conn.commit()
    except Exception as e:
        print(f"[PAGE VIEW ERROR] {e}")


# ── Routes ──────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    record_page_view(path="/")
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
        projects = []
        for r in rows:
            p = dict(r)
            p["tag_list"] = [t.strip() for t in p["tags"].split(",") if t.strip()]
            projects.append(p)

        skill_rows = conn.execute("SELECT * FROM skills ORDER BY category, order_num, id").fetchall()
        # Agrupar habilidades por categoría
        skills_by_category = {}
        for s in skill_rows:
            cat = s["category"]
            if cat not in skills_by_category:
                skills_by_category[cat] = []
            skills_by_category[cat].append(dict(s))

    return render_template("index.html", projects=projects, skills_by_category=skills_by_category)


@app.route("/contact", methods=["POST"])
def contact():
    """Recibe el mensaje del formulario de contacto y lo almacena en la base de datos."""

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    phone_code = data.get("phone_code", "").strip()
    phone_number = data.get("whatsapp", "").strip()
    
    # Combinar indicativo y número si se proveyó número
    whatsapp = ""
    if phone_number:
        if phone_code and not phone_number.startswith("+"):
            whatsapp = f"{phone_code} {phone_number}"
        else:
            whatsapp = phone_number

    print(f"[NUEVO MENSAJE] De: {name} | WhatsApp: {whatsapp} | Email: {email} | Mensaje: {message}")

    if name and whatsapp and message:
        with get_db() as conn:
            now_str = now_colombia().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO messages (name, email, whatsapp, message, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, email, whatsapp, message, now_str),
            )
            conn.commit()

    if request.is_json:
        return jsonify({"status": "success", "message": "Mensaje recibido correctamente"}), 200

    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Muestra el formulario de login y autentica al usuario."""

    if current_user.is_authenticated:
        return redirect(url_for("admin"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        with get_db() as conn:
            row = conn.execute(
                "SELECT id, username, password FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if row and check_password_hash(row["password"], password):
            user = User(row["id"], row["username"])
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin"))
        else:
            error = "Usuario o contraseña incorrectos."

    return render_template("login.html", error=error)


@app.route("/logout")
@login_required
def logout():
    """Cierra la sesión del usuario."""
    logout_user()
    return redirect(url_for("login"))


@app.route("/admin")
@login_required
def admin():
    """Panel de administración con proyectos, habilidades y mensajes."""
    with get_db() as conn:
        project_rows = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
        projects = []
        for r in project_rows:
            p = dict(r)
            p["tag_list"] = [t.strip() for t in p["tags"].split(",") if t.strip()]
            projects.append(p)

        skills = [dict(s) for s in conn.execute("SELECT * FROM skills ORDER BY category, order_num, id").fetchall()]
        
        # Categorías únicas para el desplegable del modal
        categories = [r["category"] for r in conn.execute("SELECT DISTINCT category FROM skills ORDER BY category").fetchall()]
        if not categories:
            categories = [
                "Lenguajes de Programación",
                "Frameworks & Tecnologías Web",
                "Bases de Datos",
                "Herramientas & Entorno"
            ]

        raw_messages = conn.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 20").fetchall()
        messages = []
        for m in raw_messages:
            msg_dict = dict(m)
            msg_dict["formatted_date"] = format_colombia_date(msg_dict.get("created_at"))
            
            # Limpiar número de whatsapp para enlace directo api.whatsapp.com/send o wa.me
            raw_wa = msg_dict.get("whatsapp") or ""
            # Dejar solo dígitos
            clean_digits = "".join(ch for ch in raw_wa if ch.isdigit())
            msg_dict["clean_whatsapp"] = clean_digits
            messages.append(msg_dict)

        # Estadísticas de visualizaciones
        total_views_row = conn.execute("SELECT COUNT(*) as cnt FROM page_views").fetchone()
        total_views = total_views_row["cnt"] if total_views_row else 0

        unique_visitors_row = conn.execute("SELECT COUNT(DISTINCT ip_hash) as cnt FROM page_views").fetchone()
        unique_visitors = unique_visitors_row["cnt"] if unique_visitors_row else 0

        # Visualizaciones hoy (Colombia)
        today_prefix = now_colombia().strftime("%Y-%m-%d")
        today_views_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM page_views WHERE created_at LIKE ?",
            (f"{today_prefix}%",),
        ).fetchone()
        today_views = today_views_row["cnt"] if today_views_row else 0

    return render_template(
        "admin.html",
        username=current_user.username,
        projects=projects,
        skills=skills,
        categories=categories,
        messages=messages,
        total_views=total_views,
        unique_visitors=unique_visitors,
        today_views=today_views,
    )


@app.route("/admin/projects/new", methods=["POST"])
@login_required
def add_project():
    """Recibe y guarda un nuevo proyecto desde el panel de admin."""
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    year = request.form.get("year", "").strip()
    accent_color = request.form.get("accent_color", "#149CEA").strip()
    image_url = request.form.get("image_url", "").strip()
    description = request.form.get("description", "").strip()
    tags = request.form.get("tags", "").strip()
    project_url = request.form.get("project_url", "").strip() or None

    # Manejar subida de archivo si se adjuntó uno
    if "image_file" in request.files:
        file = request.files["image_file"]
        if file and file.filename != "" and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import uuid
            unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
            file.save(file_path)
            image_url = url_for("static", filename=f"uploads/{unique_name}")

    if not image_url:
        image_url = "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&h=450&fit=crop&auto=format"

    if title and category and description:
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO projects (title, category, year, accent_color, image_url, description, tags, project_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, category, year, accent_color, image_url, description, tags, project_url),
            )
            conn.commit()

    return redirect(url_for("admin"))


@app.route("/admin/projects/<int:project_id>/edit", methods=["POST"])
@login_required
def edit_project(project_id):
    """Actualiza un proyecto existente."""
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    year = request.form.get("year", "").strip()
    accent_color = request.form.get("accent_color", "#149CEA").strip()
    image_url = request.form.get("image_url", "").strip()
    description = request.form.get("description", "").strip()
    tags = request.form.get("tags", "").strip()
    project_url = request.form.get("project_url", "").strip() or None

    # Manejar si se subió un nuevo archivo
    if "image_file" in request.files:
        file = request.files["image_file"]
        if file and file.filename != "" and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import uuid
            unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
            file.save(file_path)
            image_url = url_for("static", filename=f"uploads/{unique_name}")

    if title and category and description:
        with get_db() as conn:
            if image_url:
                conn.execute(
                    """
                    UPDATE projects
                    SET title = ?, category = ?, year = ?, accent_color = ?, image_url = ?, description = ?, tags = ?, project_url = ?
                    WHERE id = ?
                    """,
                    (title, category, year, accent_color, image_url, description, tags, project_url, project_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE projects
                    SET title = ?, category = ?, year = ?, accent_color = ?, description = ?, tags = ?, project_url = ?
                    WHERE id = ?
                    """,
                    (title, category, year, accent_color, description, tags, project_url, project_id),
                )
            conn.commit()

    return redirect(url_for("admin"))


@app.route("/admin/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id):
    """Elimina un proyecto existente."""
    with get_db() as conn:
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
    return redirect(url_for("admin"))


# ── Skills Routes ───────────────────────────────────────────────────────────────
@app.route("/admin/skills/new", methods=["POST"])
@login_required
def add_skill():
    """Añade una nueva habilidad."""
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    custom_category = request.form.get("custom_category", "").strip()

    final_category = custom_category if category == "__custom__" and custom_category else category

    if name and final_category:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO skills (category, name) VALUES (?, ?)",
                (final_category, name),
            )
            conn.commit()

    return redirect(url_for("admin"))


@app.route("/admin/skills/<int:skill_id>/edit", methods=["POST"])
@login_required
def edit_skill(skill_id):
    """Edita una habilidad existente."""
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    custom_category = request.form.get("custom_category", "").strip()

    final_category = custom_category if category == "__custom__" and custom_category else category

    if name and final_category:
        with get_db() as conn:
            conn.execute(
                "UPDATE skills SET category = ?, name = ? WHERE id = ?",
                (final_category, name, skill_id),
            )
            conn.commit()

    return redirect(url_for("admin"))


@app.route("/admin/skills/<int:skill_id>/delete", methods=["POST"])
@login_required
def delete_skill(skill_id):
    """Elimina una habilidad."""
    with get_db() as conn:
        conn.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
        conn.commit()
    return redirect(url_for("admin"))


# ── Error Handlers ──────────────────────────────────────────────────────────────
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.htm"), 404


@app.errorhandler(503)
def service_unavailable(e):
    return render_template("503.htm"), 503


# ── Entry Point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)

