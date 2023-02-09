import uuid
import functools
import datetime
from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    request,
    current_app,
    url_for,
    abort,
    flash,
)
from dataclasses import asdict
from movie_library.forms import (
    PodcastForm,
    ExtendedPodcastForm,
    RegisterForm,
    LoginForm,
)
from movie_library.models import Podcast, User
from passlib.hash import pbkdf2_sha256




pages = Blueprint(
    "pages", __name__, template_folder="templates", static_folder="static"
)

# Decorator ---
def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if session.get("email") is None:
            return redirect(url_for(".login"))
        return route(*args, **kwargs)
    return route_wrapper


# Index ---
@pages.route("/")
@login_required
def index():
    user_data = current_app.db.user.find_one({"email": session["email"]})
    user = User(**user_data)
    podcast_data = current_app.db.podcast.find({"_id": {"$in": user.Podcasts}})
    podcast = [Podcast(**podcast) for podcast in podcast_data]
    return render_template("index.html", title="Video Cast", podcast_data=podcast)


# Register ---
@pages.route("/register", methods=["GET", "POST"])
def register():
    if session.get("email"):
        return redirect(url_for(".index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            _id=uuid.uuid4().hex,
            email=form.email.data,
            password=pbkdf2_sha256.hash(form.password.data),
        )

        current_app.db.user.insert_one(asdict(user))

        flash("User registrated successfully", "success")
        return redirect(url_for(".login"))
    return render_template("register.html", title="Video Cast - Register", form=form)


# Login ---
@pages.route("/login", methods=["GET", "POST"])
def login():
    if session.get("email"):
        return redirect(url_for(".index"))
    form = LoginForm()
    if form.validate_on_submit():

        user_data = current_app.db.user.find_one({"email": form.email.data})

        if not user_data:
            flash("Login credentials not correct", category="danger")
            return redirect(url_for(".login"))
        user = User(**user_data)
        if user and pbkdf2_sha256.verify(form.password.data, user.password):
            session["user_id"] = user._id
            session["email"] = user.email
            return redirect(url_for(".index"))
        flash("Login credentials not correct", category="danger")
    return render_template("login.html", title="Video Cast - Login", form=form)


# Logout ---
@pages.route("/logout")
def logout():
    current_theme = session.get("theme")
    session.clear()
    session["theme"] = current_theme
    return redirect(url_for(".login"))


# Add cast ---
@pages.route("/add", methods=["GET", "POST"])
@login_required
def add_cast():
    form = PodcastForm()
    if form.validate_on_submit():
        podcast = Podcast(
            _id=uuid.uuid4().hex,
            title=form.title.data,
            host=form.host.data,
            year=form.year.data,
            video_link=form.video_link.data,
        )

        current_app.db.podcast.insert_one(asdict(podcast))
        current_app.db.user.update_one({"_id": session["user_id"]}, {"$push": {"Podcasts": podcast._id}})

        return redirect(url_for(".index"))
    return render_template("new_podcast.html", title="Video Cast - Add Cast", form=form)


# Edit cast ---
@pages.route("/edit/<string:_id>", methods=["GET", "POST"])
@login_required
def edit_podcast(_id: str):

    podcast_data = current_app.db.podcast.find_one({"_id": _id})

    podcast = Podcast(**podcast_data)
    form = ExtendedPodcastForm(obj=podcast)
    if form.validate_on_submit():
        podcast.title = form.title.data
        podcast.description = form.description.data
        podcast.year = form.year.data
        podcast.cast = form.cast.data
        podcast.series = form.series.data
        podcast.tags = form.tags.data
        podcast.description = form.description.data
        podcast.video_link = form.video_link.data

        current_app.db.podcast.update_one(
            {"_id": podcast._id}, {"$set": asdict(podcast)}
        )

        return redirect(url_for(".podcast", _id=podcast._id))
    return render_template("podcast_form.html", podcast=podcast, form=form)


# Cast details ---
@pages.get("/podcast/<string:_id>")
def podcast(_id: str):

    podcast_data = current_app.db.podcast.find_one({"_id": _id})

    if not podcast_data:
        abort(404)
    podcast = Podcast(**podcast_data)
    return render_template("podcast_details.html", podcast=podcast)

# Rating ---
@pages.get("/podcast/<string:_id>/rate")
@login_required
def rate_podcast(_id):
    rating = int(request.args.get("rating"))

    current_app.db.podcast.update_one({"_id": _id}, {"$set": {"rating": rating}})

    return redirect(url_for(".podcast", _id=_id))


# Mark watched ---
@pages.get("/podcast/<string:_id>/watch")
@login_required
def watch_today(_id):

    current_app.db.podcast.update_one(
        {"_id": _id}, {"$set": {"last_watched": datetime.datetime.today()}}
    )

    return redirect(url_for(".podcast", _id=_id))


# Toggle theme ---
@pages.get("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"
    return redirect(request.args.get("current_page"))
