# -*- coding: utf-8 -*-
from flask import Flask
from flask import Blueprint

from .dynamic_object_base import DynamicObjectBase


class DyManager(object):
    __blueprints = {}
    __form_class = {}
    def __init__(self, app=None):
        if app:
            self.app = app
            self.init_app(app)

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            orig = super(DyManager, cls)
            setattr(cls, '_instance', orig.__new__(cls, *args, **kwargs))
        return getattr(cls, '_instance')

    def init_app(self, app=None):
        if app:
            self.app = app
        for name, bp_dict in self.__blueprints.iteritems():
            for bp, val in bp_dict.iteritems():
                if not val:
                    val = True
                    self.app.register_blueprint(bp)

    def create_api(self, object_class, **kwargs):
        app = kwargs.pop('app', None)
        self.create_api_blueprint(object_class, **kwargs)
        self.init_app(app)

    def create_api_blueprint(self, obj_class, url_prefix='/api'):
        """ register blueprint """
        assert issubclass(obj_class, DynamicObjectBase)
        name = getattr(obj_class, "__obj_name__", obj_class.__name__).lower()
        if name in self.__blueprints:
            return self.__blueprints.get(name).keys()[0]
        blueprint = Blueprint(obj_class.__name__, __name__, url_prefix=url_prefix)
        view_func = obj_class.as_view(name)
        blueprint.add_url_rule('/{0}'.format(name), view_func=view_func)
        blueprint.add_url_rule('/{0}/'.format(name), view_func=view_func)
        self.__blueprints.setdefault(name, {blueprint: False})
        return blueprint
