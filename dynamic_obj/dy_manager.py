# -*- coding: utf-8 -*-
from flask import Flask
from flask import Blueprint

from .dynamic_object_base import DynamicObjectBase


class DyManager(object):
    __blueprints = {}
    app = None
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
        assert app
        self.app = app
        for name, bp_list in self.__blueprints.iteritems():
            self.__register_blueprint(name, bp_list[0], app)

    def create_api(self, object_class, **kwargs):
        return self.create_api_blueprint(object_class, **kwargs)

    def create_api_blueprint(self, obj_class, url_prefix='/api', app=None):
        """ register blueprint """
        assert issubclass(obj_class, DynamicObjectBase)
        name = getattr(obj_class, "__obj_name__", obj_class.__name__).lower()
        if name in self.__blueprints:
            return self.__blueprints.get(name)[0]
        blueprint = Blueprint(obj_class.__name__, __name__, url_prefix=url_prefix)
        view_func = obj_class.as_view(name)
        blueprint.add_url_rule('/{0}'.format(name), view_func=view_func)
        blueprint.add_url_rule('/{0}/'.format(name), view_func=view_func)
        self.__register_blueprint(name, blueprint, app)
        return blueprint

    def __register_blueprint(self, name, blueprint, app=None):
        app = app or self.app
        if name not in self.__blueprints:
            self.__blueprints.setdefault(name, [blueprint, False])
        if app and not self.__blueprints[name][1]:
            self.__blueprints[name][1] = True
            app.register_blueprint(blueprint)
