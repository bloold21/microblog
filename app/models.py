from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from app.searchable_mixin import SearchableMixin


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
    )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship('User', secondary=followers,
                primaryjoin=(followers.c.follower_id==id),
                secondaryjoin=(followers.c.followed_id==id),
                backref=db.backref('followers', lazy='dynamic'),
                lazy='dynamic'
                )

    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    message_sent = db.relationship('Message',
                    foreign_keys='Message.sender_id',
                    backref='author', lazy='dynamic')
    message_received = db.relationship('Message',
                    foreign_keys='Message.recipient_id',
                    backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)

    def __repr__(self):
        return '<User %s>' %self.username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower()).hexdigest()
        return 'https://www.gravatar.com/avatar/%s?d=identicon&s=%s' %(digest,size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            user.id == followers.c.followed_id
        ).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id==Post.user_id)).filter(
                followers.c.follower_id==self.id
            )
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def new_message(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp>last_read_time).count()


class Post(SearchableMixin,db.Model):
    __searchable__ = ['body']
    id =db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post %s>' %self.body


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message %s>' %self.body