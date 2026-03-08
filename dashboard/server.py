from flask import render_template
import json

def register_routes(app, client):

    @app.route("/")
    def dashboard():

        try:
            with open("data/stats.json") as f:
                stats = json.load(f)
        except:
            stats = {"translations": 0}

        try:
            with open("data/channels.json") as f:
                channels = json.load(f)
        except:
            channels = {}

        return render_template(
            "index.html",
            translations=stats.get("translations", 0),
            servers=len(client.guilds),
            users=len(client.users),
            channels=len(channels)
        )