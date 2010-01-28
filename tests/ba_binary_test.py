import sqlalchemy as sa
import sqlalchemy.types as sa_types
import sqlalchemy.orm as orm

metadata = sa.MetaData()

simple_table = sa.Table('simple', metadata,
    sa.Column('simp_id', sa_types.Integer, primary_key=True),
    sa.Column('hash', sa_types.String(128)),
)


class Simple(object):
    def __init__(self, hash=None):
        self.hash = hash

simple_mapper = orm.mapper(Simple, simple_table)

from bootalchemy.loader import YamlLoader

class model:
    Simple = Simple

s = '''
-
 Simple:
    - {hash: '1yrdLS8QDAKYe28hBRURx3JEhLg='}
'''

if __name__ == '__main__':
    engine = sa.create_engine('postgresql+psycopg2://localhost/ba_binary_test')

    metadata.bind = engine
    metadata.create_all(checkfirst=True)

    session = orm.sessionmaker()()

    loader = YamlLoader(model)
    loader.loads(session, s)

    session.commit()
