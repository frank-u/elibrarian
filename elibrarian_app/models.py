from re import compile
from datetime import datetime
from . import db


# ----=[ primary library models ]=----------------------------------------------
class Author(db.Model):
    """Can be book author, translator or somebody who makes something"""
    __tablename__ = "authors"
    id = db.Column(db.Integer, primary_key=True)
    original_lang = db.Column(db.String(3), nullable=True)

    details = db.relationship('AuthorDetail', backref='author',
                              lazy='dynamic')
    literary_works = db.relationship('Authors2LiteraryWorks',
                                     backref=db.backref('author',
                                                        lazy='joined'),
                                     lazy='select')

    @property
    def full_name(self):
        # TODO: Return full_name on preferred lang or default otherwise
        details = self.details.filter_by(lang=self.original_lang).first()
        full_name_row = " ".join([details.first_name, details.middle_name,
                                  details.last_name])
        return compile(r'\s+').sub(' ', full_name_row)


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
    lang = db.Column(db.String(3), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    annotation = db.Column(db.Text, nullable=True)
    creation_datestring = db.Column(db.String(63), nullable=True)
    original_lang = db.Column(db.String(3), nullable=True)
    added = db.Column(db.DateTime, default=datetime.utcnow)


class LiteraryWorkStorage(db.Model):
    """Support storing of files - actual literary work (book) data"""
    __tablename__ = 'literary_works_storage'
    id = db.Column(db.Integer, primary_key=True)
    literary_work_id = db.Column(db.Integer,
                                 db.ForeignKey('literary_works.id'),
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

    literary_works = db.relationship('LiteraryWork', backref="authors")


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
