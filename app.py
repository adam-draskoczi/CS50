from datetime import datetime
from features import analysis, batch_details, batch_new, batch_overview, batch_saved, inspection_new, inspection_saved, inspection_view, process_new, process_saved
from flask import flash, Flask, redirect, render_template, request, session
from function import login_required, signup
from helpers import dict_factory
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = "ac76c5ef0d9fb019a9b316042888aa26cc023f3682e008c48ab6a040a1b5d245"

areas = [
    ("filling", "Filling"),
    ("coating", "Coating"),
    ("topping", "Topping")
    ]

defects = [
    ("DF01", "Filling is missing"),
    ("DF02", "Overfill"),
    ("DC01", "Coating is missing"),
    ("DC02", "Coating is leaking"),
    ("DT01", "Topping is missing"),
    ("DT02", "Topping is misplaced")
    ]

parameters = [
    ("temp", "Temperature"),
    ("type", "Type"),
    ("line", "Line")
    ]


@app.context_processor
def add_userdata():

    if "user_id" in session:
        with sqlite3.connect("bonbons.db") as con:
            con.row_factory = dict_factory
            db = con.cursor()
            res = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
            userdata = res.fetchone()

        with sqlite3.connect("bonbons.db") as con:
            con.row_factory = dict_factory
            db = con.cursor()
            res = db.execute("SELECT area FROM users WHERE id = ?", (session["user_id"],))
            area = res.fetchone()["area"]

            if area == "Filling":
                query = "AND created IS NOT NULL AND filling IS NULL"
            if area == "Coating":
                query = "AND filling IS NOT NULL AND coating IS NULL"
            if area == "Topping":
                query = "AND coating IS NOT NULL AND topping IS NULL"
            if area == "Quality":
                query = "AND topping IS NOT NULL"

        with sqlite3.connect("bonbons.db") as con:
            con.row_factory = dict_factory
            db = con.cursor()
            res = db.execute("SELECT name FROM batches WHERE 1=1 " + query + " ORDER BY name")
            batches = list(res.fetchall())

        return {"userdata": userdata, "toprocess": batches}
    else:
        return {}

@app.route("/")
def index():

    if "user_id" not in session:
        return render_template("index.html")
    if "user_id" in session:
        return redirect("/home")

@app.route("/analyse", methods=["GET"])
@login_required
def analyse():

    return render_template("analyse.html", processes=areas, parameters=parameters, defects=defects)

@app.route("/analysis")
@login_required
def analysis_data():

    return analysis()

@app.route("/batch", methods=["POST", "GET"])
@login_required
def batch():

    if request.method == "GET":
        return batch_new()

    if request.method == "POST":
        return batch_saved()

@app.route("/batch-details/<string:batchname>", methods=["GET"])
@login_required
def details(batchname):

    if request.method == "GET":
        return batch_details(batchname)

@app.route("/home")
@login_required
def home():

        return render_template("home.html")

@app.route("/inspection", methods=["GET", "POST"])
@login_required
def inspection():

    if request.method == "GET":
        return inspection_new()
    if request.method == "POST":
        return inspection_saved()

@app.route("/inspection-view/<string:batchname>", methods=["GET"])
@login_required
def view_inspection(batchname):

    return inspection_view(batchname)

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        if "user_id" in session:
            return redirect("/home")
        return render_template("login.html")

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        with sqlite3.connect("bonbons.db") as con:
            con.row_factory = dict_factory
            db = con.cursor()
            res = db.execute("SELECT * FROM users WHERE username = ?", (username,))
            users = list(res.fetchall())

        if len(users) != 1:
            flash("Invalid username")
            return render_template("login.html")

        if not check_password_hash(users[0]["hash"], password):
            flash("Invalid password")
            return render_template("login.html")

        session["user_id"] = users[0]["id"]
        return redirect("/home")

@app.route("/logout")
def logout():

    session.clear()
    flash("Log out was successful.")
    return redirect("/")

@app.route("/overview")
@login_required
def overview():

    return batch_overview()

@app.route("/process", methods=["POST", "GET"])
@login_required
def process():

    if request.method == "GET":
        return process_new()

    if request.method == "POST":
        return process_saved()

@app.route("/register", methods = ["GET", "POST"])
def register():

    if request.method == "GET":
        return signup()

    if request.method == "POST":

        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        area = request.form.get("area")
        title = request.form.get("title")
        username = request.form.get("username")
        password = request.form.get("password")

        hash = generate_password_hash(password)
        reg = datetime.now()

        with sqlite3.connect("bonbons.db") as con:
            con.row_factory = dict_factory
            db = con.cursor()
            db.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?, ?, ?)", (None, username, hash, firstname, lastname, area, title, reg))
            con.commit()

        flash("Registration successful. Please log in.")
        return redirect("/login")

