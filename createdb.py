from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime , timedelta
import pytz
from sqlalchemy import DateTime, event

from __init__ import app
from app_config import *
db = SQLAlchemy(app)




class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(300), unique=True)
    uuid = db.Column(db.String(300), unique=True)
    visited=db.Column(db.Integer, default=None)
    # Add maximum_book_issued column
    maximum_book_issued = db.Column(db.Integer, default=5)  # Adjust the default value as needed
    maximum_book_requested = db.Column(db.Integer, default=5)  # Adjust the default value as needed

    # Add back reference to requested books
    requested_books = db.relationship('BookRequested', backref='user', lazy=True)
    completed_books = db.relationship('CompletedBook', backref='user', lazy=True)

class Manager(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(300), unique=True)
    uuid = db.Column(db.String(300), unique=True)
    books = db.relationship('Book', backref='manager', lazy=True)
    requested_books = db.relationship('BookRequested', backref='manager', lazy=True)
    sections = db.relationship('Section', backref='manager', lazy=True)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('manager.id'), nullable=False)
    books = db.relationship('Book', backref='section', lazy=True)
    created_date = db.Column(DateTime, nullable=False)
    updated_date = db.Column(DateTime, default=None, nullable=True)

    def __init__(self, *args, **kwargs):
        super(Section, self).__init__(*args, **kwargs)
        self.created_date = datetime.now(pytz.timezone('Asia/Kolkata'))

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    ebook = db.Column(db.String(200), nullable=False)
    preview_book = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float,nullable=False)
    rating = db.Column(db.Float,default=0,nullable=False)
    total_rating = db.Column(db.Integer,default=0,nullable=False)
    total_rated_users = db.Column(db.Integer,default=0,nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('manager.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    created_date = db.Column(DateTime, nullable=False)
    updated_date = db.Column(DateTime, default=None, nullable=True)


    def __init__(self, *args, **kwargs):
        super(Book, self).__init__(*args, **kwargs)
        self.created_date = datetime.now(pytz.timezone('Asia/Kolkata'))

class BookRequested(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    ebook = db.Column(db.String(200), nullable=False)
    preview_book = db.Column(db.String(200), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('manager.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    reading_status = db.Column(db.String(20), nullable=False, default='pending')
    created_date = db.Column(DateTime, nullable=False)
    processed_date = db.Column(DateTime, default=None, nullable=True)
    expire_date = db.Column(DateTime, nullable=True)

    def __init__(self, *args, **kwargs):
        super(BookRequested, self).__init__(*args, **kwargs)
        self.created_date = datetime.now(pytz.timezone('Asia/Kolkata'))

class CompletedBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    manager_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    processed_date = db.Column(DateTime, default=None, nullable=True)







    





with app.app_context():
    db.create_all()