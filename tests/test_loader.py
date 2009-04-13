import os
from bootalchemy.loader import YamlLoader
from pprint import pprint

test_file = os.path.dirname(__file__)+'/data/test_data.yaml'

class MochObj(object):
    
    def __init__(self, **kw):
        for key, value in kw.iteritems():
            setattr(self, key, value)
            
    @property
    def json(self):
        d = {}
        for key, value in self.__dict__.iteritems():
            if not key.startswith('_'):
                d[key] = value
        return d
    
class User(MochObj):pass

class Group(MochObj):pass


class model:
    User = User
    Group = Group

class MochSession(object):
    
    def __init__(self):
        self._objects = []
        self._saved_objects = []

    def add(self, obj):
        self._objects.append(obj)
        setattr(obj, obj.__class__.__name__.lower()+'_id', len(self._objects))
        
    def commit(self):
        pass
    def flush(self):
        self._saved_objects.extend(self._objects)
    
    def clear(self):
        self._objects = []

class TestYamlLoader:
    
    def setup(self):
        self.loader = YamlLoader(model)
        self.session = MochSession()
        
    def test_loads(self):
        s = open(test_file).read()
        self.loader.loads(self.session, s)
        r =  [x.json for x in self.session._objects[:-1]]
        assert r == [{'name': 'peggy', 'user_id': 1},
                     {'name': 'sue', 'user_id': 2},
                     {'admin_id': 1, 'group_id': 3, 'name': 'teachers'},
                     {'group_id': 4, 'name': 'students'},
                     {'group_id': 5, 'name': 'players'},
                     {'groups': [4, 5], 'name': 'bobby', 'user_id': 6}], pprint(r)
        last_r = self.session._objects[-1]
        assert len(last_r.groups) == 2, last_r
        assert last_r.groups[0].json ==  {'group_id': 4, 'name': 'students'}, last_r.groups[0].json
