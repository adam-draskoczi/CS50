from flask import redirect, render_template, session
from functools import wraps
from helpers import dict_factory
import sqlite3

areas = ["Filling", "Coating", "Topping", "Quality"]

titles = ["Engineer", "Team Lead", "Operator", "Quality inspector"]


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def signup():

    with sqlite3.connect("bonbons.db") as con:
        con.row_factory = dict_factory
        db = con.cursor()
        res = db.execute("SELECT username FROM users")
        users = list(res.fetchall())

        usernames = []
        for user in users:
            usernames.append(user["username"].upper())

    return render_template("register.html", areas=areas, titles=titles, usernames=usernames)


