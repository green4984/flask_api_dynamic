#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wtforms
from wtforms import validators
from dynamic_obj.dynamic_object import DynamicObject, Segment

class TestObj(DynamicObject):
    domain = Segment(wtforms.StringField, [validators.Length(min=4, max=20, message="domain invalid")])
    ip = Segment(wtforms.StringField, [validators.Length(min=7, max=15, message="ip invalid")])

    def perform(self, *args, **kwargs):
        return {"url": "http://www.360.cn"}


import os
import sys
import unittest

# add root path to sys.path
path = os.path.abspath(os.path.dirname(__file__))
if path not in sys.path:
    sys.path.insert(0, path)
path = os.path.split(path)
if path not in sys.path:
    sys.path.insert(0, path[0])
from flask import Flask
app = Flask(__name__)

if __name__ == '__main__':
    from Tests import init_test
    init_test(app)
    DynamicObject.create_api(TestObj, app=app)
    testsuite = unittest.TestLoader().discover('Tests')
    unittest.TextTestRunner(verbosity=2).run(testsuite)
