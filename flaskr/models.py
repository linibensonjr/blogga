from turtle import title
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
try:
    from app import app as app
except:
    from __main__ import app

db = SQLAlchemy(app)

class Blog(db.Model):
    __tablename__ = "Blog"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_published = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f"<Blog {self.id} {self.title}>"


class User(db.Model, UserMixin):
    __tablename__ = "User"

    id = db.Column(db.Integer(), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.Text(), nullable=False)

    def __repr__(self):
        return f"User <{self.first_name}>"


db.create_all()