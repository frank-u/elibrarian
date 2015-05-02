import hashlib
from datetime import datetime
from flask import current_app, request, url_for
from flask.ext.login import AnonymousUserMixin, UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from re import compile
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


# ----=[ authentication support models ]=---------------------------------------
class Permission:
    VIEW_LIBRARY_STATS = 0x01
    VIEW_LIBRARY_ITEMS_METADATA = 0x02
    VIEW_LIBRARY_ITEMS = 0x04
    DOWNLOAD_FROM_LIBRARY_STORAGE = 0x08
    UPLOAD_CONTENT = 0x10
    ADMINISTER = 0x80


class AuthRole(db.Model):
    __tablename__ = 'auth_roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('AuthUser', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            # user - is the default role assigned when creating a user
            'user': (Permission.VIEW_LIBRARY_STATS |
                     Permission.VIEW_LIBRARY_ITEMS_METADATA, True),
            'moderator': (Permission.VIEW_LIBRARY_STATS |
                          Permission.VIEW_LIBRARY_ITEMS_METADATA |
                          Permission.VIEW_LIBRARY_ITEMS |
                          Permission.DOWNLOAD_FROM_LIBRARY_STORAGE, False),
            'administrator': (0xff, False)
        }
        for r in roles:
            role = AuthRole.query.filter_by(name=r).first()
            if role is None:
                role = AuthRole(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return "<Role {0}>".format(self.name)


class AuthUser(UserMixin, db.Model):
    __tablename__ = 'auth_users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('auth_roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    preferred_lang = db.Column(db.String(3), nullable=True)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))

    def __init__(self, **kwargs):
        super(AuthUser, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ELIBRARIAN_ADMIN']:
                self.role = AuthRole.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = AuthRole.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='x'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return AuthUser.query.get(data['id'])

    def __repr__(self):
        return "<User {0}({1}, {2})>".format(self.username, self.id, self.email)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return AuthUser.query.get(int(user_id))


# ----=[ primary library models ]=----------------------------------------------
class Author(db.Model):
    """Can be book author, translator or somebody who makes something"""
    __tablename__ = "authors"
    id = db.Column(db.Integer, primary_key=True)
    original_lang = db.Column(db.String(3), nullable=True)

    details = db.relationship('AuthorDetail', backref='author', lazy='dynamic')
    literary_works = db.relationship('Authors2LiteraryWorks', backref='author')

    @property
    def full_name(self):
        # TODO: Return full_name on preferred lang or default otherwise
        details = self.details.first()
        if details:
            full_name_row = " ".join([
                details.first_name if details.first_name else "",
                details.middle_name if details.middle_name else "",
                details.last_name
            ])
            return compile(r'\s+').sub(' ', full_name_row)
        else:
            return ""

    def get_literary_works(self):
        return [assoc.literary_works for assoc in self.literary_works]

    def to_json(self):
        details = self.details.first()
        json_post = {
            'id': self.id,
            'url': url_for('api.get_author', author_id=self.id, _external=True),
            'name': self.full_name,
            'literary_works': [
                {
                    'id': lw.id,
                    'url': url_for('api.get_literary_work',
                                   work_id=lw.id, _external=True)
                }
                for lw in self.get_literary_works()
            ]
        }
        if self.original_lang:
            json_post['original_lang'] = self.original_lang
        if details:
            if details.nickname:
                json_post['nickname'] = details.nickname
            if details.wikipedia_hyperlink:
                json_post['wikipedia_hyperlink'] = details.wikipedia_hyperlink
        return json_post


class AuthorDetail(db.Model):
    """Multilingual author's detailed information"""
    __tablename__ = "authors_details"
    id = db.Column(db.Integer, db.ForeignKey('authors.id'), primary_key=True)
    lang = db.Column(db.String(3), nullable=False)
    last_name = db.Column(db.String(63), nullable=False, index=True)
    first_name = db.Column(db.String(63), nullable=True)
    middle_name = db.Column(db.String(63), nullable=True)
    nickname = db.Column(db.String(127), nullable=True)
    wikipedia_hyperlink = db.Column(db.String(255), nullable=True)


class LiteraryWork(db.Model):
    """Books, articles, and other literary works metadata"""
    __tablename__ = "literary_works"
    id = db.Column(db.Integer, primary_key=True)
    creation_datestring = db.Column(db.String(63), nullable=True)
    original_lang = db.Column(db.String(3), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    details = db.relationship('LiteraryWorkDetail', backref='literarywork',
                              lazy='dynamic')

    def get_authors(self):
        lws = Authors2LiteraryWorks.query.filter_by(
            literary_work_id=self.id).all()
        return [Author.query.filter_by(id=lw.author_id).scalar() for lw in lws]

    def to_json(self, lang="en"):
        json = {
            'id': self.id,
            'url': url_for('api.get_literary_work', work_id=self.id,
                           _external=True),
            # TODO: Implement language agnostic API or return titles on all
            # stored languages
            # 'title': self.title,
            'original_lang': self.original_lang,
            'authors': [
                {'name': author.full_name,
                 'id': author.id,
                 'url': url_for('api.get_author', author_id=author.id,
                                _external=True)
                 }
                for author in self.get_authors()
            ]
        }
        if self.creation_datestring:
            json['creation_datestring'] = self.creation_datestring
        # catch-up literary works details
        details = self.details.filter_by(lang=lang).all()
        if not details:
            details = self.details.all()
        if details:
            json['title'] = details[0].title
            if details[0].annotation:
                json['annotation'] = details[0].annotation
        return json


class LiteraryWorkDetail(db.Model):
    """Books, articles, and other literary works metadata details in different
    languages"""
    __tablename__ = "literary_works_details"
    id = db.Column(db.Integer, primary_key=True)
    literary_work_id = db.Column(db.Integer,
                                 db.ForeignKey('literary_works.id'),
                                 nullable=False)
    lang = db.Column(db.String(5), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    annotation = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('literary_work_id', 'lang', name='lw_lang_unique'),
        {},
    )

    files = db.relationship('LiteraryWorkStorage', backref='literaryworkdetail',
                            lazy='dynamic')


class LiteraryWorkStorage(db.Model):
    """Support storing of files - actual literary work (book) data for selected
    languages"""
    __tablename__ = 'literary_works_storage'
    id = db.Column(db.Integer, primary_key=True)
    literary_work_details_id = db.Column(
        db.Integer,
        db.ForeignKey('literary_works_details.id'),
        nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    mime_type = db.Column(db.String(63), nullable=False)
    original_file_name = db.Column(db.String(255))
    original_file_ext = db.Column(db.String(255))
    # Allow storing max 2^27=128MB files
    binary_data = db.Column(db.LargeBinary(2 ** 27), nullable=False)
    parent_id = db.Column(db.ForeignKey('literary_works_storage.id'),
                          default=None, nullable=True)


class BookSeries(db.Model):
    __tablename__ = 'literary_works_series'

    id = db.Column(db.Integer, primary_key=True)
    original_lang = db.Column(db.String(3), nullable=True, default=None)
    parent_id = db.Column(db.ForeignKey(__tablename__ + '.id'), nullable=True,
                          default=None)

    details = db.relationship('BookSeriesDetail', backref='bookserie',
                              lazy='dynamic')


class BookSeriesDetail(db.Model):
    """Multilingual book series detailed information"""
    __tablename__ = 'literary_works_series_details'

    id = db.Column(db.Integer, db.ForeignKey('literary_works_series.id'),
                   primary_key=True)
    lang = db.Column(db.String(3), nullable=False)
    title = db.Column(db.String(255), nullable=False)


class Genre(db.Model):
    """Hierarchical table for genres"""
    __tablename__ = 'genres'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(63), nullable=True)
    parent_id = db.Column(db.ForeignKey(__tablename__ + '.id'), nullable=True,
                          default=None)


class GenreDetail(db.Model):
    """Multilingual genre detailed information"""
    __tablename__ = 'genres_details'

    id = db.Column(db.Integer, db.ForeignKey('genres_details.id'),
                   primary_key=True)
    lang = db.Column(db.String(3), nullable=False)
    title = db.Column(db.String(255), nullable=False)


# ----=[ primary library join models ]=-----------------------------------------
class Authors2LiteraryWorks(db.Model):
    """Link between authors and their literary works (usually books)"""
    __tablename__ = "authors_2_literary_works"
    author_id = db.Column(db.Integer,
                          db.ForeignKey('authors.id'),
                          primary_key=True)
    literary_work_id = db.Column(db.Integer,
                                 db.ForeignKey('literary_works.id'),
                                 primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    literary_works = db.relationship('LiteraryWork', backref="author_assocs")


class BookSeriesSnap(db.Model):
    """Link between literary works and series"""
    __tablename__ = 'literary_works_2_series'

    literary_work_id = db.Column(db.Integer, db.ForeignKey('literary_works.id'),
                                 primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('literary_works_series.id'),
                          primary_key=True)
    position = db.Column(db.Integer, primary_key=True)


class BookGenreSnap(db.Model):
    """Link between literary works and genres"""
    __tablename__ = 'literary_works_2_genres'

    literary_work_id = db.Column(db.Integer, db.ForeignKey('literary_works.id'),
                                 primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'),
                         primary_key=True)


# ----=[ user relations with the library ]=-------------------------------------
class AuthUserPersonalLibrary(db.Model):
    """User's personal library. A subset of all known books in "literary_works".
    Contains user's library usage statistics (what to read, book ratings...)"""
    __tablename__ = "users_personal_library"
    user_id = db.Column(db.Integer, db.ForeignKey('auth_users.id'))
    literary_work_id = db.Column(db.Integer, db.ForeignKey('literary_works.id'))
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'literary_work_id'),
        {},
    )
    # Special flags about book in user's personal collection
    plan_to_read = db.Column(db.Boolean, default=False, nullable=False)
    read_flag = db.Column(db.Boolean, default=False, nullable=False)
    # read progress percentage, not null indicating that user start reading book
    read_progress = db.Column(db.Integer, default=None, nullable=True)
    read_date = db.Column(db.Date, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.Text, nullable=True)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
