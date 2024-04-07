from flask import Flask, request, render_template, flash, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from flask_sqlalchemy import SQLAlchemy
import os
import requests    # ← new import\
import time
from sqlalchemy.sql.functions import user

from sqlalchemy.sql import func 
import json

from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client
from datetime import datetime


import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
) 


scheduler = BackgroundScheduler()
scheduler.start()

# auth0 routes 

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# create db for tasks  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flash.db'
dbt = SQLAlchemy(app)

	# db model 
class Flash(dbt.Model):
    id = dbt.Column(dbt.Integer, primary_key=True)
    question = dbt.Column(dbt.String(150000000000))
    answer = dbt.Column(dbt.String(150000000000))
    date = dbt.Column(dbt.DateTime(timezone=True), default=func.now())

    def __repr__(self):
            return f"Post('{self.question}', '{self.answer}')"
with app.app_context():
        dbt.create_all()
        print('Created Database!')


    # Fetch two random entries from the database




@app.route("/")
def home():
    return render_template("index.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))


@app.route("/contact")
def contact():
    return render_template("contact.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))



@app.route("/settings")
def settings():
    return render_template("settings.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))



# user can edit, delete and add new flashcards 
@app.route('/flashcards', methods=['GET', 'POST'])
def flashcards():
    if request.method == 'POST':
        question = request.form.get('question')
        answer = request.form.get('answer')
        new_flashcard = Flash(question=question, answer=answer)
        dbt.session.add(new_flashcard)
        dbt.session.commit()

            
        flash('Flashcard added!', category='success')

    # Query all flashcards
    flashes = Flash.query.all()

    return render_template('notes.html', flashes=flashes,  session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))


@app.route("/delete", methods=["POST"])
def delete():
    question = request.form.get("question")
    answer = request.form.get("answer")
    random_data = Flash.query.order_by(func.random()).limit(1).all()
    
    dbt.session.delete(flash)
    dbt.session.commit()
    return redirect("/flashcards")


@app.route("/sms", methods=['POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""
    # Fetch the message
    msg = request.form.get('Body').lower()
    resp = MessagingResponse()
    random_data = Flash.query.first()

    if random_data:  # Check if a record exists
        random_ques = random_data.question
        random_ans = random_data.answer
    



        

    if 'set-up' in msg:
        resp.message(f"At what times do you want study your quizzes? \t 1) Morning \t 2) Morning - Afternoon \t 3) Afternoon \t 4) Afternoon \t 5) Afternoon-evening")
    elif "1" in msg:
        hour = 10
    scheduler.add_job( 'cron', hour=10)  
        resp.message("saved!")
    elif "3" in msg:
        hour = '10-11'
        resp.message("saved!")
    elif "quiz" in msg:
        resp.message(f"the question is {random_ques}")

    elif msg == random_ans:
        resp.message("Correct answer! keep going!!")
    else:
        resp.message(f"Wrong answer! but don't lose hope \n The correct answer is:\t {random_ans}")

    return str(resp)

 
if __name__ == "__main__":
    app.run(debug=True)
