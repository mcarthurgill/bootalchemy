from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Table
from sqlalchemy.orm import relation, sessionmaker

metadata = MetaData()
DeclarativeBase = declarative_base(metadata=metadata)

movie_directors_table = Table('movie_directors', metadata,
                              Column('movie_id', Integer, ForeignKey('movies.movie_id'), primary_key = True),
                              Column('director_id', Integer, ForeignKey('directors.director_id'), primary_key = True))

class Genre(DeclarativeBase):
    __tablename__ = "genres"
    genre_id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(300))

class Movie(DeclarativeBase):
    __tablename__ = "movies"
    movie_id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    genre_id = Column(Integer, ForeignKey('genres.genre_id'))
    genre = relation('Genre', backref='movies')
    release_date = Column(Date, nullable=True)

class Director(DeclarativeBase):
    __tablename__ = "directors"
    director_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    movies = relation(Movie, secondary=movie_directors_table, backref="directors")
    
engine = create_engine("postgres://localhost/test_bootalchemy")
metadata.bind = engine
metadata.drop_all()
metadata.create_all()

session = sessionmaker()()

from bootalchemy.loader import Loader

class Model(object):pass
model = Model()
model.Genre = Genre
model.Movie = Movie 
model.Director = Director

data = [{'Genre':[{'name': "action", 
                   'description':'Car chases, guns and violence.'
                  }
                 ]
        }
       ]

loader = Loader(model)
loader.from_list(session, data)

genres = session.query(Genre).all()
print [(genre.name, genre.description) for genre in genres]

data = [{'Genre':[{'genre_id':'&scifi_id',
                   'name': "sci-fi", 
                   'description':'Science Fiction, see: 42'
                  }
                 ],
          'flush':None},
        {'Movie':[{"title": "Back to the Future", 
                  "description": "In 1985, Doc Brown invents time travel; in 1955,\
                                  Marty McFly accidentally prevents his parents from\
                                  meeting, putting his own existence at stake",
                  "release_date": "1985-04-03", 
                  "genre_id": '*scifi_id'}],
         'flush':None
         }]

loader.from_list(session, data)
movies = session.query(Movie).all()
print [(movie.title, movie.genre.name) for movie in movies]
#[('Back to the Future', 'sci-fi')]

data = [{'Genre':[{'&comedy':{'name': "comedy", 
                   'description':"Don't you _like_ to laugh?"
                  }}
                 ],
          'flush':None},
        {'Movie':[{"description": '"Dude" Lebowski, mistaken for a millionaire Lebowski,\
                                   seeks restitution for his ruined rug and enlists his \
                                   bowling buddies to help get it.', 
                   "title": "The Big Lebowski", 
                   "release_date": "1998-03-06", 
                   "genre": "*comedy"}],
         'flush':None
         }]

loader.from_list(session, data)
movies = session.query(Movie).all()
print [(movie.title, movie.genre.name) for movie in movies]
#[('Back to the Future', 'sci-fi'), ('The Big Lebowski', 'comedy')]

data = [{'Director':[{'&andy':{'name': "Andy Wachowski"}},
                     {'&larry':{'name': "Larry Wachowski"}} 
                 ],
          'flush':None},
        {'Movie':[{"description": "A computer hacker learns from mysterious rebels\
                                   about the true nature of his reality and his\
                                   role in the war against the controllers of it.", 
                   "title": "The Matrix", 
                   "release_date": "1999-03-31", 
                   "directors": ['*andy', '*larry'], "genre_id": "*scifi_id"}],
         'flush':None
         }]

loader.from_list(session, data)
movies = session.query(Movie).all()
print [(movie.title, [d.name for d in movie.directors]) for movie in movies]
#[('Back to the Future', []), ('The Big Lebowski', []), ('The Matrix', ['Andy Wachowski', 'Larry Wachowski'])]


data = """
- Movie:
    - description: An office employee and a soap salesman build a global organization to help vent male aggression.,
      title: Fight Club,
      release_date: 1999-10-14
      genre: "*action"
  flush:
"""
from bootalchemy.loader import YamlLoader

action = session.query(Genre).filter(Genre.name=='action').first()
loader = YamlLoader(model, references={'action':action})
loader.loads(session, data)
movies = session.query(Movie).all()
print [(movie.title, movie.genre.name) for movie in movies]
#[('Back to the Future', 'sci-fi'), ('The Big Lebowski', 'comedy'), ('The Matrix', 'sci-fi'), ('Fight Club,', 'action')]
