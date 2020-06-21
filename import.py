import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgres://hdpfrarverqier:90c05be2b1a16cc5e978ab33067f04ce84589012e7e775656c9d3a4482f04531@ec2-50-17-90-177.compute-1.amazonaws.com:5432/d9o64u1gej1c13")
db = scoped_session(sessionmaker(bind = engine))

def main():
	f = open('books.csv')
	reader = csv.reader(f)

	for isbn, title, author, year in reader:
		db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
			{"isbn": isbn, "title": title, "author": author, "year": year})

	db.commit()

if __name__ == '__main__':
	main()