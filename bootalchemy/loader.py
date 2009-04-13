from yaml import load

class Loader(object):
    pass


class YamlLoader(Loader):
    
    def __init__(self, model, references=None):
        self.model = model
        if references is None:
            self._references = {}
        else:
            self._references = references
        
    def clear(self):
        self._references = {}
    
    def create_obj(self, klass, item):
        return klass(**item)
    
    def update_item(self, item):
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('*'):
                id = value[1:]
                item[key] = self._references.get(id, item[key])
            if isinstance(value, list):
                l = []
                for i in value:
                    if isinstance(i, basestring) and i.startswith('*'):
                        id = i[1:]
                        l.append(self._references.get(id, i))
                item[key] = l

    def has_references(self, item):
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                return True

    def add_reference(self, key, obj):
        self._references[key] = obj
            
    def set_references(self, obj, item):
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                self._references[value[1:]] = getattr(obj, key)
            if isinstance(value, list):
                for i in value:
                    if isinstance(value, basestring) and i.startswith('&'):
                        self._references[value[1:]] = getattr(obj, value[1:])

    def loads(self, session, s):
        data = load(s)
        for group in data:
            for name, items in group.iteritems():
                if name in ['flush', 'commit', 'clear']:
                    continue
                klass = getattr(self.model, name)
                for item in items:
                    name = None
                    keys = item.keys()
                    if len(keys) == 1 and keys[0].startswith('&') and isinstance(item[keys[0]], dict):
                        name = keys[0]
                        item = item[name]
                        name = name[1:]
                    items = self.update_item(item)
                    obj = self.create_obj(klass, item)
                    session.add(obj)
                    if name:
                        self.add_reference(name, obj)
                    if self.has_references(item):
                        session.flush()
                        self.set_references(obj, item)

            keys = group.keys()
            if 'flush' in keys:
                session.flush()
            if 'commit' in keys:
                session.commit()
            if 'clear' in keys:
                self.clear()