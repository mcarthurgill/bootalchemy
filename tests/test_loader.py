import os
from bootalchemy.loader import YamlLoader
from pprint import pprint

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import model
engine = create_engine('sqlite://')
model.metadata.bind = engine

model.metadata.create_all()

Session = sessionmaker(bind=engine)

test_file = os.path.dirname(__file__)+'/data/test_data.yaml'


class TestYamlLoader:
    
    def setup(self):
        self.loader = YamlLoader(model)
        self.session = Session()
    
    def tearDown(self):
        for user in self.session.query(model.User).all():
            self.session.delete(user)
        for user in self.session.query(model.Group).all():
            self.session.delete(user)
        self.session.flush()
        
    def test_loads(self):
        s = open(test_file).read()
        self.loader.loads(self.session, s)
        groups = self.session.query(model.Group).all()
        r =  [x .json for x in groups]
        assert r == [{'display_name': None, 'group_id': 1, 'name': u'teachers'},
                     {'display_name': None, 'group_id': 2, 'name': u'students'},
                     {'display_name': None, 'group_id': 3, 'name': u'players'}], pprint(r)
        users = self.session.query(model.User).all()
        r =  [x .json for x in users]
        assert r == [{'display_name': None,
                      'email_address': None,
                      'user_id': 1,
                      'user_name': u'peggy'},
                     {'display_name': None,
                      'email_address': None,
                      'user_id': 2,
                      'user_name': u'sue'},
                     {'display_name': None,
                      'email_address': None,
                      'user_id': 3,
                      'user_name': u'bobby'},
                     {'display_name': None,
                      'email_address': None,
                      'user_id': 4,
                      'user_name': u'billy'}], pprint(r)
        user = self.session.query(model.User).get(4)
        r = [group.name for group in user.groups]
        assert r == [u'students', u'players'], r
        
    def test_init_model_string(self):
        self.loader = YamlLoader(['model'])
        self.session = Session()
        s = open(test_file).read()
        self.loader.loads(self.session, s)
