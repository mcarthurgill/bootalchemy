from yaml import load
import sys
import logging
from pprint import pformat
from converters import timestamp
from sqlalchemy.orm import class_mapper
from sqlalchemy import Unicode, Date, DateTime, Time, Integer, Boolean

log = logging.Logger('bootalchemy', level=logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)
class Loader(object):
    """
       Basic Loader 
       
       *Arguments*
          model
            list of classes in your model.
          references
            references from an sqlalchemy session to initialize with.
          check_types
            introspect the target model class to re-cast the data appropriately.
    """
    default_encoding = 'utf-8'
    
    def __init__(self, model, references=None, check_types=True):
        self.source = 'UNKNOWN'
        self.model = model
        if references is None:
            self._references = {}
        else:
            self._references = references
        
        if not isinstance(model, list):
            model = [model]
        
        self.modules = []
        for item in model:
            if isinstance(item, basestring):
                self.modules.append(__import__(item))
            else:
                self.modules.append(item)
        
        self.check_types = check_types
        
    def clear(self):
        """
        clear the existing references
        """
        self._references = {}
    
    def create_obj(self, klass, item):
        """
        create an object with the given data
        """
        # xxx: introspect the class constructor and pull the items out of item that you can, assign the rest
        return klass(**item)
    
    def update_item(self, item):
        new_item = item.copy()
        for key, value in new_item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                new_item[key] = None
            if isinstance(value, basestring) and value.startswith('*'):
                id = value[1:]
                new_item[key] = self._references.get(id, new_item[key])
            if isinstance(value, list):
                l = []
                for i in value:
                    if isinstance(i, basestring) and i.startswith('*'):
                        id = i[1:]
                        l.append(self._references.get(id, i))
                        continue
                    l.append(i)
                new_item[key] = l
        return new_item

    def has_references(self, item):
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                return True

    def add_reference(self, key, obj):
        """
        add a reference to the internal reference dictionary
        """
        self._references[key[1:]] = obj
            
    def set_references(self, obj, item):
        """
        extracts the value from the object and stores them in the reference dictionary.
        """
        for key, value in item.iteritems():
            if isinstance(value, basestring) and value.startswith('&'):
                self._references[value[1:]] = getattr(obj, key)
            if isinstance(value, list):
                for i in value:
                    if isinstance(value, basestring) and i.startswith('&'):
                        self._references[value[1:]] = getattr(obj, value[1:])

    def _check_types(self, klass, obj):
        if not self.check_types:
            return obj
        mapper = class_mapper(klass)
        for table in mapper.tables:
            for key in obj.keys():
                col = table.columns.get(key, None)
                value = obj[key]
                if col is not None and isinstance(col.type, (Date, DateTime, Time)) and isinstance(value, basestring):
                    obj[key] = timestamp(value)
                    continue
                if col is not None and isinstance(col.type, Unicode) and isinstance(value, str):
                    obj[key] = unicode(value, self.default_encoding)
                    continue
                #if col is not None and isinstance(col.type, Integer) and isinstance(value, basestring):
                #    obj[key] = int(value)
                #    continue
                #if col is not None and isinstance(col.type, Boolean) and isinstance(value, basestring):
                #    obj[key] = bool(value)
                #    continue
                #if col is not None and key == 'stat_type_type':
                #    import ipdb; ipdb.set_trace();
        return obj
        
    def from_list(self, session, data):
        """
        extract data from a list of groups in the form:
        
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

        """
        klass = None
        item = None
        group = None
        try:
            for group in data:
                for name, items in group.iteritems():
                    if name in ['flush', 'commit', 'clear']:
                        continue
#                    klass = getattr(self.model, name)
                    klass = None
                    for module in self.modules:
                        try:
                            klass = getattr(module, name)
                            break;
                        except AttributeError, e:
                            pass
                    # check that the class was found.
                    if klass is None:
                        raise AttributeError('Class %s from %s not found in any module' % (name , self.source))
                    for item in items:
                        ref_name = None
                        keys = item.keys()
                        if len(keys) == 1 and keys[0].startswith('&') and isinstance(item[keys[0]], dict):
                            ref_name = keys[0]
                            item = item[ref_name]
                            name = name[1:]
                        new_item = self.update_item(item)
                        new_item = self._check_types(klass, new_item)
                        obj = self.create_obj(klass, new_item)
                        session.add(obj)
                        if ref_name:
                            self.add_reference(ref_name, obj)
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
                    
        except AttributeError, e:
            if hasattr(item, 'iteritems'):
                missing_refs = [(key, value) for key, value in item.iteritems() if isinstance(value,basestring) and value.startswith('*')]
                self.log_error(e, data, klass, item)
                if missing_refs:
                    log.error('*'*80)
                    log.error('It is very possible you are missing a reference, or require a "flush:" between blocks to store the references')
                    log.error('here is a list of references that were not accessible (key, value): %s'%missing_refs)
                    log.error('*'*80)
            else:
                self.log_error(e, data, klass, item)
        except Exception, e:
            self.log_error(sys.exc_info()[2], data, klass, item)
            raise
    def log_error(self, e, data, klass, item):
            log.error('error occured while loading yaml data with output:\n%s'%pformat(data))
            log.error('references:\n%s'%pformat(self._references))
            log.error('class: %s'%klass)
            log.error('item: %s'%item)
            import traceback
            log.error(traceback.format_exc(e))
        
class YamlLoader(Loader):
    
    def loadf(self, session, filename):
        self.source = filename
        s = open(filename).read()
        return self.loads(session, s)
    
    def loads(self, session, s):
        data = load(s)
        if data:
            return self.from_list(session, data)
