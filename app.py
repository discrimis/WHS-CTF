#!/usr/bin/env python3
from datetime import datetime
from os import environ
from time import time

from flask import Flask, redirect, render_template, request

from admin_secret import ADMIN_PASSWORD
from flag import FLAG


APP = Flask(__name__, static_folder="public", static_url_path="")

users = {
    "admin": {
        "username": "admin",
        "email": "ctfproblem@ctf.local",
        "password": ADMIN_PASSWORD,
        "role": "admin",
    }
}

register_logs = []


def get_register_time():
    now = datetime.now()
    return f"{now.year}:{now.hour:02d}:{now.minute:02d}"


def generate_reset_token(user, minute_offset=0):
    email_prefix = user["email"].split("@")[0]
    current_minute = int(time() // 60) + minute_offset
    return f"{email_prefix}{user['password']}{current_minute}"


def is_valid_reset_token(user, token):
    candidates = [
        generate_reset_token(user, -1),
        generate_reset_token(user, 0),
        generate_reset_token(user, 1),
    ]
    return token in candidates


@APP.route("/")
def index():
    return render_template("index.html")


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
    return render_template("board.html", register_logs=register_logs)


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


@APP.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        username = request.form.get("username", "")
        email = request.form.get("email", "")
        user = users.get(username)

        if not user or user["email"] != email:
            return render_template(
                "message.html",
                title="Password Lookup",
                message="If the account exists, password lookup has been processed.",
                link_url="/",
                link_text="Home",
            )

        return render_template(
            "message.html",
            title="Password Found",
            heading="Password Found",
            message="",
            extra_message=f"Password: {user['password']}",
            link_url="/login",
            link_text="Login",
        )

    return render_template("forgot.html")


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
                message="Invalid reset token.",
                link_url="/forgot",
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
