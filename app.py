import re
from datetime import datetime
from flask import Flask, render_template, url_for


app = Flask(__name__)


@app.route("/hello/")
@app.route("/hello/<name>")
def hello_there(name = None):
    print(name)
    return render_template(
        "hello_there.html",
        name=name,
        date=datetime.now()
    )
    
@app.route("/api/data")
def get_data():
    return app.send_static_file("data.json")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/news")
def news():
    return render_template("news.html")
