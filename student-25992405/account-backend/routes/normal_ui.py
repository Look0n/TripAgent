from flask import Blueprint, render_template, redirect, url_for, session

normal_ui_bp = Blueprint("normal_ui", __name__)


@normal_ui_bp.get("/")
def home():
    return render_template("index.html"), 200


@normal_ui_bp.get("/account")
def account():
    if "customer_id" not in session:
        return redirect(url_for("normal_ui.login"))

    return redirect(url_for("normal_ui.profile"))


@normal_ui_bp.get("/account/login")
def login():
    if "customer_id" in session:
        return redirect(url_for("normal_ui.profile"))

    return render_template("account/login.html"), 200


@normal_ui_bp.get("/account/register")
def register():
    if "customer_id" in session:
        return redirect(url_for("normal_ui.profile"))

    return render_template("account/register.html"), 200


@normal_ui_bp.get("/account/profile")
def profile():
    if "customer_id" not in session:
        return redirect(url_for("normal_ui.login"))

    return render_template("account/profile.html"), 200


@normal_ui_bp.get("/account/preferences")
def preferences():
    if "customer_id" not in session:
        return redirect(url_for("normal_ui.login"))

    return render_template("account/preferences.html"), 200
