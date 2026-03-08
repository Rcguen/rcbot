from flask import render_template, request, redirect
import json
from storage import load_json, save_json

CHANNEL_FILE = "data/channels.json"

def register_routes(app, client):

    @app.route("/")
    def dashboard():

        try:
            with open("data/stats.json") as f:
                stats = json.load(f)
        except:
            stats = {"translations": 0}

        channels = load_json(CHANNEL_FILE)

        chart_data = [
            stats.get("translations",0)-5,
            stats.get("translations",0)-3,
            stats.get("translations",0)-1,
            stats.get("translations",0)
        ]

        return render_template(
            "index.html",
            translations=stats.get("translations",0),
            servers=len(client.guilds),
            users=len(client.users),
            channels=channels,
            chart_data=chart_data
        )


    @app.route("/add_channel", methods=["POST"])
    def add_channel():

        cid = request.form.get("channel_id")

        channels = load_json(CHANNEL_FILE)

        channels[cid] = True

        save_json(CHANNEL_FILE, channels)

        return redirect("/")


    @app.route("/remove_channel", methods=["POST"])
    def remove_channel():

        cid = request.form.get("channel_id")

        channels = load_json(CHANNEL_FILE)

        channels.pop(cid, None)

        save_json(CHANNEL_FILE, channels)

        return redirect("/")