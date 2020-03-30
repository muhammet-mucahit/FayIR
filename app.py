# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    abort,
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
import sys

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

# shows = db.Table(
#     "Show",
#     db.Column("artist_id", db.Integer, db.ForeignKey("Artist.id"), primary_key=True),
#     db.Column("venue_id", db.Integer, db.ForeignKey("Venue.id"), primary_key=True),
#     db.Column("start_time", db.DateTime),
# )


class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String(30)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())

    shows = db.relationship("Show", cascade="all, delete-orphan", backref="venues",)

    def to_dict(self):
        """ Returns a dictinary of vevenuesnues """
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "state": self.state,
            "address": self.address,
            "phone": self.phone,
            "genres": self.genres,
            "image_link": self.image_link,
            "facebook_link": self.facebook_link,
            "website": self.website,
            "seeking_talent": self.seeking_talent,
            "seeking_description": self.seeking_description,
        }

    def __repr__(self):
        return f"<Venue {self.id} {self.name}>"


class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String(30)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())

    shows = db.relationship("Show", cascade="all, delete-orphan", backref="artists")

    def to_dict(self):
        """ Returns a dictinary of vevenuesnues """
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "state": self.state,
            "phone": self.phone,
            "genres": self.genres,
            "image_link": self.image_link,
            "facebook_link": self.facebook_link,
            "website": self.website,
            "seeking_venue": self.seeking_venue,
            "seeking_description": self.seeking_description,
        }


class Show(db.Model):
    __tablename__ = "Show"

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id",))
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"))
    start_time = db.Column(db.DateTime, nullable=False)

    venue = db.relationship("Venue")
    artist = db.relationship("Artist")

    def show_artist(self):
        """ Returns a dictinary of artists for the show """
        return {
            "artist_id": self.artist_id,
            "artist_name": self.artist.name,
            "artist_image_link": self.artist.image_link,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def show_venue(self):
        """ Returns a dictinary of venues for the show """
        return {
            "venue_id": self.venue_id,
            "venue_name": self.venue.name,
            "venue_image_link": self.venue.image_link,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
        }


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE | d MMMM y | HH:MM"
    elif format == "medium":
        format = "EE MM, dd, y HH:MM"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    data = [venue.to_dict() for venue in Venue.query.all()]
    city_states = (
        db.session.query(Venue.city, Venue.state)
        .group_by(Venue.city, Venue.state)
        .all()
    )

    venues_data = list()
    for c in city_states:
        venue_dict = {}
        venue_dict["city"], venue_dict["state"] = c[0], c[1]
        venue_dict["venues"] = [
            {"id": v.id, "name": v.name, "num_upcoming_shows": 0}
            for v in Venue.query.filter_by(city=venue_dict["city"]).all()
        ]
        venues_data.append(venue_dict)

    return render_template("pages/venues.html", areas=venues_data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    search_term = request.form.get("search_term", "")
    search_result = Venue.query.filter(
        Venue.name.ilike("%{}%".format(search_term))
    ).all()
    response = {
        "count": len(search_result),
        "data": [
            {"id": v.id, "name": v.name, "num_upcoming_shows": 0,}
            for v in search_result
        ],
    }
    return render_template(
        "pages/search_venues.html", results=response, search_term=search_term,
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    venue_dict = venue.to_dict()

    past_shows = list(filter(lambda x: x.start_time < datetime.today(), venue.shows,))
    upcoming_shows = list(
        filter(lambda x: x.start_time >= datetime.today(), venue.shows,)
    )

    past_shows = list(map(lambda x: x.show_artist(), past_shows))
    upcoming_shows = list(map(lambda x: x.show_artist(), upcoming_shows))

    venue_dict["past_shows"] = past_shows
    venue_dict["upcoming_shows"] = upcoming_shows
    venue_dict["past_shows_count"] = len(past_shows)
    venue_dict["upcoming_shows_count"] = len(upcoming_shows)

    return render_template("pages/show_venue.html", venue=venue_dict)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    error = False
    try:
        venue = Venue()
        venue.name = request.form["name"]
        venue.city = request.form["city"]
        venue.state = request.form["state"]
        venue.phone = request.form["phone"]
        venue.address = request.form["address"]
        venue.genres = request.form.getlist("genres")
        venue.facebook_link = request.form["facebook_link"]
        venue.website = request.form["website"]
        venue.image_link = request.form["image_link"]
        venue.seeking_venue = (
            True
            if "seeking_talent" in request.form
            and request.form["seeking_talent"] == "y"
            else False
        )
        venue.seeking_description = request.form["seeking_description"]
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash(
                "An error occurred. Venue "
                + request.form["name"]
                + " could not be listed."
            )
        else:
            flash("Venue " + request.form["name"] + " was successfully listed!")
        return render_template("pages/home.html")


#  Update Venue
#  ----------------------------------------------------------------
@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).one_or_none()

    if venue is None:
        abort(404)

    form = VenueForm(
        request.form,
        name=venue.name,
        city=venue.city,
        state=venue.state,
        phone=venue.phone,
        facebook_link=venue.facebook_link,
        genres=venue.genres,
        website=venue.website,
        seeking_venue=venue.seeking_talent,
        seeking_description=venue.seeking_description,
        image_link=venue.image_link,
        address=venue.address,
    )

    return render_template("forms/edit_venue.html", form=form, venue=venue.to_dict())


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form["name"]
        venue.city = request.form["city"]
        venue.state = request.form["state"]
        venue.phone = request.form["phone"]
        venue.address = request.form["address"]
        venue.genres = request.form.getlist("genres")
        venue.facebook_link = request.form["facebook_link"]
        venue.website = request.form["website"]
        venue.image_link = request.form["image_link"]
        venue.seeking_talent = (
            True
            if "seeking_talent" in request.form
            and request.form["seeking_talent"] == "y"
            else False
        )
        venue.seeking_description = request.form["seeking_description"]
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash(
                "An error occurred. Venue "
                + request.form["name"]
                + " could not be updated."
            )
        else:
            flash("Venue " + request.form["name"] + " was successfully updated!")

        return redirect(url_for("show_venue", venue_id=venue_id))


#  Delete Venue
#  ----------------------------------------------------------------
@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).one_or_none()
    if venue is None:
        abort(404)
    db.session.delete(venue)
    db.session.commit()

    return None


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    artists = Artist.query.order_by(Artist.id).all()
    return render_template("pages/artists.html", artists=artists)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    search_term = request.form.get("search_term", "")
    artists = Artist.query.filter(Artist.name.ilike("%{}%".format(search_term))).all()
    data = [{"id": a.id, "name": a.name, "num_upcoming_shows": 0} for a in artists]

    response = {
        "count": len(artists),
        "data": data,
    }
    return render_template(
        "pages/search_artists.html", results=response, search_term=search_term,
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).one_or_none()
    if artist is None:
        abort(404)
    artist_dict = artist.to_dict()

    past_shows = list(filter(lambda x: x.start_time < datetime.today(), artist.shows,))
    upcoming_shows = list(
        filter(lambda x: x.start_time >= datetime.today(), artist.shows,)
    )

    past_shows = list(map(lambda x: x.show_venue(), past_shows))
    upcoming_shows = list(map(lambda x: x.show_venue(), upcoming_shows))

    artist_dict["past_shows"] = past_shows
    artist_dict["upcoming_shows"] = upcoming_shows
    artist_dict["past_shows_count"] = len(past_shows)
    artist_dict["upcoming_shows_count"] = len(upcoming_shows)
    return render_template("pages/show_artist.html", artist=artist_dict)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).one_or_none()

    if artist is None:
        abort(404)

    form = ArtistForm(
        request.form,
        name=artist.name,
        city=artist.city,
        state=artist.state,
        phone=artist.phone,
        facebook_link=artist.facebook_link,
        genres=artist.genres,
        website=artist.website,
        seeking_venue=artist.seeking_venue,
        seeking_description=artist.seeking_description,
        image_link=artist.image_link,
    )

    return render_template("forms/edit_artist.html", form=form, artist=artist.to_dict())


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form["name"]
        artist.city = request.form["city"]
        artist.state = request.form["state"]
        artist.phone = request.form["phone"]
        artist.genres = request.form.getlist("genres")
        artist.facebook_link = request.form["facebook_link"]
        artist.website = request.form["website"]
        artist.image_link = request.form["image_link"]
        artist.seeking_venue = (
            True
            if "seeking_venue" in request.form and request.form["seeking_venue"] == "y"
            else False
        )
        artist.seeking_description = request.form["seeking_description"]
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash(
                "An error occurred. Artist "
                + request.form["name"]
                + " could not be updated."
            )
        else:
            flash("Artist " + request.form["name"] + " was successfully updated!")

        return redirect(url_for("show_artist", artist_id=artist_id))


#  Delete
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>", methods=["DELETE"])
def delete_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).one_or_none()
    if artist is None:
        abort(404)
    db.session.delete(artist)
    db.session.commit()

    return {"success": True}


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    error = False
    try:
        artist = Artist()
        artist.name = request.form["name"]
        artist.city = request.form["city"]
        artist.state = request.form["state"]
        artist.phone = request.form["phone"]
        artist.genres = request.form.getlist("genres")
        artist.facebook_link = request.form["facebook_link"]
        artist.website = request.form["website"]
        artist.image_link = request.form["image_link"]
        artist.seeking_venue = (
            True
            if "seeking_venue" in request.form and request.form["seeking_venue"] == "y"
            else False
        )
        artist.seeking_description = request.form["seeking_description"]
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash(
                "An error occurred. Artist "
                + request.form["name"]
                + " could not be listed."
            )
        else:
            flash("Artist " + request.form["name"] + " was successfully listed!")
        return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    data = [
        {
            "venue_id": show.venue_id,
            "venue_name": Venue.query.get(show.venue_id).name,
            "artist_id": show.artist_id,
            "artist_name": Artist.query.get(show.artist_id).name,
            "artist_image_link": Artist.query.get(show.artist_id).image_link,
            "start_time": str(show.start_time),
        }
        for show in Show.query.all()
    ]
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    error = False
    try:
        show = Show()
        show.artist_id = request.form["artist_id"]
        show.venue_id = request.form["venue_id"]
        show.start_time = request.form["start_time"]
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash("An error occurred. Show could not be listed.")
        else:
            flash("Show was successfully listed!")
        return render_template("pages/home.html")


@app.route("/shows/search", methods=["POST"])
# TODO search shows
def search_shows():
    search_term = request.form.get("search_term", "")

    shows = [
        {
            "venue_id": show.venue_id,
            "venue_name": Venue.query.get(show.venue_id).name,
            "artist_id": show.artist_id,
            "artist_name": Artist.query.get(show.artist_id).name,
            "artist_image_link": Artist.query.get(show.artist_id).image_link,
            "start_time": str(show.start_time),
        }
        for show in Show.query.all()
    ]

    response = {
        "count": len(shows),
        "data": shows,
    }
    return render_template(
        "pages/search_shows.html", results=response, search_term=search_term,
    )


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
