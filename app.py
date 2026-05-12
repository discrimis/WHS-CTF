import base64
from datetime import datetime
from os import environ
from time import time

from flask import Flask, redirect, render_template, request

from admin_secret import ADMIN_USER
from flag import FLAG


APP = Flask(__name__, static_folder="public", static_url_path="")

users = {"admin": ADMIN_USER.copy()}

register_logs = []


def get_register_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def e_token(token):
    return base64.urlsafe_b64encode(token.encode()).decode()


def generate_reset_token(user, minute_offset=0):
    email_prefix = user["email"].split("@")[0]
    current_minute = int(time() // 60) + minute_offset
    return f"{user['username']}{email_prefix}{current_minute}"


def is_valid_reset_token(user, token):
    candidates = [
        e_token(generate_reset_token(user, -1)),
        e_token(generate_reset_token(user, 0)),
        e_token(generate_reset_token(user, 1)),
    ]
    return token in candidates


def get_board_row(username):
    user = users.get(username)
    if not user:
        return None

    register_log = next(
        (log for log in register_logs if log["username"] == username),
        None,
    )
    return {
        "time": register_log["time"] if register_log else "-",
        "username": user["username"],
        "email": user["email"],
    }


@APP.route("/")
def index():
    return render_template("index.html", class_name="home")


@APP.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        if username in users:
            return render_template(
                "message.html",
                title="아이디 중복",
                heading="아이디 중복",
                message="이미 등록된 username입니다. 다른 아이디로 회원가입해주세요.",
                back_url="/register",
            )

        email_exists = any(user["email"] == email for user in users.values())
        if email_exists:
            return render_template(
                "message.html",
                title="이메일 중복",
                heading="이메일 중복",
                message="이미 등록된 email입니다. 다른 이메일로 회원가입해주세요.",
                back_url="/register",
            )

        users[username] = {
            "username": username,
            "email": email,
            "password": password,
            "role": "user",
        }
        register_logs.append({
            "time": get_register_time(),
            "username": username,
            "email": email,
        })
        return redirect("/")

    return render_template("register.html")


@APP.route("/board")
def board():
    return render_template(
        "board.html",
        heading="Board",
        register_logs=register_logs,
    )


@APP.route("/board/<username>")
def board_user(username):
    board_row = get_board_row(username)
    if not board_row:
        return (
            render_template(
                "message.html",
                title="Board",
                heading="Board",
                message="User not found.",
                link_url="/board",
                link_text="Board",
            ),
            404,
        )

    return render_template(
        "board.html",
        heading=f"Board: {username}",
        register_logs=[board_row],
    )


@APP.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = users.get(username)

        if not user or user["password"] != password:
            return (
                render_template(
                    "message.html",
                    title="Login Failed",
                    message="Login failed.",
                    back_url="/login",
                ),
                401,
            )

        if user["role"] == "admin":
            return render_template(
                "message.html",
                title="Admin Page",
                heading="Admin Page",
                message=FLAG,
            )

        return render_template(
            "message.html",
            title=f"Hello, {user['username']}",
            heading=f"Hello, {user['username']}",
            message="You are normal user.",
        )

    return render_template("login.html")


@APP.route("/check", methods=["GET", "POST"])
def check():
    if request.method == "POST":
        username = request.form.get("username", "")
        email = request.form.get("email", "")
        user = users.get(username)

        if not user or user["email"] != email:
            return render_template(
                "message.html",
                title="Check",
                heading="Check",
                message="Check failed.",
                link_url="/",
                link_text="Home",
            )

        token = generate_reset_token(user)
        encoded_token = e_token(token)

        return render_template(
            "message.html",
            title="Check",
            heading="Check",
            message="Check complete.",
            extra_message=f"token = {encoded_token}",
            link_url="/",
            link_text="Home",
        )

    return render_template("check.html")


@APP.route("/reset", methods=["GET", "POST"])
def reset():
    if request.method == "POST":
        username = request.form.get("username", "")
        token = request.form.get("token", "")
        new_password = request.form.get("newPassword", "")
    else:
        username = request.args.get("username", "")
        token = request.args.get("token", "")
        new_password = ""

    user = users.get(username)

    if not user:
        return (
            render_template(
                "message.html",
                title="Invalid User",
                message="Invalid user.",
                link_url="/",
                link_text="Home",
            ),
            400,
        )

    if not is_valid_reset_token(user, token):
        return (
            render_template(
                "message.html",
                title="Invalid Token",
                message="Invalid token.",
                link_url="/check",
                link_text="Try again",
            ),
            403,
        )

    if request.method == "POST":
        user["password"] = new_password
        return render_template(
            "message.html",
            title="Password Changed",
            message="Password changed.",
            link_url="/login",
            link_text="Login",
        )

    return render_template("reset.html", username=username, token=token)


if __name__ == "__main__":
    port = int(environ.get("PORT", "3000"))
    APP.run(host="localhost", port=port)
