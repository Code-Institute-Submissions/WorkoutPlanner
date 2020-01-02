import os
from flask import Flask, redirect, render_template, request, url_for
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

if os.path.exists("env.py"):
    import env

app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")

client = PyMongo(app)


@app.route("/")
@app.route("/index")
def homepage():
    return render_template(
        "index.html",
        title = "Workout Planner | Home")

@app.route("/myexercises")
def exercises(owner):
    exercises = client.db.exercises.aggregate([{"$match": {"owner": owner}}])
    return render_template(
        "myexercises.html",
        title="Workout Planner | My Exercises",
        exercises = exercises)

@app.route("/login", methods=["POST", "GET"])
def login():
    users = client.db.users.find()
    if request.method == "POST":
        print(request.form["inputUsername"])
        logged_user = client.db.users.find_one({"username": request.form["inputUsername"]})
        if logged_user:
            print("Logged user found.")
        else:
            print("Logged user not found.")
    return render_template(
        "login.html",
        title="Workout Planner | Login",
        users=users)


if __name__ == '__main__':
    app.run(host=os.getenv('IP'), port=os.getenv('PORT'), debug=True)
