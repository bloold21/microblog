from app import db, create_app
from app.models import User, Post, Notification, Message

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post,
            'Message': Message, 'Notification': Notification}