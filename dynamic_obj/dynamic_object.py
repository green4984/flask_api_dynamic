# -*- coding: utf-8 -*-
import abc

import flask_sqlalchemy
import wtforms
from flask import Blueprint
from flask import Flask
from flask import current_app
from flask import jsonify
from flask import make_response
from flask import request
from flask.views import MethodView, MethodViewType

import exceptions


class DynamicObjectMeta(type):
    ''' define the metaclass for dynamic object for create,
    record the segment fields in __fields just for no need
    to use 'dir(self)' for subclass in for loop
    '''

    def __new__(cls, name, base, attrs):
        t = type.__new__(cls, name, base, attrs)
        # if the 'cls' is the subclass of DynamicObject
        if MethodView in base:
            return t
        # subclass may rewrite get, so comment it out
        if attrs.has_key('get'):
            raise exceptions.ImplementedError("subclass of DynamicObject must not implement 'get' method")
        if DynamicObject in base:
            fields = []
            # add Segment to __fields
            for key, val in attrs.iteritems():
                if not key.startswith('__') and isinstance(val, Segment):
                    fields.append(key)
            setattr(t, '__fields', fields)

        if flask_sqlalchemy.Model in base:
            pass
        return t


# avoid metaclass conflict
#class DynamicMeta(abc.ABCMeta, DynamicObjectMeta, MethodViewType):
class DynamicMeta(DynamicObjectMeta, MethodViewType):
    pass


def convert_standard_response(func):
    def decorator(*args, **kwargs):
        resp = make_response()
        try:
            ret_val = func(*args, **kwargs)
            if ret_val is None:
                raise ValueError
            if isinstance(ret_val, dict):
                if "fields" not in ret_val and "data" not in ret_val:
                    ret_val = {"data": [ret_val, ]}
            elif isinstance(ret_val, (str, unicode)):
                ret_val = {"data": [ret_val, ]}
            elif isinstance(ret_val, (tuple, list)):
                ret_val = {"data": [ret_val, ]}
            resp = make_response(jsonify(ret_val))
        except (exceptions.FieldNotSupport, exceptions.CheckException) as e:
            current_app.logger.warning("check query field error : {0}".format(func.func_name), exc_info=1)
            resp = make_response(jsonify({"error": e.message}), 400)
        except Exception as e:
            current_app.logger.warning(exc_info=1)
            resp = make_response(jsonify({"error": e.message}), 400)
        return resp

    return decorator


class DynamicObject(MethodView):
    """dynamic create object during the flask is already running
       which can define class by user if you like
    """
    __metaclass__ = DynamicMeta
    decorators = [convert_standard_response]

    def __init__(self, app=None):
        self.app = app
        self.__register_class = {}
        self.__form_class = {}
        if app:
            self.init_app(app)

    def init_app(self, app):
        assert isinstance(app, Flask)
        self.app = app
        for name, cls in self.__register_class.iteritems():
            if not cls.get("is_registered"):
                app.register_blueprint(cls.get("bp"))
                cls["is_registered"] = True

    #@abc.abstractmethod
    def perform(self, *args, **kwargs):
        raise exceptions.ImplementedError("class which inherit DynamicObject should implement `perform` method")

    def get(self, *args, **kwargs):
        req_args = request.args
        ret_val = None
        if len(req_args) > 0:
            try:
                # FIXME need call DynamicObject instance
                form = super(self.__class__, self)._make_form(req_args)
            except Exception as e:
                pass
            if not form.validate():
                raise exceptions.CheckException(form.errors)
            self.__set_field_value(req_args)
            ret_val = self.perform(*args, **kwargs)
        else:
            # return the obj struct and define
            fields = {}
            for seg in getattr(self, '__fields'):
                segment = getattr(self, seg)
                fields[seg] = {"field_type": segment.type.__name__, "define": {}}
                for validator in segment.validators:
                    for dict_name in validator.__dict__:
                        if dict_name != 'message':
                            fields[seg]["define"][dict_name] = validator.__dict__[dict_name]
            ret_val = {"fields": fields}
        return ret_val

    def options(self):
        return ''

    def create_api(self, object_class, url_prefix='/api'):
        assert self.app
        bp = self.create_api_blueprint(object_class, url_prefix)
        self.app.register_blueprint(bp)

    def create_api_blueprint(self, obj_class, url_prefix='/api'):
        name = getattr(obj_class, "__obj_name__", obj_class.__name__).lower()
        if name in self.__register_class:
            return self.__register_class.get(name)["bp"]
        blueprint = Blueprint(obj_class.__name__, __name__, url_prefix=url_prefix)
        view_func = obj_class.as_view(name)
        blueprint.add_url_rule('/{0}'.format(name), view_func=view_func)
        blueprint.add_url_rule('/{0}/'.format(name), view_func=view_func)
        self.__register_class.setdefault(name, {"is_registered": False, "bp": blueprint})
        return blueprint

    def _make_form(self, req_args):
        """ make the form by query parameters"""
        fields = {}
        support_fields = getattr(self, '__fields')
        unsupport_fileds = [field for field in req_args if field not in support_fields]
        if unsupport_fileds:
            raise exceptions.FieldNotSupport("%s not support" % (unsupport_fileds))
        for seg in req_args.keys():
            segment = getattr(self, seg)
            fields[seg] = segment.type(seg, validators=segment.validators)
        name = getattr(self, "__obj_name__", repr(self.__class__.__name__))
        fields.keys().sort()
        name = 'Form' + name + str(fields.keys())
        base = self.__class__.__base__
        form_class = base._form_class.get(name, None) or type(name, (wtforms.Form,), fields)
        base._form_class.setdefault(name, form_class)
        # return the instance of form_class
        return form_class(req_args)

    def __set_field_value(self, req_args):
        relation_dict = {
            wtforms.StringField: str,
            wtforms.IntegerField: int,
            wtforms.DecimalField: float,
        }
        for field in getattr(self, '__fields'):
            seg = getattr(self, field)
            val = None
            if seg.type in relation_dict:
                val = relation_dict.get(seg.type)(req_args.get(field))
            setattr(self, field, val)


class Segment(object):
    __slots__ = ('type', 'validators')

    def __init__(self, segment_type, validator=None):
        """ define for query field
        :type validator: list
        """
        validator = validator or []
        self.type = segment_type
        self.validators = validator if isinstance(validator, list) else [validator, ]
