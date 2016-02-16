# -*- coding: utf-8 -*-
import wtforms
from flask import Blueprint
from flask import current_app
from flask import make_response, jsonify
from flask import request
from flask.views import MethodView, MethodViewType


class DynamicObjectMeta(type):
    ''' define the metaclass for dynamic object for create,
    record the segment fields in __fields just for no need
    to use 'dir(self)' for subclass in for loop
    '''

    def __new__(cls, name, base, attrs):
        if base[0] is MethodView:
            # cls is DynamicObject
            t = type.__new__(cls, name, base, attrs)
        else:  # cls is the subclass of DynamicObject
            fields = []
            # add Segment to __fields
            for key, val in attrs.iteritems():
                if not key.startswith('__') and isinstance(val, Segment):
                    fields.append(key)
            attrs.setdefault('__fields', fields)
            t = type.__new__(cls, name, base, attrs)
        return t
        # def __init__(cls, name, base, attrs):
        #    type.__init__(cls, name, base, attrs)


# avoid metaclass conflict
class DynamicMeta(DynamicObjectMeta, MethodViewType):
    pass


class DynamicObject(MethodView):
    """dynamic create object during the flask is already running
       which can define class by user if you like
    """
    __metaclass__ = DynamicMeta
    __register_class = set()
    decorators = []

    def perform(self, *args, **kwargs):
        raise NotImplementedError("class which inherit DynamicObject should implement `perform` method")

    def get(self, *args, **kwargs):
        req_args = request.args
        if len(req_args) > 0:
            form = self.__make_form(req_args)
            if form.validate():
                ret_val = self.perform()
                if ret_val is None:
                    raise ValueError

                if isinstance(ret_val, dict):
                    if "data" not in ret_val:
                        ret_val = {"data": ret_val}
                elif isinstance(ret_val, (str, unicode)):
                    ret_val = {"data": list(ret_val)}
                elif isinstance(ret_val, (tuple, list)):
                    ret_val = {"data": list(ret_val)}
                return make_response(jsonify(ret_val))
            else:
                return make_response(jsonify({"error": form.errors}))
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
            fields = {"fields": fields}
            return make_response(jsonify(fields))

    @classmethod
    def create_api(cls, obj_class, url_prefix='/api', app=None):
        name = getattr(obj_class, "__obj_name__", obj_class.__name__).lower()
        if name in cls.__register_class:
            return
        app = current_app if not app else app
        blueprints = Blueprint(obj_class.__name__, __name__, url_prefix=url_prefix)
        cls.__register_class.add(name)
        view_func = obj_class.as_view(name)
        blueprints.add_url_rule('/{0}/'.format(name), view_func=view_func)
        app.register_blueprint(blueprints)

    def __make_form(self, req_args):
        """ make the form by query parameters"""
        fields = {}
        for seg in getattr(self, '__fields'):
            if seg in req_args:
                segment = getattr(self, seg)
                fields[seg] = segment.type(seg, validators=segment.validators)
        name = getattr(self, "__obj_name__", repr(self.__class__.__name__))
        form_class = type(name + 'Form', (wtforms.Form,), fields)
        # return the instance of form_class
        return form_class(req_args)


class Segment(object):
    __slots__ = ('type', 'validators')

    def __init__(self, segment_type, validator=None):
        """ define for query field
        :type validator: list
        """
        validator = validator or []
        self.type = segment_type
        self.validators = validator if isinstance(validator, list) else [validator, ]
