"""
    Module contains all DB models, which makes the database structure and
behaviour.
"""
import hashlib
from datetime import datetime
from flask import current_app, g, request, url_for
from flask_login import AnonymousUserMixin, UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


# ----=[ authentication support models ]=--------------------------------------
class Permission:
    """Describes bit fields in permissions value of AuthRole model"""
    VIEW_LIBRARY_STATS = 0x01
    VIEW_LIBRARY_ITEMS_METADATA = 0x02
    VIEW_LIBRARY_ITEMS = 0x04
    DOWNLOAD_FROM_LIBRARY_STORAGE = 0x08
    UPLOAD_CONTENT = 0x10
    ADMINISTER = 0x80


class AuthRole(db.Model):
    """
        Describes database access roles which composed of different sets of
    permissions
    """
    __tablename__ = 'auth_roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('AuthUser', backref='role', lazy='dynamic')

    def __init__(self, name, permissions=0, default=False):
        super(AuthRole, self).__init__()
        self.name = name
        self.permissions = permissions
        self.default = default

    @staticmethod
    def insert_roles():
        """Helper for initial fill-in predefined default roles"""
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
        for role_name in roles:
            role = AuthRole.query.filter_by(name=role_name).first()
            if role is None:
                role = AuthRole(name=role_name)
            role.permissions = roles[role_name][0]
            role.default = roles[role_name][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return "<Role {0}>".format(self.name)


class AuthUser(UserMixin, db.Model):
    """
        Describes eLibrarian's end user.
        Stores fields describing user, his credentials, role, etc.
    """
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
        """Do not allow to read plain password"""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """Save only password hash instead of password"""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Verify that given password belongs to this user by checking hash"""
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        """Generate confirmation token with expiration time in seconds and
        return a JSON"""
        serializer = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serializer.dumps({'confirm': self.id})

    def confirm(self, token):
        """
            First, checks that given token is:
            - valid;
            - the 'confirm' type token;
            - belong to this user.
            After that save to database that this user is confirmed.
        """
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        """Generate token to reset password with expiration time in seconds and
        return a JSON"""
        serializer = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serializer.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        """
            First, checks that given token is:
            - valid;
            - the 'reset' type token;
            - belong to this user.
            After that set 'new_password' to this user object and append object
        to database session for saving.
        """
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        """Generate token to change email with expiration time in seconds and
        return a JSON"""
        serializer = Serializer(current_app.config['SECRET_KEY'], expiration)
        return serializer.dumps(
            {'change_email': self.id, 'new_email': new_email}
        )

    def change_email(self, token):
        """
            First, checks that given token is:
            - valid;
            - the 'change_email' type token;
            - belong to this user.
            After that get 'new_email' from token and change email for this
        user object and append object to database session for saving.
        """
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except (BadSignature, SignatureExpired):
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
        """Return true if user has all the permissions"""
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        """Return true if user is administrator"""
        return self.can(Permission.ADMINISTER)

    def ping(self):
        """
            Update user's last_seen value.
            Method should be called on any user activity.
        """
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='x'):
        """Get link pointing to user's gravatar"""
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        av_hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=av_hash, size=size, default=default, rating=rating)

    def generate_auth_token(self, expiration):
        """
            Generate authorization token with user id inside and expiration
        time in seconds and return a JSON.
        """
        serializer = Serializer(current_app.config['SECRET_KEY'],
                                expires_in=expiration)
        return serializer.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        """
            Checks that given token is valid and returns the user object given
        by id inside token
        """
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except (BadSignature, SignatureExpired):
            return None
        return AuthUser.query.get(data['id'])

    def __repr__(self):
        return "<User {0}({1}, {2})>".format(
            self.username, self.id, self.email)


class AnonymousUser(AnonymousUserMixin):
    """Disable all permissions for anonymous user"""

    def can(self, permissions):
        """Forbid everything despite of permission"""
        return False

    def is_administrator(self):
        """Anonymous is not the administrator"""
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    """Get user object by id for flask auth purpose"""
    return AuthUser.query.get(int(user_id))


# ----=[ primary library models ]=---------------------------------------------
class Author(db.Model):
    """Can be book author, translator or somebody who makes something"""
    __tablename__ = "authors"
    id = db.Column(db.Integer, primary_key=True)
    original_lang = db.Column(db.String(3), nullable=True)

    details = db.relationship('AuthorDetail', backref='author', lazy='dynamic')
    literary_works = db.relationship('Authors2LiteraryWorks', backref='author')

    @property
    def full_name(self, lang):
        """
            Returns constructed full name in language ``lang`` or current user
        prefered language
        """
        if lang:
            return self.get_details(lang)['full_name']
        else:
            return self.get_details(g.current_user.preferred_lang)['full_name']

    def get_details(self, lang="en"):
        """
            Return author details dictionary in preferred language, or
        search english if 'lang' is not specified or trying for find any
        details if no details with above languages exist.
        """
        details = self.details.filter_by(lang=lang).first()
        if not details:
            details = self.details.filter_by(lang="en").first()
        if not details:
            details = self.details.first()
        if details:
            return details.to_json()
        return None

    def get_literary_works(self):
        """
            Returns list LiteraryWork objects. (Literary works created by this
        author.
        """
        return [assoc.literary_works for assoc in self.literary_works]

    def to_json(self, lang="en", verbose=False):
        """
            Returns JSON representation of author object and related literary
        works list on a given language (if available, english by default), and
        verbose if needed.
        """
        json = {
            'id': self.id,
            'url': url_for('api.get_author', author_id=self.id,
                           _external=True),
            'literary_works': []
        }
        if verbose:
            json.update(self.get_details(lang=lang))
        else:
            json['full_name'] = self.get_details(lang=lang)['full_name']
            json['lang'] = self.get_details(lang=lang)['lang']
        if self.original_lang:
            json['original_lang'] = self.original_lang

        for literary_work in self.get_literary_works():
            lw_base = {
                'id': literary_work.id,
                'url': url_for('api.get_literary_work',
                               work_id=literary_work.id, _external=True)
            }
            lw_detail = literary_work.get_details(lang=lang)
            if lw_detail:
                for key in ('title', 'lang'):
                    lw_base[key] = lw_detail[key]
            json['literary_works'].append(lw_base)
        return json


class AuthorDetail(db.Model):
    """Multilingual author's detailed information"""
    __tablename__ = "authors_details"
    id = db.Column(db.Integer, db.ForeignKey('authors.id'))
    lang = db.Column(db.String(3), nullable=False)
    last_name = db.Column(db.String(63), nullable=False, index=True)
    first_name = db.Column(db.String(63), nullable=True)
    middle_name = db.Column(db.String(63), nullable=True)
    nickname = db.Column(db.String(127), nullable=True)
    wikipedia_hyperlink = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.PrimaryKeyConstraint('id', 'lang', name='author_id-lang_pkey'),
        {},
    )

    def __init__(self, lang, last_name):
        super(AuthorDetail, self).__init__()
        self.lang = lang
        self.last_name = last_name

    def to_json(self):
        """Returns JSON representation of authors detailed information."""
        result = {
            'lang': self.lang,
            'last_name': self.last_name,
            'full_name': self.last_name
        }
        if self.middle_name:
            result['middle_name'] = self.middle_name
            result['full_name'] = " ".join(
                (self.middle_name, result['full_name'])
            )
        if self.first_name:
            result['first_name'] = self.first_name
            result['full_name'] = " ".join(
                (self.first_name, result['full_name'])
            )
        if self.nickname:
            result['nickname'] = self.nickname
        if self.wikipedia_hyperlink:
            result['wikipedia_hyperlink'] = self.wikipedia_hyperlink
        return result


class LiteraryWork(db.Model):
    """Books, articles, and other literary works metadata"""
    __tablename__ = "literary_works"
    id = db.Column(db.Integer, primary_key=True)
    creation_datestring = db.Column(db.String(63), nullable=True)
    original_lang = db.Column(db.String(3), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    details = db.relationship('LiteraryWorkDetail', backref='literarywork',
                              lazy='dynamic')

    def __init__(self, original_lang):
        super(LiteraryWork, self).__init__()
        if original_lang:
            self.original_lang = original_lang

    def get_authors(self):
        """
            Returns list of authors (instances of Author objects) belongs to
        this literary work.
        """
        lws = Authors2LiteraryWorks.query.filter_by(
            literary_work_id=self.id).all()
        return [Author.query.filter_by(id=lw.author_id).scalar() for lw in lws]

    def get_details(self, lang="en", verbose=False):
        """
            Return literary work details dictionary in preferred language, or
        search  english if 'lang' is not specified  or trying for find any
        details if no details with above languages exist.
        """
        details = self.details.filter_by(lang=lang).first()
        if not details:
            details = self.details.filter_by(lang="en").first()
        if not details:
            details = self.details.first()
        if details:
            result = {
                'title': details.title,
                'lang': details.lang
            }
            if verbose and details.annotation:
                result['annotation'] = details.annotation
            return result
        return None

    def to_json(self, lang="en", verbose=False):
        """
            Returns JSON representation of literary work on a given language
        if available, and verbose if needed.
        """
        json = {
            'id': self.id,
            'url': url_for('api.get_literary_work', work_id=self.id,
                           _external=True),
            'original_lang': self.original_lang,
            'authors': [
                {
                    'name': author.get_details(lang=lang)['full_name'],
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
        details = self.get_details(lang=lang, verbose=verbose)
        if details:
            json.update(details)
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

    files = db.relationship('LiteraryWorkStorage',
                            backref='literaryworkdetail',
                            lazy='dynamic')

    def __init__(self, lang, title):
        super(LiteraryWorkDetail, self).__init__()
        self.lang = lang
        self.title = title


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
    """
        If different literary works belongs to the serie (like dilogy, trilogy
    or something else) this model will stick together book with serie.
        Model also supports hierarchy of series.
    """
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

    def __init__(self, lang, title):
        super(BookSeriesDetail, self).__init__()
        self.lang = lang
        self.title = title


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

    def __init__(self, lang, title):
        super(GenreDetail, self).__init__()
        self.lang = lang
        self.title = title


# ----=[ primary library join models ]=----------------------------------------
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

    literary_work_id = db.Column(db.Integer,
                                 db.ForeignKey('literary_works.id'),
                                 primary_key=True)
    series_id = db.Column(db.Integer,
                          db.ForeignKey('literary_works_series.id'),
                          primary_key=True)
    position = db.Column(db.Integer, primary_key=True)


class BookGenreSnap(db.Model):
    """Link between literary works and genres"""
    __tablename__ = 'literary_works_2_genres'

    literary_work_id = db.Column(db.Integer,
                                 db.ForeignKey('literary_works.id'),
                                 primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'),
                         primary_key=True)


# ----=[ user relations with the library ]=------------------------------------
class AuthUserPersonalLibrary(db.Model):
    """User's personal library. A subset of all known books in "literary_works".
    Contains user's library usage statistics (what to read, book ratings...)"""
    __tablename__ = "users_personal_library"
    user_id = db.Column(db.Integer, db.ForeignKey('auth_users.id'))
    literary_work_id = db.Column(db.Integer,
                                 db.ForeignKey('literary_works.id'))
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'literary_work_id'),
        {},
    )
    # Special flags about book in user's personal collection
    plan_to_read = db.Column(db.Boolean, default=False, nullable=False)
    read_flag = db.Column(db.Boolean, default=False, nullable=False)
    # read progress percentage, not null indicating that user start to read a
    # book
    read_progress = db.Column(db.Integer, default=None, nullable=True)
    read_date = db.Column(db.Date, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.Text, nullable=True)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self):
        super(AuthUserPersonalLibrary, self).__init__()
        self.plan_to_read = False
        self.read_flag = False

    @property
    def rating(self):
        """Return book rating by a given user"""
        return self.rating

    @rating.setter
    def rating(self, rating):
        """Set personal book rating for a given user"""
        error_msg = "Rating should be integer or float in range 0.0,...,5.0"
        if not (isinstance(rating, float) or isinstance(rating, int)):
            raise TypeError(error_msg)
        if 0 <= rating <= 5:
            self.rating = rating
        else:
            raise ValueError(error_msg)
