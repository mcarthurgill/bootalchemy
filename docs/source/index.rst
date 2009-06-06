BootAlchemy
=============
BootAlchemy is a tool which allows you to load data into an SQL
database via yaml-formatted text.  You provide bootalchemy with set
of mapped objects, and some text, and it will push objects
with that text into the database.  In addition to all of the functionality
YAML provides, BootAlchemy can also de-obfuscate relationships and
add those to the database as well.

Current Version
------------------
|version|

Requirements
---------------
* SqlAlchemy>=0.5
* PyYaml

Getting Started With BootAlchemy
---------------------------------
Let us first consider this model, assume it is defined in a module called "model"::

        
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
        title = Column(String(100), nullable=False)
        movies = relation(Movie, secondary=movie_directors_table, backref="directors")

Simple Example
----------------
First let's explore the structure used to push data into the database.  We
will use plain python to load in the data::

    from bootalchemy.loader import Loader
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

produces::

  [('action', 'Car chases, guns and violence.')]

Note that while the data is in the session, it has not yet been commited
to the database.  Boot alchemy does not commit by default but can be
made to do so.

The BootAlchemy Data Structure
-----------------------------------

The basic structure of a BootAlchemy data structure is like this::

    [
        { #start of the first grouping
          ObjectName:[ #start of objects of type ObjectName
                      {'attribute':'value', 'attribute':'value' ... more attributes},
                      {'attribute':'value', 'attribute':'value' ... more attributes},
                      ...
                      } 
                      ]
          ObjectName: [ ... more attr dicts here ... ]
          [commit:None] #optionally commit at the end of this grouping
          [flush:None]  #optionally flush at the end of this grouping
        }, #end of first grouping
        { #start of the next grouping
          ...
        } #end of the next grouping
    ]
    
The basic structure is a list of dictionaries.  Each dictionary represents a "group" of objects.
Each object can have one or more records associated with it.

Flushing and Committing
------------------------
If you provide keys with the name commit and flush to the grouping, the session will 
be committed or flushed accordingly.  One thing to note is that if you define any 
relationships within a record, the grouping will be flushed at that point.  
There is no way to avoid this flush.

About Your Model
------------------

BootAlchemy expects that your models have the ability to pass a set of keyword pairs into
your objects.  DeclarativeBase does this automatically, but if you have the standard SqlAlchemy object
definitions, you may want to augment them with a superclass that looks something like this::

    class DBObject(object):
        """
        This is the DBObject class which all other model classes rely on.
        It allows us to instantiate an object with attributes simply by passing
        them into the constructor.
    
        """
        def __init__(self, **kw):
            for item, value in kw.iteritems():
                setattr(self, item, value)

Storing References (think Autoincrement)
-----------------------------------------
You can store references within your records and then use them later.  For instance, let's
store the genre_id, and use it in a movie define.::

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

produces::

   [('Back to the Future', 'sci-fi')]

If you provide a string with a '&' as one of the attribute values,
boot alchemy will store the value of this item in a reference dictionary.  This is then
retrieved when you provide a string starting with '*'.  The reference is set after the
object is flushed to the database, which means that if you have an auto-incrementing
field, it will be set to the incremented value.
Notice that the genre was populated within the movie object.  This is more of an affect of the
ORM than of bootalchemy, but we will see next how boot alchemy itself takes advantage of the
inner workings of the orm.  

Relationships
----------------
Since we have an object mapping to tables, and not just tables in our database, we cann
assign actual objects to the reference dictionary, not just id's.  Here is another
way to assign the genre to our movie::

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

produces::

    #[('Back to the Future', 'sci-fi'), ('The Big Lebowski', 'comedy')]


This also works for one-to-many and many-to-many relationships.  If you profide a list of
objects, bootalchemy will retrieve them from the reference dictionary and attach them
to the proper attribute of your object.  Lets assign some directors to a movie.::

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

produces::

    [('Back to the Future', []), ('The Big Lebowski', []), ('The Matrix', ['Andy Wachowski', 'Larry Wachowski'])]
    
Yaml
---------
BootAlchemy has a very simple data structure because we wanted it to work with YAML.  You can easily
provide a yaml string to BootAlchemy for parsing.  Yaml has the benefit that it is a standard that
non-python developers can follow, and has a large set of functionality outside of what you can
do with simple strings in dictionaries.  Take a look at the spec:  http://www.yaml.org/spec/ .  Here is
an example Yaml string loaded into the database with bootalchemy::

    from bootalchemy.loader import YamlLoader

    data = """
    - Movie:
        - description: An office employee and a soap salesman build a global organization to help vent male aggression.,
          title: Fight Club,
          release_date: 1999-10-14
          genre: "*action"
      flush:
    """
    
    action = session.query(Genre).filter(Genre.name=='action').first()
    loader = YamlLoader(model, references={'action':action})
    loader.loads(session, data)
    movies = session.query(Movie).all()
    print [(movie.title, movie.genre.name) for movie in movies]

produces::

    [('Back to the Future', 'sci-fi'), ('The Big Lebowski', 'comedy'), ('The Matrix', 'sci-fi'), ('Fight Club,', 'action')]

Notice too that we supplied existing references into this loader since it did not have them from the previous runs.
As a python programmer, you might find yaml pretty refreshing.  It has simple syntax, rewards brevity, and is sensitive
to indentation.  In many ways it is nicer to set data up within than Python, as many of the quotes have been eliminated.
PyYaml supplies readable debug output in case your yaml syntax is incorect.  Here is an example where a stray "}" has been
left at the end of the genre line::

    yaml.parser.ParserError: while parsing a block mapping
      in "<string>", line 3, column 7:
            - description: An office employee  ... 
              ^
    expected <block end>, but found '}'
      in "<string>", line 6, column 23:
              genre: "*action"}
                              ^


:class:`YamlLoader` also provides a loadf function which takes a file name and loads it into the database.

Json!
------
One of the great things about YAML is that JSon is a subset of the specification for Yaml.  Often times I find
myself with a bunch of data that I have hand-entered into a database, and I want to replicate that data for some
kind of development process.  I can output the database data into Json using my browser and then inject it as a
stream into my bootloader program.  


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

