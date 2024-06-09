from createdb import *
from werkzeug.security import generate_password_hash, check_password_hash

admin_username = 'L1'
admin_password = 'L1@123'  # Change this to a secure password
admin_email = 'L1@gmail.com'

hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')

with app.app_context():
    new_admin = Manager(username=admin_username, email=admin_email, password=hashed_password)
    db.session.add(new_admin)
    db.session.commit()



'''

user = User(username="indu",email="indumiriyala@",password="1234567")
manager = Manager(username="M1",email="M1@gmail",password="M1")
book = Book(title="B1",author="A1")
db.session.add(user)
db.session.add(manager)
db.session.commit()
manager.books.append(book)
db.session.commit()
requset_book = BookRequested(title="B1",author="A1",manager_id=manager.id,user_id=user.id)
db.session.add(requset_book)
db.session.commit()
print(manager.books,manager.requested_books.__dict__,user.requested_books.__dict__)
'''