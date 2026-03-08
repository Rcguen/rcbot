from flask import render_template, request, redirect, session
import requests
import json
from storage import load_json

CLIENT_ID = "1479064692474380352"
CLIENT_SECRET = "9Depd9Mw81VEX8NVpcMdsNN9unnB32BP"
REDIRECT_URI = "https://rcbot-8120.onrender.com/callback"

AUTH_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
API_BASE = "https://discord.com/api/users/@me"

def register_routes(app, client):

    @app.route("/")
    def dashboard():

        if "user" not in session:
            return redirect("/login")

        stats = load_json("data/stats.json")

        languages = load_json("data/language_stats.json")

        return render_template(
            "index.html",
            translations=stats.get("translations",0),
            servers=len(client.guilds),
            users=len(client.users),
            bot_status="Online" if client.is_ready() else "Offline",
            languages=languages
        )

    @app.route("/login")
    def login():

        return redirect(
            f"{AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify"
        )

    @app.route("/callback")
    def callback():

        code = request.args.get("code")

        data = {
            "client_id":CLIENT_ID,
            "client_secret":CLIENT_SECRET,
            "grant_type":"authorization_code",
            "code":code,
            "redirect_uri":REDIRECT_URI
        }

        headers = {
            "Content-Type":"application/x-www-form-urlencoded"
        }

        r = requests.post(TOKEN_URL,data=data,headers=headers)

        token = r.json()["access_token"]

        user = requests.get(
            API_BASE,
            headers={"Authorization":f"Bearer {token}"}
        ).json()

        session["user"] = user

        return redirect("/")