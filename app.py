import os

from flask import Flask, session, render_template, request, redirect, flash, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_bcrypt import Bcrypt 

import requests as rq

app = Flask(__name__)


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine("postgres://hdpfrarverqier:90c05be2b1a16cc5e978ab33067f04ce84589012e7e775656c9d3a4482f04531@ec2-50-17-90-177.compute-1.amazonaws.com:5432/d9o64u1gej1c13")
db = scoped_session(sessionmaker(bind=engine))

bycrpt = Bcrypt(app)

app.secret_key = os.urandom(24)


@app.route("/")
def index():
	if 'user_name' in session:
		return redirect(url_for('search'))
	
	return render_template('login.html')



@app.route("/register")
def register():
	return render_template('register.html')


#User login function
@app.route("/login", methods=['POST', 'GET'])
def login():
	if request.method == "POST":
		email = request.form.get('email')
		password = request.form.get('password')

		user = db.execute("SELECT * FROM users WHERE email = :email",
			{"email": email}).fetchone()
		if user and bycrpt.check_password_hash(user.password, password):
			session['user_name'] = email
			return redirect(url_for('search'))

		else:
			flash("Please enter a valid email or password!")
			return redirect(url_for('index'))

	else:
		return redirect(url_for('index'))


@app.route("/new_user", methods = ["POST", "GET"])
def new_user():
	if request.method == "POST":
		name = request.form.get("name")
		email = request.form.get("email")
		password = request.form.get("password")
		users = db.execute("SELECT * FROM users WHERE email = :email",
			{"email": email}).fetchone()
		if users:
			flash("User Already Exist! Please login")
			return redirect(url_for('index'))
		pswd = bycrpt.generate_password_hash(password).decode('utf8')
		db.execute("INSERT INTO users(name, email, password) VALUES (:name, :email, :password)",
			{"name": name, "email": email, "password": pswd})
		db.commit()

		session['user_name'] = email
		return redirect(url_for('search'))


	else:
		return redirect(url_for('index'))

#book search after successfully register or login
@app.route('/search')
def search():
	if 'user_name' in session:
		user = db.execute("SELECT * FROM users WHERE email = :email",
			{"email": session['user_name']}).fetchone()
		return render_template('search.html', user = user)
	else:
		return redirect(url_for('index'))

#Book Search as per user choice
@app.route('/result', methods = ['POST','GET'])
def result():
	if 'user_name' in session:
		isbn = request.args.get('isbn')
		title = request.args.get('title')
		author = request.args.get('author')
		
		if isbn!="" and title!="" and author!="":
			books = db.execute("SELECT * FROM books WHERE isbn = :isbn and title = :title and author = :author",
					{"isbn": isbn, "title": title, "author": author}).fetchall()

			return render_template('result.html', books = books)

		elif isbn!="" and title=="" and author=="":
			books = db.execute("SELECT * FROM books WHERE isbn = :isbn",
					{"isbn": isbn}).fetchall()

			return render_template('result.html', books = books)

		elif isbn=="" and title!="" and author=="":
			books = db.execute("SELECT * FROM books WHERE title = :title",
					{"title": title}).fetchall()

			return render_template('result.html', books = books)

		elif isbn=="" and title=="" and author!="":
			books = db.execute("SELECT * FROM books WHERE author = :author",
					{"author": author}).fetchall()

			return render_template('result.html', books = books)

		elif isbn!="" and title!="" and author=="":
			books = db.execute("SELECT * FROM books WHERE isbn = :isbn and title = :title",
					{"isbn": isbn, "title": title}).fetchall()

			return render_template('result.html', books = books)

		elif isbn!="" and title=="" and author!="":
			books = db.execute("SELECT * FROM books WHERE isbn = :isbn and author = :author",
					{"isbn": isbn, "author": author}).fetchall()

			return render_template('result.html', books = books)

		elif isbn=="" and title!="" and author!="":
			books = db.execute("SELECT * FROM books WHERE title = :title and author = :author",
					{"title": title, "author": author}).fetchall()

			return render_template('result.html', books = books)

		else:
			flash("No book is available!")
			return redirect(url_for('search'))


	else:
		return redirect(url_for('index'))


#Book Details
@app.route('/book/<string:isbn>')
def book(isbn):
	if 'user_name' in session:
		users = db.execute("SELECT * FROM users WHERE email = :email",
			{"email": session['user_name']}).fetchone()
		goodreads = rq.get("https://www.goodreads.com/book/review_counts.json?", params={"key": "o9Tb1ysXo9YVpBTeRmJGw", "isbns": isbn}).json()
		book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
			{"isbn": isbn}).fetchone()

		if book:
			rating = db.execute("SELECT * FROM reviews WHERE book_id = :id",
				{"id": book.book_id}).fetchall()
			goodreads = goodreads["books"]

			presentRating = db.execute("SELECT * FROM reviews WHERE user_id = :id and book_id = :book_id",
				{"id": users.user_id, "book_id": book.book_id}).fetchone()

			return render_template('book.html', book = book, goodreads = goodreads, ratings = rating, presentRating = presentRating)

		else:
			return redirect(url_for('search'))

	else:
		return redirect(url_for('index'))



#submiting user rating
@app.route('/rating', methods=['POST', 'GET'])
def rating():
	if 'user_name' in session and request.method == 'POST':
		rating = request.form.get('rating')
		book_id = request.form.get('book_id')
		comment = request.form.get('comment')
		user = db.execute("SELECT * FROM users WHERE email = :email",
			{"email": session['user_name']}).fetchone()
		book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
			{"isbn": book_id}).fetchone()

		db.execute("INSERT INTO reviews (rating, book_id, user_id, comment) VALUES (:rating, :book_id, :user, :comment)",
			{"rating": rating, "book_id": book.book_id, "user": user.user_id, "comment": comment})

		db.commit()
		flash("Thank you for rate this book!")
		return redirect(f'/book/{book_id}')

	else:
		return redirect('index')


#User logout function
@app.route('/logout')
def logout():
	if 'user_name' in session:
		session.pop('user_name')
		return redirect(url_for('index'))
	else:
		return redirect(url_for('index'))


#API
@app.route('/api-doc')
def application():
	if 'user_name' in session:
		return render_template('api.html')

#API (Application Programming Interface)
@app.route('/api/<string:isbn>')
def api(isbn):
	if 'user_name' in session:
		book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
			{"isbn": isbn}).fetchone()

		if book is None:
			return jsonify({"error": "Invalid flight id"}), 422

		review_count = db.execute("SELECT count(*) FROM reviews WHERE book_id = :id",
			{"id": book.book_id}).scalar()
		average_score = db.execute("SELECT AVG(CAST(rating AS INTEGER)) FROM reviews WHERE book_id = :id",
			{"id": book.book_id}).scalar()

		return jsonify({
			"isbn": book.isbn,
			"title": book.title,
			"author": book.author,
			"year": book.year,
			"review_count": review_count,
			"average_score": str(average_score)[:4]
			})


if __name__ == '__main__':
	app.run(debug = True)