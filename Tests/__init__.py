# -*- coding: utf-8 -*-
# include all skyeye-master unit tests in this package
from __future__ import absolute_import


import unittest
import logging
from flask import Flask
app = None
#from flask import current_app as app
from flask import _app_ctx_stack, _request_ctx_stack
def init_test(app_outsite):
    global app
    app = app_outsite

class TestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        global app
        assert isinstance(app, Flask)
        self.app = app.test_client()
        super(TestCase, self).__init__(methodName=methodName)

    def setUp(self):
        #self.output("running %s test!", self.__repr__())
        assert app is not None, "must run before run unittest !"
        from flask import _app_ctx_stack as ctx
        if not ctx.top:
            ctx.push(app.app_context())

    def tearDown(self):
        #self.output("finish %s test!", self.__repr__())
        pass

    def output(self, msg, *args, **kwargs):
        logging.warn(msg, *args, **kwargs)

    def get(self, *args, **kwargs):
        kwargs.setdefault("follow_redirects", True)
        rv = self.app.get(*args, **kwargs)
        self.assertIsNotNone(rv, "response is None!!!")
        return rv

    # add app_context when call method in subclass
    def __getattribute__(self, item):
        with app.app_context():
            return super(TestCase, self).__getattribute__(item)
