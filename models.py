from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    credits = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)


class GroupRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    server = db.Column(db.String(50), nullable=False)
    clan_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), default="Pending")
    reject_reason = db.Column(db.String(300), nullable=True)


class PaymentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    credits_requested = db.Column(db.Integer, nullable=False)
    utr_number = db.Column(db.String(200), nullable=False)
    screenshot = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(30), default="Pending")
    reject_reason = db.Column(db.String(300), nullable=True)


class WebsiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    maintenance_mode = db.Column(db.Boolean, default=False)
    whatsapp_number = db.Column(db.String(30), default="8272853396")
    credit_price = db.Column(db.Integer, default=299)


class RedeemCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    used = db.Column(db.Boolean, default=False)


class BotLaunch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    server = db.Column(db.String(100))
    clan_id = db.Column(db.String(100))

    status = db.Column(db.String(50), default="RUNNING")

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())