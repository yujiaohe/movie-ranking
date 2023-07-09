import os
import ast
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_URL = "https://api.themoviedb.org/3/search/movie"
POSTER_URL = "https://image.tmdb.org/t/p/original"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies-collection.db"
db = SQLAlchemy(app)

# create DB and table Movie
with app.app_context():
    class Movie(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(250), unique=True, nullable=False)
        year = db.Column(db.Integer, nullable=False)
        description = db.Column(db.String(250), nullable=False)
        rating = db.Column(db.Float)
        ranking = db.Column(db.Integer)
        review = db.Column(db.String)
        img_url = db.Column(db.String)

    db.create_all()


class EditForm(FlaskForm):
    rating = FloatField(label="Your Rating Out of 10 e.g. 7.5",
                        validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    for index in range(len(movies)):
        movies[index].ranking = len(movies) - index
        db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    edit_form = EditForm()
    movie_id = request.args.get('id')
    print(movie_id)
    with app.app_context():
        movie_to_update = db.get_or_404(Movie, movie_id)
        if request.method == "POST" and edit_form.validate_on_submit():
            rating = edit_form.rating.data
            review = edit_form.review.data
            movie_to_update.rating = rating
            movie_to_update.review = review
            db.session.commit()
            return redirect(url_for('home'))
    return render_template('edit.html', form=edit_form, movie=movie_to_update)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    with app.app_context():
        movie_to_delete = db.get_or_404(Movie, movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
        return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddForm()
    if request.method == "POST" and add_form.validate_on_submit():
        title = add_form.title.data
        params = {
            "api_key": TMDB_API_KEY,
            "query": title
        }
        response = requests.get(TMDB_URL, params=params)
        query_data = response.json()["results"]
        return render_template('select.html', movies=query_data)
    return render_template('add.html', form=add_form)


@app.route("/insert")
def insert():
    movie_data = request.args.get('movie_data')
    movie_data = ast.literal_eval(movie_data)
    with app.app_context():
        movie_to_insert = Movie(title=movie_data['original_title'],
                                year=movie_data['release_date'].split("-")[0],
                                description=movie_data['overview'],
                                img_url=f"{POSTER_URL}{movie_data['poster_path']}")
        db.session.add(movie_to_insert)
        db.session.commit()
        movie_id = Movie.query.filter_by(
            title=movie_data['original_title']).first().id
    return redirect(url_for('edit', id=movie_id))


if __name__ == '__main__':
    app.run(debug=True)
