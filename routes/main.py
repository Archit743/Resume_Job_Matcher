from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    return render_template("index.html")
@main_bp.route("/signup")
def signup():
    return render_template("signup.html")
@main_bp.route("/login")
def login():
    return render_template("signup.html")
@main_bp.route("/home")
def homepage():
    return render_template("homepage.html")