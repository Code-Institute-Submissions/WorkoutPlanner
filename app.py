import os
import json
from flask import Flask, redirect, render_template, request, url_for, session, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from bson.json_util import dumps

if os.path.exists("env.py"):
    import env

app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
# app.config["wsgi.url_scheme"] = "https"
client = PyMongo(app)


def active_session_check(route_url):
    route_url = str(route_url)
    active_session = bool("user" in session)
    if active_session is False and (route_url != "/login" or "/register"):
        render_dict = dict({"page_render": render_template(
            "pages/login.html",
            title="Workout Planner | Login"),
                            "redirect_action": True})
    else:
        render_dict = dict({"page_render": "", "redirect_action": False})
    return render_dict


@app.route("/")
def homepage():
    if ((active_session_check(request.url_rule)))["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    return render_template(
        "pages/index.html",
        title="Workout Planner | Home")


@app.route("/login", methods=["POST", "GET"])
def login():
    active_session_check(request.url_rule)

    if request.method == "POST":
        request_data = request.get_json()
        print(request_data)
        response = {"existingUsername": False, "validPassword": False}
        logged_username = client.db.users.find_one(
            {"username": request_data["inputUsername"]}
        )
        if logged_username is None:
            response["existingUsername"] = False
            return json.dumps(response)
        response["existingUsername"] = True
        if check_password_hash(
                (logged_username["password"]),
                (request_data["inputPassword"])):
            session["user"] = request_data["inputUsername"]
            return redirect(url_for("homepage"))
        response["validPassword"] = False
        return json.dumps(response)
    return render_template(
        "pages/login.html",
        title="Workout Planner | Login")


@app.route("/register", methods=["POST", "GET"])
def register():
    active_session_check(request.url_rule)
    if request.method == "POST":
        request_data = request.get_json()
        response = {"newUsername": False, "newEmail": False}
        existing_username = client.db.users.find_one(
            {"username": request_data["inputUsername"]})
        existing_email = client.db.users.find_one(
            {"email": request_data["inputEmail"]})
        if existing_username is None:
            response["newUsername"] = True
        else:
            response["newUsername"] = False
        if existing_email is None:
            response["newEmail"] = True
        else:
            response["newEmail"] = False
        if existing_username is None and existing_email is None:
            client.db.users.insert_one(
                {
                    "username": request_data["inputUsername"],
                    "email": request_data["inputEmail"],
                    "password": generate_password_hash(
                        request_data["inputPassword"])})
            session["username"] = request_data["inputUsername"]
            return redirect(url_for("login"))
        return json.dumps(response)
    return render_template(
        "pages/register.html",
        title="Workout Planner | Register")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("homepage"))


@app.route("/globalexercises")
def global_exercises():
    if ((active_session_check(request.url_rule)))["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    exercises = client.db.exercises.find()
    return render_template(
        "pages/myexercises.html",
        title="Workout Planner | Global Exercises",
        exercises=exercises)


@app.route("/myexercises")
def my_exercises():
    if ((active_session_check(request.url_rule)))["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    exercises = client.db.exercises.aggregate(
        [{"$match": {"owner": session["user"]}}])
    return render_template(
        "pages/myexercises.html",
        title="Workout Planner | My Exercises",
        exercises=exercises)


@app.route("/createexercise", methods=["POST", "GET"])
def create_exercise():
    if ((active_session_check(request.url_rule)))["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    if request.method == "POST":
        request_data = request.get_json()
        print(request_data)
        partial_record = {"owner": session["user"], "complete": False}
        request_data.update(partial_record)
        client.db.exercises.insert_one(request_data)
    return render_template(
        "forms/exerciseform.html",
        title="Workout Planner | Edit Exercise",
        form_heading="Create Exercise",
        form_name="createExerciseForm",
        exercise={"exercisename": "chest press", "targetmuscle": "chest",
                  "equipmentname": "barbell", "weightdistancevalue": "100kg"}
    )


@app.route("/editexercise/<exercise_id>", methods=["POST", "GET"])
def edit_exercise(exercise_id):
    if (active_session_check(request.url_rule))["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    exercise = client.db.exercises.find_one(
        {"_id": ObjectId(exercise_id)}
    )
    if request.method == "POST":
        request_data = request.get_json()
        client.db.exercises.update_many({"_id": ObjectId(
            exercise_id), "owner": session["user"]}, {"$set": request_data})
    return render_template(
        "forms/exerciseform.html",
        title="Workout Planner | Edit Exercise",
        form_heading="Edit Exercise",
        exercise=exercise,
        form_name="editExerciseForm",
    )

@app.route("/cloneexercise/<exercise_id>")
def clone_exercise(exercise_id):
    original_record = client.db.exercises.find_one({"_id": ObjectId(exercise_id)})
    print(original_record)
    return dumps(original_record)
    # partial_record = {"owner": session["user"], "complete": False}
    # return exercise_id


if __name__ == '__main__':
    app.run(host=os.getenv('IP'), port=os.getenv('PORT'), debug=True)
