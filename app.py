import os
import json
from flask import Flask, redirect, render_template, request, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
if os.path.exists("env.py"):
    import env


class ReverseProxied():
    """Ensures requests operate through https protocol.

    Solution to mixed content error provided by user "aldel":
    https://stackoverflow.com/a/37842465
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


# Create Flask instance, assign environment variables for DB access.
APP = Flask(__name__)
APP.wsgi_app = ReverseProxied(APP.wsgi_app)
APP.config["MONGO_URI"] = os.environ.get("MONGO_URI")
APP.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
APP.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
APP.debug = True
CLIENT = PyMongo(APP)


# Defines the route on generic site load, different for return/new users.
@APP.route("/")
def intro_route():
    """Checks if user has visited site before, if so: redirects to login."""
    if "returnUser" in session:
        return redirect(url_for("login"))
    return redirect(url_for("welcome"))


# Logged-in checker.
def active_session_check(route_url):
    """Checks if user has an active session, if not redirects to login page.

    Keyword argument:
    route_url -- The URL that the user is accessing set by the route.
    """
    route_url = str(route_url)
    active_session = bool("user" in session)
    if active_session is False and (route_url != "/login" or "/register"):
        render_dict = dict(
            {"page_render": render_template(
                "pages/authentication.html",
                title="Workout Planner | Login",
                formId="loginForm",
                currentAuthPath="login",
                alternativeAuthPath=(url_for('register')),
                alternativeAuthPathPrompt="Not registered? Click here."),
             "redirect_action": True}
        )
    else:
        render_dict = dict(
            {"page_render": "", "redirect_action": False}
        )
    return render_dict


# Welcome page.
@APP.route("/welcome")
def welcome():
    """The welcome screen to be displayed on page load."""
    session["returnUser"] = True
    return render_template(
        "pages/welcome.html",
        title="Workout Planner | Welcome",
        bodyId="welcomeBody")


# Personal exercise list.
@APP.route("/myexercises")
def my_exercises():
    """Displays a logged in user's exercise list.

    Exercise documents where the value of the field equals the name of the user
    that is logged to the session are grouped for display.
    """
    if active_session_check(request.url_rule)["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    exercises = CLIENT.db.exercises.aggregate(
        [{"$match": {"owner": session["user"]}}]
    )
    return render_template(
        "pages/exercises.html",
        title="Workout Planner | My Exercises",
        exercises=exercises,
        nav=["following", "global"])


# Followed users' exercises.
@APP.route("/following", methods=["POST", "GET"])
def followed_users():
    """Displays followed users' exercises & interface to manage followed users.

    Each followed user's exercise cards are displayed on the page.
    This function also handles requests to add/remove users from followed list.
    The result triggers an appropriate response modal in the Javascript.
    The user is allowed to add users that do not exist yet in anticipation of
    friends setting up their accounts with those usernames at a later date.
    """
    if active_session_check(request.url_rule)["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    logged_username = CLIENT.db.users.find_one({"username": session["user"]})
    existing_following = logged_username["following"]
    if request.method == "POST":
        request_data = request.get_json()
        response = {}
        if request_data == "followedUserRequest":
            return json.dumps(existing_following)
        addition_key = "addFollowUsername"
        removal_key = "removeFollowUsername"
        if addition_key in request_data:
            target_user = request_data[addition_key]
            if target_user in existing_following:
                response["followExisting"] = True
                return response
            CLIENT.db.users.update_one(
                {"username": session["user"]},
                {"$push": {"following": target_user}})
            response["followAddition"] = True
            return response
        if removal_key in request_data:
            target_user = request_data[removal_key]
            CLIENT.db.users.update_one(
                {"username": session["user"]},
                {"$pull": {"following": target_user}})
            response["followRemoval"] = True
            return response
    record_matches = []
    for user in existing_following:
        record_matches.append(list(CLIENT.db.exercises.aggregate(
            [{"$match": {"owner": user}}])))
    return render_template(
        "pages/exercises.html",
        title="Workout Planner | Following",
        nav=["myexercises", "global"],
        recordmatches=record_matches)


# Login page.
@APP.route("/login", methods=["POST", "GET"])
def login():
    """Validates data, if valid: add user to session, else: fail response.

    Checks if the submitted username exists in the database.
    If user is not in database a suitable response is returned.
    If username exists then hashed password is compared with database record.
    If both the submitted username and password match the database records:
    user is added to session and redirected to their list of exercises.
    """
    active_session_check(request.url_rule)
    if request.method == "POST":
        request_data = request.get_json()
        response = {}
        logged_username = CLIENT.db.users.find_one(
            {"username": request_data["inputUsername"]}
        )
        if logged_username is None:
            response["validUsername"] = False
            return json.dumps(response)
        response["validUsername"] = True
        if check_password_hash(
                (logged_username["password"]),
                (request_data["inputPassword"])):
            session["user"] = request_data["inputUsername"]
            response["validPassword"] = True
            response["authApproved"] = True
            return json.dumps(response)
        response["validPassword"] = False
        return json.dumps(response)
    return render_template(
        "pages/authentication.html",
        title="Workout Planner | Login",
        formId="loginForm",
        currentAuthPath="login",
        alternativeAuthPath=(url_for('register')),
        alternativeAuthPathPrompt="Not registered? Click here.")


# Register page.
@APP.route("/register", methods=["POST", "GET"])
def register():
    """Validates data, if valid: add user to db/session, else: fail response.

    Checks if submitted username or password already exist in database,
    if so then a fail message is returned.
    If user is non-existent then a new user is created,
    the password is passed in hashed form.
    User is redirected to their exercise list on successful account creation.
    """
    active_session_check(request.url_rule)
    if request.method == "POST":
        request_data = request.get_json()
        response = {}
        existing_username = CLIENT.db.users.find_one(
            {"username": request_data["inputUsername"]}
        )
        existing_email = CLIENT.db.users.find_one(
            {"email": request_data["inputEmail"]}
        )
        response["newUsername"] = bool(existing_username is None)
        response["newEmail"] = bool(existing_email is None)
        if existing_username is None and existing_email is None:
            CLIENT.db.users.insert_one(
                {"username": request_data["inputUsername"],
                 "email": request_data["inputEmail"],
                 "password": generate_password_hash(
                     request_data["inputPassword"]),
                 "following": []}
            )
            session["user"] = request_data["inputUsername"]
            response["authApproved"] = True
        return json.dumps(response)
    return render_template(
        "pages/authentication.html",
        title="Workout Planner | Register",
        formId="registerForm",
        currentAuthPath="register",
        alternativeAuthPath=(url_for('login')),
        alternativeAuthPathPrompt="Already registered? Login here.")


# Route to remove user from session (logout).
@APP.route("/logout")
def logout():
    """Clears user from session and redirects to the login page.

    This only deletes the session key for the logged-in user.
    The cookie for the site visit is preserved with this method.
    """
    del session["user"]
    return redirect(url_for("login"))


# Page of all users' exercises.
@APP.route("/globalexercises")
def global_exercises():
    """Displays exercises owned by all users."""
    if ((active_session_check(request.url_rule)))["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    exercises = CLIENT.db.exercises.find()
    return render_template(
        "pages/exercises.html",
        title="Workout Planner | Global Exercises",
        exercises=exercises,
        nav=["myexercises", "following"])

# Page with form to create a new exercise.
@APP.route("/createexercise", methods=["POST", "GET"])
def create_exercise():
    """User-defined exercise added to db, user in session recorded as owner."""
    if ((active_session_check(request.url_rule)))["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    if request.method == "POST":
        request_data = request.get_json()
        partial_record = {"owner": session["user"], "complete": False}
        request_data.update(partial_record)
        CLIENT.db.exercises.insert_one(request_data)
    return render_template(
        "components/forms/exercise.html",
        title="Workout Planner | Edit Exercise",
        nav=["following", "myexercises", "global"],
        form_heading="Create Exercise",
        form_name="createExerciseForm",
        exercise={"exercisename": "chest press", "targetmuscle": "chest",
                  "equipmentname": "barbell", "weightdistancevalue": "100kg"}
    )


# Page with form to edit an existing exercise.
@APP.route("/editexercise/<exercise_id>", methods=["POST", "GET"])
def edit_exercise(exercise_id):
    """Selected exercise updated with user details if owner is session user."""
    if (active_session_check(request.url_rule))["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    exercise = CLIENT.db.exercises.find_one(
        {"_id": ObjectId(exercise_id)}
    )
    if request.method == "POST":
        request_data = request.get_json()
        CLIENT.db.exercises.update_one(
            {"_id": ObjectId(exercise_id),
             "owner": session["user"]},
            {"$set": request_data}
        )
    return render_template(
        "components/forms/exercise.html",
        title="Workout Planner | Edit Exercise",
        form_heading="Edit Exercise",
        exercise=exercise,
        form_name="editExerciseForm",
        nav=["following", "myexercises", "global"]
    )


# Toggle exercise completion status.
@APP.route("/completeexercise/<exercise_id>", methods=["POST", "GET"])
def complete_exercise(exercise_id):
    """Selected exercise "complete" variable boolean inverted."""
    if (active_session_check(request.url_rule))["redirect_action"]:
        return active_session_check(request.url_rule)["page_render"]
    query_filter = {"_id": ObjectId(exercise_id), "owner": session["user"]}
    exercise = (CLIENT.db.exercises.find_one(query_filter))
    toggle_value = not bool(exercise["complete"])
    CLIENT.db.exercises.update_one(
        query_filter, {"$set": {"complete": toggle_value}}
    )
    return redirect(url_for("my_exercises"))


# Removal of selected exercise from database.
@APP.route("/deleteexercise/<exercise_id>")
def delete_exercise(exercise_id):
    """Selected exercise is removed from the database."""
    CLIENT.db.exercises.find_one_and_delete({"_id": ObjectId(exercise_id)})
    return redirect(url_for("my_exercises"))


# Duplication of selected exercise in database with new user.
@APP.route("/cloneexercise/<exercise_id>", methods=["POST", "GET"])
def clone_exercise(exercise_id):
    """Exercise details passed to form, exercise assigned to session user."""
    full_record = CLIENT.db.exercises.find_one({"_id": ObjectId(exercise_id)})
    partial_record = {"owner": session["user"],
                      "_id": ObjectId(), "complete": False}
    if request.method == "POST":
        request_data = request.get_json()
        request_data.update(partial_record)
        CLIENT.db.exercises.insert_one(request_data)
    return render_template(
        "components/forms/exercise.html",
        title="Workout Planner | Clone Exercise",
        form_heading="Clone Exercise",
        exercise=full_record,
        form_name="editExerciseForm",
        nav=["following", "myexercises", "global"]
    )


if __name__ == '__main__':
    APP.run(host=os.getenv('IP'), port=os.getenv('PORT'), debug=APP.debug)
