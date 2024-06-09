from __init__ import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SECRET_KEY'] = '1234!@#)(*&^#$)'
app.config['UPLOADED_PHOTOS_DEST'] = 'static/book-coverpages'
app.config['UPLOADED_EBOOKS_DEST'] = 'Uploades/books'
app.config['UPLOADED_PRE_EBOOKS_DEST']='Uploades/preview_books'

app.config['MAIL_SERVER'] = 'localhost'
app.config['MAIL_PORT'] = 1025
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEBUG'] = app.debug
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None
app.config['MAIL_DEFAULT_SENDER'] = 'admin@gmail.com'

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Cache Configuration with Redis
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = '6379'