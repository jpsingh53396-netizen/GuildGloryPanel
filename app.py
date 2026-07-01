from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
import os
import random
import string

from models import db, User, RedeemCode, BotLaunch,PaymentRequest,WebsiteSettings

from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "guild_glory_secret_key"

# DB config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Upload folder (FIXED)
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_app(app)

# ---------------- ADMIN ----------------
ADMIN_EMAIL = "admin@guild.com"
ADMIN_PASSWORD = "admin123"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User(email=email, password=password, credits=0)
        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session["user_id"] = user.id
            return redirect("/dashboard")
        else:
            return render_template("message.html", msg="Please register first")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    payments = PaymentRequest.query.filter_by(
        user_id=user.id
    ).all()

    logs = BotLaunch.query.filter_by(user_id=user.id).all()

    for l in logs:
        expire_time = l.created_at + timedelta(hours=8)

        if datetime.now() >= expire_time:
            l.expire_text = "Expired"
        else:
            remaining = expire_time - datetime.now()

            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60

            l.expire_text = f"{hours}h {minutes}m"

    return render_template(
        "dashboard.html",
        user=user,
        payments=payments,
        logs=logs
    )
    
# ---------------- PAYMENT ----------------
@app.route("/payment", methods=["POST"])
def payment():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    credits = int(request.form.get("credits"))
    utr = request.form.get("utr")

    file = request.files.get("screenshot")
    filename = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    new_request = PaymentRequest(
        user_id=user.id,
        credits_requested=credits,
        utr_number=utr,
        screenshot=filename,
        status="Pending"
    )

    db.session.add(new_request)
    db.session.commit()

    return redirect("/dashboard")


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")

        return "Invalid Admin Login"

    return render_template("admin_login.html")


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin"):
        return redirect("/admin")

    settings = WebsiteSettings.query.first()

    if not settings:
        settings = WebsiteSettings()
        db.session.add(settings)
        db.session.commit()

    users = User.query.all()
    payments = PaymentRequest.query.all()
    codes = RedeemCode.query.all()
    bot_logs = BotLaunch.query.order_by(BotLaunch.created_at.desc()).all()

    total_users = len(users)
    pending_payments = PaymentRequest.query.filter_by(status="Pending").count()
    approved_payments = PaymentRequest.query.filter_by(status="Approved").count()
    rejected_payments = PaymentRequest.query.filter_by(status="Rejected").count()

    return render_template(
        "admin_dashboard.html",
        users=users,
        payments=payments,
        codes=codes,
        bot_logs=bot_logs,
        total_users=total_users,
        pending_payments=pending_payments,
        approved_payments=approved_payments,
        rejected_payments=rejected_payments,
        settings=settings
    )


# ---------------- APPROVE PAYMENT ----------------
@app.route("/admin/approve/<int:id>")
def approve_payment(id):
    if not session.get("admin"):
        return redirect("/admin")

    req = PaymentRequest.query.get(id)
    user = User.query.get(req.user_id)

    user.credits += req.credits_requested
    req.status = "Approved"

    db.session.commit()

    return redirect("/admin/dashboard")


# ---------------- REJECT PAYMENT ----------------
@app.route("/admin/reject/<int:id>", methods=["POST"])
def reject_payment(id):
    if not session.get("admin"):
        return redirect("/admin")

    req = PaymentRequest.query.get(id)
    reason = request.form.get("reason")

    req.status = "Rejected"
    req.reject_reason = reason

    db.session.commit()

    return redirect("/admin/dashboard")


# ---------------- GENERATE REDEEM CODE ----------------
@app.route("/admin/generate-code", methods=["POST"])
def generate_redeem_code():
    if not session.get("admin"):
        return redirect("/admin")

    credits = int(request.form.get("credits"))

    code = "GG-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    new_code = RedeemCode(
        code=code,
        credits=credits,
        used=False
    )

    db.session.add(new_code)
    db.session.commit()

    return redirect("/admin/dashboard")


# ---------------- REDEEM CODE ----------------
@app.route("/redeem", methods=["POST"])
def redeem():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])
    code = request.form.get("code")

    redeem_code = RedeemCode.query.filter_by(code=code, used=False).first()

    if redeem_code:
        user.credits += redeem_code.credits
        redeem_code.used = True
        db.session.commit()

        return render_template("dashboard.html", user=user, message="Code redeemed successfully!")

    return render_template("dashboard.html", user=user, message="Invalid or already used code")
    
@app.route("/admin/toggle-maintenance")
def toggle_maintenance():

    if not session.get("admin"):
        return redirect("/admin")

    settings = WebsiteSettings.query.first()

    if not settings:
        settings = WebsiteSettings()
        db.session.add(settings)

    settings.maintenance_mode = not settings.maintenance_mode

    db.session.commit()

    return redirect("/admin/dashboard")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
    
# ---------------- LAUNCH BOT ----------------
@app.route("/launch-bot", methods=["POST"])
def launch_bot():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    if user.credits < 1:
        return "Not enough credits"

    clan_id = request.form.get("clan_id")
    server = request.form.get("server")

    user.credits -= 1

    new_log = BotLaunch(
        user_id=user.id,
        clan_id=clan_id,
        server=server
    )

    db.session.add(new_log)
    db.session.commit()

    return redirect("/dashboard")


# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=10000)
