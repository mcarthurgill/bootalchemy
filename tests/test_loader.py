import os
from bootalchemy.loader import YamlLoader
from pprint import pprint, pformat

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

import model
engine = create_engine('sqlite://')
model.metadata.bind = engine

model.metadata.create_all()

Session = sessionmaker(bind=engine)

test_file = os.path.dirname(__file__)+'/data/test_data.yaml'
nested_test_file = os.path.dirname(__file__)+'/data/nested_data.yaml'

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
                     {'display_name': None, 'group_id': 3, 'name': u'players'},
                     {'display_name': None, 'group_id': 4, 'name': u'\xe0\xe9\xef\xf4u'},
                     {'display_name': None, 'group_id': 5, 'name': u'bullies'}
                    ], pprint(r)
        users = self.session.query(model.User).all()
        r =  [x .json for x in users]
        assert r == [{'display_name': None,
                      'email_address': None,
                      'user_id': 1,
                      'user_name': u'peggy',
                      'active': False},
                     {'display_name': None,
                      'email_address': None,
                      'user_id': 2,
                      'user_name': u'sue',
                      'active': True },
                     {'display_name': None,
                      'email_address': None,
                      'user_id': 3,
                      'user_name': u'bobby',
                      'active': False},
                     {'display_name': None,
                      'email_address': None,
                      'user_id': 4,
                      'user_name': u'billy',
                      'active': True},
                     {'display_name': None,
                      'email_address': None,
                      'user_id': 5,
                      'user_name': u'\xe9cho',
                      'active': False},
                     {'display_name': None,
                      'email_address': None,
                      'user_id': 6,
                      'user_name': u'bully',
                      'active': True},
                     ], pprint(r)
        user = self.session.query(model.User).get(4)
        r = [group.name for group in user.groups]
        assert r == [u'students', u'players'], r
        
    def test_init_model_string(self):
        self.loader = YamlLoader(['model'])
        self.session = Session()
        s = open(test_file).read()
        self.loader.loads(self.session, s)
        
    def test_nested_data(self):
        normal_file = open(test_file).read()
        self.loader.loads(self.session, normal_file)
        normal_groups = self.session.query(model.Group).all()
        normal_groups_json = [x.json for x in normal_groups]
        normal_users = self.session.query(model.User).all()
        normal_users_json = [x.json for x in normal_users]
        
        self.tearDown()
        
        nested_file = open(nested_test_file).read()
        self.loader.loads(self.session, nested_file)
        nested_groups = self.session.query(model.Group).all()
        nested_groups_json = [x.json for x in nested_groups]
        nested_users = self.session.query(model.User).all()
        nested_users_json = [x.json for x in nested_users]
        
        # groups
        assert normal_groups_json == nested_groups_json, \
            '\n' + pformat(normal_groups_json) + '\n\n-^- not equal to -v-\n\n' + pformat(nested_groups_json)
        
        # users
        assert normal_users_json == nested_users_json, \
            '\n' + pformat(normal_users_json) + '\n\n-^- not equal to -v-\n\n' + pformat(nested_users_json)
        
