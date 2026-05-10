from flask import Flask, render_template, redirect, url_for, flash, session
from flask import request
import requests
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie_ratings.db"
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db = SQLAlchemy(app)

# DATABASE CLASSES
class User(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable= False)
    password = db.Column(db.String(200), nullable= False)

    ratings = db.relationship("Rating", back_populates="user") 

class Movie(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    imdb_id = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)

    ratings = db.relationship("Rating", back_populates="movie")

class Rating(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movie.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date_rated = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates= "ratings")
    movie = db.relationship("Movie", back_populates= "ratings")  


# user login function
def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()

    if not user:
        return False
    
    if check_password_hash(user.password, password):
        return True
    else:
        return False

# Create tables
with app.app_context():
    db.create_all()

# start page
@app.route('/')
def home():
    return render_template('index.html')

#login page
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if authenticate_user(username, password):
            session['username'] = username 
            return redirect(url_for('userhome'))
        else:
            flash("WRONG")
            
    return render_template('login.html')

# register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    #Processing
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # check for existing usernames
        if User.query.filter_by(username=username).first():
            flash("username already exists")
            return redirect(url_for("register"))

        # create new account
        hashed_pass = generate_password_hash(password, method="pbkdf2:sha256") # encrypt password 
        new_user = User(username=username, password=hashed_pass) # new user object
        db.session.add(new_user) # add user to database
        db.session.commit() # saves user to database

        return redirect(url_for("login"))
    
    return render_template('register.html')

# user home
@app.route('/userhome', methods=['GET', 'POST'])
def userhome():
    username = session.get('username', 'Guest') # get user from session
    movies = None # creates initial search results
    # processing
    if request.method == 'POST':
        # get query
        movie_query = request.form.get("movie_query")
        print(f"search for: {movie_query}") #DEBUG
        if movie_query:
            url = f"http://www.omdbapi.com/?apikey={os.environ.get('OMDB_API_KEY')}&s={movie_query}"
            print(f"API URL: {url}")

            # query results 
            response = requests.get(url)
            data = response.json()
            print(f"API Response: {data}") #DEBUG

            # processing results
            if data.get("Response") == "True": # search is in API
                movies = data["Search"] # put search into movies
    return render_template('userhome.html', username=username, movies=movies)

@app.route('/rate_movie', methods=['GET','POST'])
def rate_movie():
    return render_template('rate_movie.html')


if __name__ == '__main__':
    app.run(debug=False)