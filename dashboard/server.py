from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route("/")
def home():

    with open("data/stats.json") as f:
        stats = json.load(f)

    return render_template("index.html", stats=stats)

def start_dashboard():

    app.run(
        host="0.0.0.0",
        port=8080
    )