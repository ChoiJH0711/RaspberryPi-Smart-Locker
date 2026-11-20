import os
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import URL
from werkzeug.security import check_password_hash, generate_password_hash

from hardware import LockerHardware


load_dotenv()

LOCKER_NUMBERS = (1, 2)
db = SQLAlchemy()
csrf = CSRFProtect()
hardware = LockerHardware()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())


class Locker(db.Model):
    __tablename__ = "lockers"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    locker_number = db.Column(db.Integer, unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="available")
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"))
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )


class LockerLog(db.Model):
    __tablename__ = "locker_logs"

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    locker_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("lockers.id"), nullable=False)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey("users.id"))
    action = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())


def database_url():
    return URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER", "locker_app"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "locker_db"),
    )


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "change-this-before-running"),
        SQLALCHEMY_DATABASE_URI=database_url(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 280},
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)

    @app.context_processor
    def inject_current_user():
        user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
        return {"current_user": user}

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("로그인이 필요합니다.", "error")
                return redirect(url_for("index"))
            return view(*args, **kwargs)

        return wrapped

    @app.get("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboard"))
        return render_template("index.html")

    @app.post("/register")
    def register():
        username = request.form.get("username", "").strip()
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not username or not name or not password:
            flash("아이디, 이름, 비밀번호를 모두 입력해주세요.", "error")
        elif len(username) < 4:
            flash("아이디는 4자 이상이어야 합니다.", "error")
        elif len(password) < 8:
            flash("비밀번호는 8자 이상이어야 합니다.", "error")
        elif password != password_confirm:
            flash("비밀번호 확인이 일치하지 않습니다.", "error")
        elif User.query.filter_by(username=username).first():
            flash("이미 사용 중인 아이디입니다.", "error")
        else:
            user = User(
                username=username,
                name=name,
                phone=phone or None,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            flash("회원가입이 완료되었습니다. 로그인해주세요.", "success")

        return redirect(url_for("index", mode="register"))

    @app.post("/login")
    def login():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("아이디 또는 비밀번호가 올바르지 않습니다.", "error")
            return redirect(url_for("index"))

        session.clear()
        session["user_id"] = user.id
        flash(f"{user.name}님, 환영합니다.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        flash("로그아웃되었습니다.", "success")
        return redirect(url_for("index"))

    @app.get("/lockers")
    @login_required
    def dashboard():
        lockers = (
            Locker.query
            .filter(Locker.locker_number.in_(LOCKER_NUMBERS))
            .order_by(Locker.locker_number)
            .all()
        )
        owned_locker = (
            Locker.query
            .filter(
                Locker.user_id == session["user_id"],
                Locker.locker_number.in_(LOCKER_NUMBERS),
            )
            .first()
        )
        return render_template(
            "dashboard.html",
            lockers=lockers,
            owned_locker=owned_locker,
        )

    @app.post("/lockers/<int:locker_id>/select")
    @login_required
    def select_locker(locker_id):
        owned_locker = (
            Locker.query
            .filter(
                Locker.user_id == session["user_id"],
                Locker.locker_number.in_(LOCKER_NUMBERS),
            )
            .first()
        )
        if owned_locker:
            flash("한 번에 하나의 락커만 사용할 수 있습니다.", "error")
            return redirect(url_for("dashboard"))

        locker = db.session.execute(
            db.select(Locker)
            .where(Locker.id == locker_id, Locker.locker_number.in_(LOCKER_NUMBERS))
            .with_for_update()
        ).scalar_one_or_none()

        if not locker or locker.user_id is not None or locker.status != "available":
            db.session.rollback()
            flash("이미 사용 중이거나 선택할 수 없는 락커입니다.", "error")
            return redirect(url_for("dashboard"))

        try:
            hardware.lock(locker.locker_number)
            locker.user_id = session["user_id"]
            locker.status = "locked"
            db.session.add(LockerLog(locker_id=locker.id, user_id=session["user_id"], action="assigned"))
            db.session.commit()
            flash(f"{locker.locker_number}번 락커가 배정되고 잠겼습니다.", "success")
        except Exception:
            db.session.rollback()
            app.logger.exception("락커 잠금 중 오류")
            flash("하드웨어 제어에 실패했습니다. 배선과 GPIO 설정을 확인해주세요.", "error")

        return redirect(url_for("dashboard"))

    @app.post("/lockers/<int:locker_id>/toggle")
    @login_required
    def toggle_locker(locker_id):
        locker = db.session.get(Locker, locker_id)
        if (
            not locker
            or locker.locker_number not in LOCKER_NUMBERS
            or locker.user_id != session["user_id"]
        ):
            flash("본인에게 배정된 락커만 제어할 수 있습니다.", "error")
            return redirect(url_for("dashboard"))

        try:
            if locker.status == "locked":
                hardware.unlock(locker.locker_number)
                locker.status = "open"
                action = "unlocked"
                message = "잠금이 해제되었습니다."
            else:
                hardware.lock(locker.locker_number)
                locker.status = "locked"
                action = "locked"
                message = "락커가 잠겼습니다."

            db.session.add(LockerLog(locker_id=locker.id, user_id=session["user_id"], action=action))
            db.session.commit()
            flash(message, "success")
        except Exception:
            db.session.rollback()
            app.logger.exception("락커 토글 중 오류")
            flash("하드웨어 제어에 실패했습니다. 배선과 전원을 확인해주세요.", "error")

        return redirect(url_for("dashboard"))

    @app.post("/lockers/<int:locker_id>/release")
    @login_required
    def release_locker(locker_id):
        locker = db.session.get(Locker, locker_id)
        if (
            not locker
            or locker.locker_number not in LOCKER_NUMBERS
            or locker.user_id != session["user_id"]
        ):
            flash("본인에게 배정된 락커만 반납할 수 있습니다.", "error")
            return redirect(url_for("dashboard"))

        try:
            hardware.unlock(locker.locker_number)
            user_id = locker.user_id
            locker.user_id = None
            locker.status = "available"
            db.session.add(LockerLog(locker_id=locker.id, user_id=user_id, action="returned"))
            db.session.commit()
            flash(f"{locker.locker_number}번 락커 사용을 종료했습니다.", "success")
        except Exception:
            db.session.rollback()
            app.logger.exception("락커 반납 중 오류")
            flash("락커를 여는 데 실패하여 반납 처리가 취소되었습니다.", "error")

        return redirect(url_for("dashboard"))

    return app


app = create_app()


def ensure_default_lockers():
    """SQL 테이블 생성 후 최초 실행 시 1~2번 락커를 채운다."""
    for locker_number in LOCKER_NUMBERS:
        if not Locker.query.filter_by(locker_number=locker_number).first():
            db.session.add(Locker(locker_number=locker_number))
    db.session.commit()


def restore_hardware_state():
    """서버 재시작 시 DB 상태에 맞춰 두 락커의 LED와 서보를 복원한다."""
    lockers = (
        Locker.query
        .filter(Locker.locker_number.in_(LOCKER_NUMBERS))
        .order_by(Locker.locker_number)
        .all()
    )
    for locker in lockers:
        if locker.status == "locked":
            hardware.lock(locker.locker_number)
        else:
            hardware.unlock(locker.locker_number)


if __name__ == "__main__":
    with app.app_context():
        ensure_default_lockers()
        restore_hardware_state()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)


