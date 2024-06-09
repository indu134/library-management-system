from flask import Flask, request,render_template,send_from_directory
from flask_mail import Mail, Message
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from celery import Celery
from flask_caching import Cache
import uuid 
import werkzeug
import PyPDF2
import base64
from flask_cors import CORS 
import jwt
from datetime import datetime, timedelta
import pytz
import os
import random
import string
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
from io import BytesIO
from __init__ import app
from app_config import *
from createdb import User,Manager,Book,BookRequested,Section,CompletedBook,db
from celery.schedules import crontab

api = Api(app)
CORS(app)
mail = Mail(app)
cache = Cache(app)

celery = Celery(
    'app',
    backend=app.config['RESULT_BACKEND'],
    broker=app.config['CELERY_BROKER_URL'],
    timezone='Asia/Kolkata'
)

celery.conf.update(app.config)

celery.conf.timezone = 'Asia/Kolkata'

celery.conf.beat_schedule = {
    'run-monthly-reports': {
        'task': 'app.generate_and_send_monthly_reports',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    },
    'run-monthly-reports_user': {
        'task': 'app.generate_and_send_monthly_reports_user',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
    },
    'send-visit-site-reminder': {
        'task': 'app.send_visit_site_reminder',
        'schedule': crontab(hour=18, minute=00),
    },
}

def send_revocation_email(user_email,username,title,author):
    subject = 'Book Access Revoked'
    body = f"Dear {username},\n\nYour access to the book '{title}' by {author} has been revoked.\n\n"
    msg = Message(subject, recipients=[user_email])
    msg.body = body + "Thank you.\n"
    mail.send(msg)

ALLOWED_EXTENSIONS_PDF = {'pdf'}
ALLOWED_EXTENSIONS_PHOTO = {'png','jpg','jpeg','webp'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@celery.task
def send_visit_site_reminder():
    with app.app_context():
        users_to_remind = User.query.filter(User.visited == None).all()   # Fetch users with 'visited' field not set
        users_visited =  User.query.filter(User.visited == 1).all()
        
        for user in users_to_remind:
            send_visit_site_email(user)
        for user in users_visited:
            user.visited = None
        db.session.commit()

def send_visit_site_email(user):
    msg = Message(subject="Reminder: Visit Our Site", recipients=[user.email])
    msg.body = f"Dear {user.username},\n\nWe noticed that you haven't visited our site yet, Please visit our site. \n\nThank You. \n"
    mail.send(msg)

@celery.task
def revoke_book_access( book_request_id):
    with app.app_context():
        book_request = BookRequested.query.get(book_request_id)
        if book_request and book_request.status == 'accepted':
            book_request.status = 'revoked'
            user = User.query.get(book_request.user_id)
            user.maximum_book_issued += 1
            subject = 'Book Access Revoked'
            body = f"Dear {user.username},\n\nYour access to the book '{book_request.title}' by {book_request.author} has been revoked.\n\nThank you.\n"
            msg = Message(subject, recipients=[user.email])
            msg.body = body
            mail.send(msg)
            db.session.commit()

def extract_first_10_pages(pdf_path, output_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Create a writer object for output
        pdf_writer = PyPDF2.PdfWriter()
        
        # Add first 10 pages to the writer
        for page_num in range(min(10, len(pdf_reader.pages))):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        
        # Write the pages to a new PDF file
        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)



def token_required(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token or len(token.split(" ")) != 2:
            return {'message': 'Invalid token format'}, 401

        try:
            # Verify the token
            data = jwt.decode(token.split(" ")[1], app.config['SECRET_KEY'], algorithms=['HS256'])
            #username = data.get('username', None)
            current_user = User.query.filter_by(username=data['username'],uuid=data['unique_id']).first()
        except jwt.ExpiredSignatureError:
            return {'message': 'Token has expired'}, 401
        except jwt.InvalidTokenError as e:
            return {'message': 'Invalid token', 'error': str(e), 'token': token}, 401

        return f(current_user=current_user,*args, **kwargs)

    return wrapper


def token_required_m(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token or len(token.split(" ")) != 2:
            return {'message': 'Invalid token format'}, 401

        try:
            # Verify the token
            data = jwt.decode(token.split(" ")[1], app.config['SECRET_KEY'], algorithms=['HS256'])
            #username = data.get('username', None)
            current_user = Manager.query.filter_by(username=data['username'],uuid=data['unique_id']).first()
        except jwt.ExpiredSignatureError:
            return {'message': 'Token has expired'}, 401
        except jwt.InvalidTokenError as e:
            return {'message': 'Invalid token', 'error': str(e), 'token': token}, 401

        return f(current_user=current_user,*args, **kwargs)

    return wrapper




class UserResource(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('username', type=str, help='Username is required', required=True)
            parser.add_argument('email', type=str, help='Email is required', required=True)
            parser.add_argument('password', type=str, help='Password is required', required=True)
            args = parser.parse_args()

            # Hash the password before saving to the database
            hashed_password = generate_password_hash(args['password'], method='pbkdf2:sha256')

            new_user = User(username=args['username'], email=args['email'], password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            return {'message': 'User created successfully'}, 201
        except:
            return {'message': 'something went wrong'},500

class UserLogin(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, help='Username is required', required=True)
        parser.add_argument('password', type=str, help='Password is required', required=True)
        args = parser.parse_args()

        user = User.query.filter_by(username=args['username']).first()
        

        if user and check_password_hash(user.password, args['password']):
            user.uuid = str(uuid.uuid4())
            payload = {
            'username': user.username,
            'unique_id': user.uuid 
                                        }
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            user.token = token
            user.visited = 1
            db.session.commit()
            return {'message': 'Login successful', 'token': token}, 200
        else:
            return {'message': 'Invalid credentials'}, 401
        

class ManagerLogin(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, help='Username is required', required=True)
        parser.add_argument('password', type=str, help='Password is required', required=True)
        args = parser.parse_args()

        user = Manager.query.filter_by(username=args['username']).first()
        

        if user and check_password_hash(user.password, args['password']):
            user.uuid = str(uuid.uuid4())
            payload = {
            'username': user.username,
            'unique_id': user.uuid  # Generate a unique identifier
                                        }
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            user.token = token
            db.session.commit()
            return {'message': 'Login successful', 'token': token}, 200
        else:
            return {'message': 'Invalid credentials'}, 401
        



def generate_filename():
    timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y%m%d%H%M%S')
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return f"{timestamp}_{random_string}"

class BookListResource(Resource):
    @token_required_m
    def get(self, current_user):
        books = Book.query.filter_by(manager=current_user).all()
        book_list = [{'id': book.id, 'title': book.title, 'author': book.author, 'image': book.image, 'price': book.price} for book in books]
        return {'books': book_list}

    @token_required_m
    def post(self, current_user):
        parser = reqparse.RequestParser()
        parser.add_argument('photo', type=werkzeug.datastructures.FileStorage, location='files',required=True, help='Input file (photo)')
        parser.add_argument('ebook', type=werkzeug.datastructures.FileStorage, location='files',required=True, help='Input file (ebook)')
        parser.add_argument('price', type=float, required=True, help='Price of the book', location='form')
        parser.add_argument('title', type=str, required=True, help='Title of the book', location='form')
        parser.add_argument('author', type=str, required=True, help='Author of the book', location='form')
        parser.add_argument('section', type=str, required=True, help='Section of the book', location='form')
        args = parser.parse_args()
        # Save the uploaded photo and ebook
        if allowed_file(args['photo'].filename, ALLOWED_EXTENSIONS_PHOTO):
            filename_photo = secure_filename(args['photo'].filename)
            photo_url = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], generate_filename() + '_' + filename_photo)
            args['photo'].save(photo_url)
        else:
            return {'message':'bad file extension(photo)'},400
        if allowed_file(args['ebook'].filename, ALLOWED_EXTENSIONS_PDF):
            filename_ebook = secure_filename(args['ebook'].filename)
            ebook_url = os.path.join(app.config['UPLOADED_EBOOKS_DEST'], generate_filename() + '_' + filename_ebook)
            args['ebook'].save(ebook_url)
            preview_book_url = os.path.join(app.config['UPLOADED_PRE_EBOOKS_DEST'], generate_filename() + '_' + 'PRE'+'_'+filename_ebook)
            extract_first_10_pages(ebook_url,preview_book_url)
        else:
            return {'message': 'bad file extension(ebook)'},400

        # Check if the section exists
        section = Section.query.filter_by(name=args['section']).first()
        if not section:
            return {'message': 'Section not found'}

        # Create a new book entry
        new_book = Book(
            title=args['title'],
            author=args['author'],
            image=photo_url,
            ebook=ebook_url,
            preview_book =  preview_book_url,
            price=args['price'],
            manager=current_user,
            section_id=section.id
        )

        db.session.add(new_book)
        db.session.commit()

        return {
            'message': 'Book added successfully',
            'book': {
                'id': new_book.id,
                'title': new_book.title,
                'author': new_book.author,
                'image': new_book.image,
                'ebook': new_book.ebook,
                'price': new_book.price
            }
        }, 201

class BookResource(Resource):
    @token_required_m
    def get(self, current_user, book_id):
        book_id = int(book_id)
        book = Book.query.filter_by(id=book_id, manager=current_user).first()

        if not book:
            return {'message': f'Book with id {book_id} not found or does not belong to the current user'}, 404

        return {'book': {'id': book.id, 'title': book.title, 'author': book.author,'section':Section.query.filter_by(id=book.section_id).first().name,
                          'image': book.image, 'price': book.price}}

    @token_required_m
    def put(self, current_user, book_id):
        book_id = int(book_id)
        book = Book.query.filter_by(id=book_id, manager=current_user).first()

        if not book:
            return {'message': f'Book with id {book_id} not found or does not belong to the current user'}, 404
        parser = reqparse.RequestParser()
        parser.add_argument('photo', type=werkzeug.datastructures.FileStorage, location='files', help='Input file (photo)')
        parser.add_argument('ebook', type=werkzeug.datastructures.FileStorage, location='files', help='Input file (ebook)')
        parser.add_argument('price', type=float, help='Price of the book',location="form")
        parser.add_argument('title', type=str, help='Title of the book',location="form")
        parser.add_argument('author', type=str, help='Author of the book',location="form")
        parser.add_argument('section', type=str, help='Section of the book',location="form")

        args = parser.parse_args()
        if args.get('section'):
            section = Section.query.filter_by(name=args['section']).first()
            if not section :
                 return {'message' : 'Section not found'},404
            book.section_id = section.id


        # Update book details
        if args.get('photo'):
            if allowed_file(args['photo'].filename, ALLOWED_EXTENSIONS_PHOTO):
                filename = secure_filename(args['photo'].filename)
                photo_url = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], generate_filename() + '_' + filename)
                args['photo'].save(photo_url)
                os.remove(book.image)
                book.image = photo_url
            else:
                {"message":"bad file extension(photo)"},400
        if args.get('ebook'):
            if allowed_file(args['ebook'].filename, ALLOWED_EXTENSIONS_PDF):
                filename_ebook = secure_filename(args['ebook'].filename)
                ebook_url = os.path.join(app.config['UPLOADED_EBOOKS_DEST'], generate_filename() + '_' + filename_ebook)
                args['ebook'].save(ebook_url)
                preview_book_url = os.path.join(app.config['UPLOADED_PRE_EBOOKS_DEST'], generate_filename() + '_' + 'PRE'+'_'+filename_ebook)
                extract_first_10_pages(ebook_url,preview_book_url)
                os.remove(book.preview_book)
                os.remove(book.ebook)
                book.ebook = ebook_url
                book.preview_book = preview_book_url
            else:
                {"message":"bad file extension(ebook)"},400
           

        book.title = args.get('title') or book.title
        book.author = args.get('author') or book.author
        book.price = args.get('price') or book.price
        book.updated_date = datetime.now(pytz.timezone('Asia/Kolkata'))

        db.session.commit()

        return {'message': f'Book {book_id} updated successfully', 'book': {'id': book.id, 'title': book.title, 'author': book.author, 'image': book.image, 'price': book.price}},200

    @token_required_m
    def delete(self, current_user, book_id):
        book_id = int(book_id)
        book = Book.query.filter_by(id=book_id, manager=current_user).first()

        if not book:
            return {'message': f'Book with id {book_id} not found or does not belong to the current user'}, 404
        os.remove(book.image)
        os.remove(book.ebook)
        os.remove(book.preview_book)
        db.session.delete(book)
        db.session.commit()

        return {'message': f'Book {book_id} deleted successfully', 'book': {'id': book.id, 'title': book.title, 'author': book.author, 'image': book.image, 'price': book.price}}
    

def send_book_request_notification(recipient, username, book_title, book_author, expire_date, action):
    if action == 'accepted':
        subject = 'Book Request Accepted'
        body = f"Dear {username},\n\nYour book request for '{book_title}' by {book_author} has been accepted.\n\n"
        body += f"The book will expire on {expire_date.strftime('%Y-%m-%d')}.\n\n"
    elif action == 'rejected':
        subject = 'Book Request Rejected'
        body = f"Dear {username},\n\nYour book request for '{book_title}' by {book_author} has been rejected.\n\n"
    else:
        return

    msg = Message(subject, recipients=[recipient])
    msg.body = body + "Thank you.\n"
    mail.send(msg)

class BookRequestResource(Resource):
    @token_required_m
    def get(self, current_user):
        requests = BookRequested.query.filter_by(manager_id=current_user.id,status='pending').all()
        requested_books = [ {'id': request.id,
                             'title': request.title,
                             'image':request.image,
                             'user': User.query.get(request.user_id).username,
                             'userbooklimit':User.query.get(request.user_id).maximum_book_issued,
                             'author': request.author,
                             'status': request.status} 
                             for request in requests]
        return {'book_requests': requested_books}

    @token_required_m
    def post(self, current_user):
        parser = reqparse.RequestParser()
        parser.add_argument('book_id', type=int, help='Book ID is required', required=True)
        parser.add_argument('action', type=str, help='Action is required (accept/reject)', required=True)
        args = parser.parse_args()

        # Check if the book request exists
        book_request = BookRequested.query.filter_by(id=args['book_id'], manager_id=current_user.id).first()
        if not book_request:
            return {'message': 'Book request not found'}, 404
        user = User.query.filter_by(id=book_request.user_id).first()

        if args['action'] == 'accept':
            # Accept the book request
            if book_request and book_request.status == 'pending':
                # Update the book request status to 'accepted'
                book_request.status = 'accepted'
                if book_request.reading_status == 'pending':
                    book_request.reading_status = 'reading'
                user.maximum_book_issued -= 1
                user.maximum_book_requested += 1
                book_request.processed_date = datetime.now(pytz.timezone('Asia/Kolkata'))
                book_request.expire_date = book_request.processed_date + timedelta(days=7)
                send_book_request_notification(user.email, user.username, book_request.title, book_request.author, book_request.expire_date, action='accepted')
                revoke_book_access.apply_async(args=[book_request.id], eta=book_request.expire_date)
                db.session.commit()
                return {'message': 'Book request accepted successfully'}, 200
            else:
                return {'message': 'Book request not found or already processed'}, 400

        elif args['action'] == 'reject':
            # Reject the book request
            if book_request and book_request.status == 'pending':
                # Update the book request status to 'rejected'
                book_request.status = 'rejected'
                user.maximum_book_requested += 1
                book_request.processed_date = datetime.now(pytz.timezone('Asia/Kolkata'))
                send_book_request_notification(user.email, user.username, book_request.title, book_request.author, None, action='rejected')
                db.session.commit()
                return {'message': 'Book request rejected successfully'}, 200
            else:
                return {'message': 'Book request not found or already processed'}, 400

        else:
            return {'message': 'Invalid action'}, 400
class AcceptedBooksResource(Resource):
    @token_required_m
    def get(self, current_user):
        accepted_requests = BookRequested.query.filter_by(manager_id=current_user.id, status='accepted').all()
        accepted_books = [{
            'id': request.id,
            'title': request.title,
            'author': request.author,
            'user': User.query.get(request.user_id).username,
            'userbooklimit':User.query.get(request.user_id).maximum_book_issued,
            'image': request.image,
            'status': request.status,
            'expires':request.expire_date.strftime("%d-%m-%Y %H:%M"),
        } for request in accepted_requests]
        return {'accepted_books': accepted_books}
class RevokeBookResource(Resource):
    @token_required_m
    def post(self, current_user):
        parser = reqparse.RequestParser()
        parser.add_argument('book_id', type=int, help='Book ID is required', required=True)
        args = parser.parse_args()

        book_request = BookRequested.query.filter_by(id=args['book_id'], manager_id=current_user.id, status='accepted').first()
        user = User.query.get(book_request.user_id)

        if book_request:
            # Update the book request status to 'revoked'
            book_request.status = 'revoked'
            user.maximum_book_issued += 1
            send_revocation_email(user.email,user.username,book_request.title,book_request.author)
            db.session.commit()
            return {'message': 'Book request revoked successfully'}, 200
        else:
            return {'message': 'Book request not found or not accepted'}, 400
        
class AllBooksResource(Resource):
    @cache.cached(timeout=30) 
    @token_required
    def get(self, current_user):
        books = Book.query.all()
        all_books = [{
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'image': book.image,
            'price': book.price,
            'rating':book.rating,
            'section': Section.query.filter_by(id=book.section_id).first().name,
            "number_of_users" :book.total_rated_users,
        } for book in books]
        return {'books': all_books}
class RequestBookResource(Resource):
    @token_required
    def post(self, current_user):
        parser = reqparse.RequestParser()
        parser.add_argument('book_id', type=int, help='Book ID is required', required=True)
        args = parser.parse_args()

        book = Book.query.get(args['book_id'])
        if current_user.maximum_book_requested <= 0:
            return {'message' : 'user exceeded request limit'},400

        if not book:
            return {'message': 'Book not found'}, 404

        # Check if the user has already requested the book
        existing_request = BookRequested.query.filter_by(title=book.title,author=book.author,manager_id=book.manager_id, user_id=current_user.id,section_id=book.section_id).first()
        if existing_request:
            if existing_request.status=='pending':
                return {'message': 'Book already requested'}, 400
        completed = CompletedBook.query.filter_by(book_id=book.id,user_id=current_user.id,section_id=book.section_id).first()
        if completed:
            reading_status='completed'
        else:
            reading_status='pending'

        # Create a new book request
        new_request = BookRequested( user_id=current_user.id,title=book.title,image=book.image,author=book.author, manager_id=book.manager_id,ebook=book.ebook,preview_book=book.preview_book,reading_status=reading_status,section_id = book.section_id)
        current_user.maximum_book_requested -= 1
        db.session.add(new_request)
        db.session.commit()

        return {'message': 'Book requested successfully'}, 201
class RequestedBooksResource(Resource):
    @token_required
    def get(self, current_user):
        requests = BookRequested.query.filter_by(user_id=current_user.id,status='pending').all()
        requested_books = [{
            'id': request.id,
            'title': request.title,
            'author': request.author,
            'image': request.image,
            'status': request.status
        } for request in requests]
        return {'requested_books': requested_books}
class DeleteRequestResource(Resource):
    @token_required
    def post(self, current_user):
        parser = reqparse.RequestParser()
        parser.add_argument('book_id', type=int, help='Book ID is required', required=True)
        args = parser.parse_args()

        book_request = BookRequested.query.filter_by(id=args['book_id'], user_id=current_user.id).first()

        if book_request:
            if book_request.status in ['accepted', 'rejected', 'revoked']:
                return {'message': 'Book request cannot be deleted as it is already processed'}, 400
            current_user.maximum_book_requested += 1
            db.session.delete(book_request)
            db.session.commit()
            return {'message': 'Book request deleted successfully'}, 200
        else:
            return {'message': 'Book request not found or not requested by current user'}, 404
class AcceptedBooksResourceUser(Resource):
    @token_required
    def get(self, current_user):
        requests = BookRequested.query.filter_by(user_id=current_user.id, status='accepted').all()
        accepted_books = [{
            'id': request.id,
            'title': request.title,
            'author': request.author,
            'image': request.image,
            'status': request.status,
            'reading_status':request.reading_status,
            'expires':request.expire_date.strftime("%d-%m-%Y %H:%M"),
        } for request in requests]
        return {'accepted_books': accepted_books}
class RejectedBooksResourceUser(Resource):
    @token_required
    def get(self, current_user):
        requests = BookRequested.query.filter_by(user_id=current_user.id, status='rejected').all()
        rejected_books = [{
            'id': request.id,
            'title': request.title,
            'author': request.author,
            'image': request.image,
            'status': request.status
        } for request in requests]
        return {'rejected_books': rejected_books}
class RevokedBooksResourceUser(Resource):
    @token_required
    def get(self, current_user):
        requests = BookRequested.query.filter_by(user_id=current_user.id, status='revoked').all()
        revoked_books = [{
            'id': request.id,
            'title': request.title,
            'author': request.author,
            'image': request.image,
            'status': request.status
        } for request in requests]
        return {'revoked_books': revoked_books}
class ManagerRejectedBooksResource(Resource):
    @token_required_m
    def get(self, current_user):
        requests = BookRequested.query.filter_by(manager_id=current_user.id,status='rejected').all()
        rejected_books = [{
            'id': request.id,
            'title': request.title,
            'author': request.author,
            'image': request.image,
            'status': request.status,
            'user': User.query.get(request.user_id).username,
            'userbooklimit':User.query.get(request.user_id).maximum_book_issued,
        } for request in requests]
        return {'rejected_books': rejected_books}
class ManagerRevokedBooksResource(Resource):
    @token_required_m
    def get(self, current_user):

        requests = BookRequested.query.filter_by(manager_id = current_user.id,status='revoked').all()
        revoked_books = [{
            'id': request.id,
            'title': request.title,
            'author': request.author,
            'image': request.image,
            'status': request.status,
            'user': User.query.get(request.user_id).username,
            'userbooklimit':User.query.get(request.user_id).maximum_book_issued,
        } for request in requests]
        return {'revoked_books': revoked_books}
class AddSectionResource(Resource):
    @token_required_m
    def post(self,current_user):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='Section name is required', required=True)
        args = parser.parse_args()

        new_section = Section(name=args['name'],manager_id=current_user.id)
        db.session.add(new_section)
        db.session.commit()

        return {'message': 'Section added successfully'}, 201
class SectionsResource(Resource):
    @token_required_m
    def get(self,current_user):
        sections = Section.query.filter_by(manager_id=current_user.id).all()
        formatted_sections = [{'id': section.id, 'name': section.name, 'books': [{'id': book.id, 'title': book.title, 'author': book.author, 'image': book.image, 'price': book.price} for book in section.books]} for section in sections]
        return {'sections': formatted_sections}, 200
    
class SectionResourceSingle(Resource):
    @token_required_m
    def get(self, current_user ,section_id):
        section = Section.query.filter_by(id=section_id,manager_id=current_user.id).first()
        if not section:
            return {'message': 'Section not found'}, 404
        section_data = {
            'id': section.id,
            'name': section.name,
        }
        return {'section': section_data}, 200
    @token_required_m
    def delete(self,current_user, section_id):
        section = Section.query.filter_by(id=section_id,manager_id=current_user.id).first()
        if not section:
            return {'message': 'Section not found'}, 404
        
        # Delete the section
        for book in section.books:
            os.remove(book.image)
            os.remove(book.ebook)
            os.remove(book.preview_book)
            db.session.delete(book)
        db.session.delete(section)
        db.session.commit()
        
        return {'message': 'Section deleted successfully'}, 200
    

class SubmitRating(Resource):
    @token_required
    def post(self, current_user):
        parser = reqparse.RequestParser()
        parser.add_argument('book_id', type=int, help='Book ID is required', required=True)
        parser.add_argument('rating', type=float, help='Rating value is required', required=True)
        args = parser.parse_args()

        bookrequest = BookRequested.query.filter_by(id=args['book_id'],user_id=current_user.id).first()

        if not bookrequest:
            return {'message': 'Book not found'}, 404
        book = Book.query.filter_by(title=bookrequest.title,manager_id=bookrequest.manager_id,author=bookrequest.author,section_id=bookrequest.section_id).first()
        if not book:
            return {'message': 'Book not found'}, 404


        current_total_rating = book.total_rating
        current_total_rated_users = book.total_rated_users

        new_total_rating = current_total_rating + args['rating']
        new_total_rated_users = current_total_rated_users + 1

        new_rating = new_total_rating / new_total_rated_users

        book.rating = new_rating
        book.total_rating = new_total_rating
        book.total_rated_users = new_total_rated_users

        try:
            db.session.commit()
            return {'message': 'Rating submitted successfully'}, 200

        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 500

def send_congratulations_email(recipient, user_name, book_title, book_author, processed_date):
    msg = Message('Congratulations!', recipients=[recipient])
    #msg.body = "Congratulations! You have successfully marked a book as completed."
    msg.html = render_template('book_complete_mail.html', 
                               user_name=user_name,
                               book_title=book_title,
                               book_author=book_author,
                               processed_date=processed_date)
    mail.send(msg)
class MarkAsCompletedResource(Resource):

    @token_required  # Implement your token_required decorator
    def post(self, current_user):
        parser = reqparse.RequestParser()
        parser.add_argument('book_id', type=int, help='Book ID is required', required=True)
        args = parser.parse_args()

        # Retrieve the book
        bookrequest = BookRequested.query.get(args['book_id'])
        if not bookrequest:
            return {'message': 'Book not found'}, 404
        book = Book.query.filter_by(title=bookrequest.title,author=bookrequest.author,manager_id=bookrequest.manager_id,section_id=bookrequest.section_id).first()


        if not book:
            return {'message': 'Book not found'}, 404

        # Check if the book is already marked as completed by the user
        existing_completed_book = CompletedBook.query.filter_by(book_id=book.id, user_id=current_user.id,section_id=book.section_id).first()
        if existing_completed_book:
            return {'message': 'Book already marked as completed'}, 400

        # Mark the book as completed for the user
        completed_book = CompletedBook(book_id=book.id, manager_id=book.manager_id,user_id=current_user.id,section_id=book.section_id)
        bookrequest.reading_status = 'completed'
        completed_book.processed_date =  datetime.now(pytz.timezone('Asia/Kolkata'))
        db.session.add(completed_book)
        send_congratulations_email(current_user.email,current_user.username,bookrequest.title,bookrequest.author,completed_book.processed_date.strftime("%d-%m-%Y %H:%M"))
        db.session.commit()
        return {'message': 'Book marked as completed successfully'}, 200
    
class CompletedBooksResourceUser(Resource):
    @token_required
    def get(self, current_user):
        completed_book_ids = CompletedBook.query.filter_by(user_id=current_user.id).all()
        completed_books = []
        for completed_book_id in completed_book_ids:
            book = Book.query.get(completed_book_id.book_id)
            if book:
                completed_books.append({
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'image': book.image,
                    'reading_status': 'Completed',
                })

        return {'completed_books': completed_books}
    


class ManagerBookDistributionResource(Resource):
    @token_required_m
    def get(self,current_user):
        section_distribution = {}
        sections = Section.query.all()
        for section in sections:
            section_distribution[section.name] = Book.query.filter_by(manager_id=current_user.id,section_id=section.id).count()
        return section_distribution

class ManagerUserReadingStatusResource(Resource):
    @token_required_m
    def get(self,current_user):
        user_reading_status = {
            'Reading': BookRequested.query.filter_by(manager_id=current_user.id,reading_status='reading').count(),
            'Completed': CompletedBook.query.filter_by(manager_id=current_user.id).count(),
        }
        return user_reading_status

class ManagerRequestStatusResource(Resource):
    @token_required_m
    def get(self,current_user):
        request_statuses = {
            'Approved': BookRequested.query.filter_by(manager_id=current_user.id, status='accepted').count()+BookRequested.query.filter_by(manager_id=current_user.id, status='revoked').count()+BookRequested.query.filter_by(manager_id=current_user.id, status='returnted').count(),
            'Rejected': BookRequested.query.filter_by(manager_id=current_user.id,status='rejected').count(),
            'Pending': BookRequested.query.filter_by(manager_id=current_user.id,status='pending').count()
        }
        return request_statuses

class ManagerCompletedBookDistributionResource(Resource):
    @token_required_m
    def get(self,current_user):
        completed_book_distribution = {}
        completed_books = CompletedBook.query.filter_by(manager_id=current_user.id).all()
        for completed_book in completed_books:
            date_str = completed_book.processed_date.strftime('%Y-%m-%d')
            if date_str in completed_book_distribution:
                completed_book_distribution[date_str] += 1
            else:
                completed_book_distribution[date_str] = 1
        return completed_book_distribution
    
class ReturnBook(Resource):
    @token_required
    def post(self, current_user):
        parser = reqparse.RequestParser()
        parser.add_argument('book_id', type=int, help='Book ID is required', required=True)
        args = parser.parse_args()

        book_request = BookRequested.query.filter_by(id=args['book_id'], user_id=current_user.id).first()

        if not book_request:
            return {'message': 'Book request not found'}, 404

        if book_request.status != 'accepted':
            return {'message': 'Book is not accepted or already returned'}, 400

        # Update book request status to 'returned'
        book_request.status = 'returned'
        current_user.maximum_book_issued += 1

        try:
            db.session.commit()
            return {'message': 'Book returned successfully'}, 200

        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 500




class UserDetailResource(Resource):
    @token_required
    def get(self, current_user):
        user_details = {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'maximum_book_issued': current_user.maximum_book_issued,
            'maximum_book_requested': current_user.maximum_book_requested,
        }
        return user_details







api.add_resource(BookListResource, '/api/books')
api.add_resource(BookResource, '/api/books/<int:book_id>')
api.add_resource(UserResource, '/api/register')
api.add_resource(UserLogin, '/api/login')
api.add_resource(ManagerLogin,'/api/managerlogin')
api.add_resource(BookRequestResource, '/api/book-requests')
api.add_resource(AcceptedBooksResource, '/api/accepted-books')
api.add_resource(RevokeBookResource, '/api/revoke-book')
api.add_resource(AllBooksResource, '/api/all-books')
api.add_resource(RequestBookResource, '/api/request-book')
api.add_resource(RequestedBooksResource, '/api/requested-books')
api.add_resource(DeleteRequestResource, '/api/delete-request')
api.add_resource(AcceptedBooksResourceUser, '/api/user/accepted-books')
api.add_resource(RejectedBooksResourceUser, '/api/user/rejected-books')
api.add_resource(RevokedBooksResourceUser, '/api/user/revoked-books')
api.add_resource(ManagerRejectedBooksResource, '/api/manager/rejected-books')
api.add_resource(ManagerRevokedBooksResource, '/api/manager/revoked-books')
api.add_resource(AddSectionResource, '/api/add-section')
api.add_resource(SectionsResource, '/api/sections')
api.add_resource(SectionResourceSingle, '/api/sections/<int:section_id>')
api.add_resource(SubmitRating,'/api/submit-rating')
api.add_resource(MarkAsCompletedResource,'/api/mark-as-completed')
api.add_resource(CompletedBooksResourceUser,'/api/user/completed-books')

api.add_resource(ManagerBookDistributionResource, '/api/manager/book-distribution')
api.add_resource(ManagerUserReadingStatusResource, '/api/manager/user-reading-status')
api.add_resource(ManagerRequestStatusResource, '/api/manager/request-status')
api.add_resource(ManagerCompletedBookDistributionResource, '/api/manager/completed-book-distribution')

api.add_resource(ReturnBook, '/api/return-book')
api.add_resource(UserDetailResource, '/api/userdetails')












@app.route('/')
def login():
    return render_template("UserLogin.html")
@app.route('/dashBoard')
def dashboard():
    return render_template("UserDashBoard.html")
@app.route('/managerLogin')
def managerLogin():
    return render_template("ManagerLogin.html")
@app.route('/managerDashBoard')
def managerDashBoard():
    return render_template("ManagerDashBoard.html")

@app.route('/<int:id>')
def preview(id):
    external_folder = 'Uploades/preview_books'
    book = Book.query.filter_by(id=id).first()
    filename = book.preview_book.split("/")[2]
    # Use send_from_directory to send the file
    return send_from_directory(external_folder, filename)
@app.route('/user/<token>/<int:id>')
def read_book(token,id):
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        current_user = User.query.filter_by(username=data['username'],uuid=data['unique_id']).first()
    except jwt.ExpiredSignatureError:
        return {'message': 'Token has expired'}, 401
    except jwt.InvalidTokenError as e:
        return {'message': 'Invalid token', 'error': str(e), 'token': token}, 401
    if current_user:
        external_folder = 'Uploades/books'
        book = BookRequested.query.filter_by(id=id,user_id=current_user.id,status='accepted').first()
        if book:
            filename = book.ebook.split("/")[2]
            return send_from_directory(external_folder, filename) 
        else:
            return {"message": "Book Not Found"},404
    else:
        return {"message" : "Invalid Token"},401
@app.route('/manager/<token>/<int:id>')
def read_manager_book(token,id):
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        current_user = Manager.query.filter_by(username=data['username'],uuid=data['unique_id']).first()
    except jwt.ExpiredSignatureError:
        return {'message': 'Token has expired'}, 401
    except jwt.InvalidTokenError as e:
        return {'message': 'Invalid token', 'error': str(e), 'token': token}, 401
    external_folder = 'Uploades/books'
    if current_user:
        book = Book.query.filter_by(id=id,manager_id=current_user.id).first()
        if book:
            filename = book.ebook.split("/")[2]
            return send_from_directory(external_folder, filename) 
        else:
            return {"message": "Book Not Found"},404
    else:
       return  {"message" : "Invalid Token"},401



@celery.task
def generate_and_send_monthly_reports():
    with app.app_context():
        managers = Manager.query.all()
        for manager in managers:
            # Get the start and end dates for the previous month
            start_date, end_date = get_previous_month_dates()
            section_distribution = get_section_distribution(manager, start_date, end_date)
            user_reading_status = get_user_reading_status(manager, start_date, end_date)
            request_statuses = get_request_statuses(manager, start_date, end_date)
            completed_book_distribution = get_completed_book_distribution(manager, start_date, end_date)

            # Generate charts and encode them
            book_distribution_chart_data = generate_base64_encoded_chart(section_distribution, 'Book Distribution', 'bar')
            user_reading_status_chart_data = generate_base64_encoded_chart(user_reading_status, 'User Reading Status', 'doughnut')
            request_status_chart_data = generate_base64_encoded_chart(request_statuses, 'Request Status', 'doughnut')
            completed_book_distribution_chart_data = generate_base64_encoded_chart(completed_book_distribution, 'Completed Book Distribution', 'line')

            # Prepare email content
            msg = Message(subject='Monthly Report', recipients=[manager.email])
            msg.body = 'Monthly report attached.'
            
            html_content = f"""
            <html>
            <body>
                <h1>Monthly Report</h1>
                <h2>Book Distribution</h2>
                <img src="data:image/png;base64,{book_distribution_chart_data}" alt="Book Distribution Chart">
                <h2>User Reading Status</h2>
                <img src="data:image/png;base64,{user_reading_status_chart_data}" alt="User Reading Status Chart">
                <h2>Request Status</h2>
                <img src="data:image/png;base64,{request_status_chart_data}" alt="Request Status Chart">
                <h2>Completed Book Distribution</h2>
                <img src="data:image/png;base64,{completed_book_distribution_chart_data}" alt="Completed Book Distribution Chart">
            </body>
            </html>
            """
            
            msg.html = html_content

            mail.send(msg)
        plt.close('all')

def get_previous_month_dates():
    today = datetime.now(pytz.timezone('Asia/Kolkata'))
    last_month = today - timedelta(days=today.day)
    start_date = datetime(last_month.year, last_month.month, 1)
    end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
    return start_date, end_date


def get_section_distribution(manager, start_date, end_date):
    section_distribution = {}
    sections = Section.query.filter(Section.created_date >= start_date, Section.created_date <= end_date).all()
    for section in sections:
        section_books = Book.query.filter_by(manager_id=manager.id, section_id=section.id).filter(Book.created_date >= start_date, Book.created_date <= end_date).all()
        section_distribution[section.name] = len(section_books)
    return section_distribution

def get_user_reading_status(manager, start_date, end_date):
    user_reading_status = {
        'Reading': BookRequested.query.filter_by(manager_id=manager.id, reading_status='reading').filter(BookRequested.processed_date >= start_date, BookRequested.processed_date <= end_date).count(),
        'Completed': CompletedBook.query.filter_by(manager_id=manager.id).filter(CompletedBook.processed_date >= start_date, CompletedBook.processed_date <= end_date).count(),
    }
    return user_reading_status

def get_request_statuses(manager, start_date, end_date):
    request_statuses = {
        'Approved': BookRequested.query.filter_by(manager_id=manager.id, status='accepted').filter(BookRequested.processed_date >= start_date, BookRequested.processed_date <= end_date).count() + 
                    BookRequested.query.filter_by(manager_id=manager.id, status='revoked').filter(BookRequested.processed_date >= start_date, BookRequested.processed_date <= end_date).count() +
                    BookRequested.query.filter_by(manager_id=manager.id, status='returned').filter(BookRequested.processed_date >= start_date, BookRequested.processed_date <= end_date).count(),
        'Rejected': BookRequested.query.filter_by(manager_id=manager.id, status='rejected').filter(BookRequested.processed_date >= start_date, BookRequested.processed_date <= end_date).count(),
    }
    return request_statuses

def get_completed_book_distribution(manager, start_date, end_date):
    completed_book_distribution = {}
    completed_books = CompletedBook.query.filter_by(manager_id=manager.id).filter(CompletedBook.processed_date >= start_date, CompletedBook.processed_date <= end_date).all()
    for completed_book in completed_books:
        date_str = completed_book.processed_date.strftime('%Y-%m-%d')
        if date_str in completed_book_distribution:
            completed_book_distribution[date_str] += 1
        else:
            completed_book_distribution[date_str] = 1
    return completed_book_distribution

def generate_base64_encoded_chart(data, title, mode):
    plt.figure()
    # Generate the chart
    if mode == 'doughnut':
        chart = generate_doughnut_chart(data, title)
    elif mode == 'bar':
        chart = generate_bar_chart(data, title)
    elif mode == 'line':
        chart = generate_line_chart(data, title)
    
    # Save the chart to a BytesIO buffer
    buffer = io.BytesIO()
    chart.savefig(buffer, format='png')
    buffer.seek(0)
    # Encode the chart as a base64 string
    encoded_chart = base64.b64encode(buffer.read()).decode()
    plt.close()  # Close the figure to release memory
    return encoded_chart

def generate_bar_chart(data, title):
    plt.figure()
    plt.bar(data.keys(), data.values())
    plt.title(title)
    plt.xlabel('Section')
    plt.ylabel('Number of Books')
    plt.xticks(rotation=45)
    return plt

def generate_doughnut_chart(data, title):
    if not data or all(value == 0 for value in data.values()):
        print(f"No data available for {title}. Returning empty figure.")
        return plt.figure(facecolor='none')  # Return an empty transparent figure

    fig, ax = plt.subplots()
    ax.pie(data.values(), labels=data.keys(), autopct='%1.1f%%')
    ax.set_title(title)
    return fig

def generate_line_chart(data, title):
    plt.figure()
    plt.plot(list(data.keys()), list(data.values()), marker='o')
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Number of Completed Books')
    return plt

@celery.task
def generate_and_send_monthly_reports_user():
    with app.app_context():
        users = User.query.all()
        for user in users:
            # Get the start and end dates for the previous month
            start_date, end_date = get_previous_month_dates()
            
            user_reading_data = get_user_reading_data(user, start_date, end_date)

            # Prepare email content
            msg = compose_email(user, user_reading_data)
            mail.send(msg)

def get_user_reading_data(user, start_date, end_date):
    user_reading_data = {}
    # Get all sections read by the user in the previous month
    sections_read = Section.query.join(CompletedBook).filter(CompletedBook.user_id == user.id, CompletedBook.processed_date >= start_date, CompletedBook.processed_date <= end_date).distinct().all()
    for section in sections_read:
        # Count the number of books read by the user in each section
        books_read_count = CompletedBook.query.filter(CompletedBook.user_id == user.id, CompletedBook.section_id == section.id, CompletedBook.processed_date >= start_date, CompletedBook.processed_date <= end_date).count()
        user_reading_data[section.name] = books_read_count
    return user_reading_data


def compose_email(user, user_reading_data):
    # Prepare email content
    msg = Message(subject='Your Monthly Reading Summary', recipients=[user.email])
    msg.body = f'Hello {user.username},\n\nHere is your reading summary for the previous month:\n\n'
    for section, book_count in user_reading_data.items():
        msg.body += f'- Section "{section}": {book_count} books\n'
    msg.body += '\nKeep up the good reading!\n\n'
    return msg


if __name__ == '__main__':
    app.run(debug=True)
