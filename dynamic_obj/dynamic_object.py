# -*- coding: utf-8 -*-
import wtforms
from flask import Blueprint
from flask import request
from flask import current_app
from flask.views import MethodView
from flask import make_response, jsonify


class DynamicObject(MethodView):
    __register_class = set()
    def perform(self, *args, **kwargs):
        raise NotImplementedError("class which inherit DynamicObject should implement `perform` method")

    def get(self, *args, **kwargs):
        req_args = request.args
        if len(req_args) > 0:
            # query the obj
            fields = {}
            for seg in dir(self):
                if not isinstance(getattr(self, seg), Segment):
                    continue
                segment = getattr(self, seg)
                assert isinstance(segment, Segment)
                if seg in req_args:
                    fields[seg] = segment.type(seg, validators=segment.validators)
            form_class = self.__make_form(fields)
            form = form_class(req_args)
            if form.validate():
                ret_val = self.perform()
                if ret_val is None:
                    raise ValueError

                if isinstance(ret_val, dict):
                    if not ret_val.has_key("data"):
                        ret_val = {"data": ret_val}
                elif isinstance(ret_val, (str, unicode)):
                    pass
                elif isinstance(ret_val, (tuple, list)):
                    ret_val = {"data": list(ret_val)}
                return make_response(jsonify(ret_val))
            else:
                return make_response(jsonify({"error": form.errors}))
        else:
            # return the obj struct and define
            fields = {}
            for seg in dir(self):
                if not isinstance(getattr(self, seg), Segment):
                    continue
                segment = getattr(self, seg)
                assert isinstance(segment, Segment)
                fields[seg] = {"field_type": segment.type.__name__, "define": {}}
                for validator in segment.validators:
                    for dict_name in validator.__dict__:
                        if dict_name != 'message':
                            fields[seg]["define"][dict_name] = validator.__dict__[dict_name]
            fields = {"fields": fields}
            return make_response(jsonify(fields))

    @classmethod
    def create_api(cls, objClass, url_prefix='/api', app=None):
        assert issubclass(objClass, DynamicObject)
        blueprints = Blueprint(objClass.__name__, __name__, url_prefix=url_prefix)
        name = getattr(objClass, "__obj_name__", objClass.__name__).lower()
        app = current_app if not app else app
        if name not in cls.__register_class:
            cls.__register_class.add(name)
            view_func = objClass.as_view(name)
            #blueprints.add_url_rule('/{0}'.format(name), view_func=view_func)
            blueprints.add_url_rule('/{0}/'.format(name), view_func=view_func)
            app.register_blueprint(blueprints)

    def __make_form(self, field_dict={}):
        name = getattr(self, "__obj_name__", repr(self.__class__.__name__))
        return type(name + 'Form', (wtforms.Form,), field_dict)


class Segment(object):
    def __init__(self, segment_type, validator=[]):
        self.type = segment_type
        if validator is list:
            self.validators = validator
        else:
            self.validators = [validator, ]
