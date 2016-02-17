#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wtforms
from flask import Flask
from wtforms import validators
from dynamic_obj.dynamic_object import DynamicObject, Segment

class TestObj(DynamicObject):
    domain = Segment(wtforms.StringField, [validators.Length(min=4, max=20, message="domain invalid")])
    ip = Segment(wtforms.StringField, [validators.Length(min=7, max=15, message="ip invalid")])

    def perform(self, *args, **kwargs):
        return {"url": "http://www.360.cn"}

app = Flask(__name__)
if __name__ == '__main__':
    DynamicObject.create_api(TestObj, app=app)
    app.run(host = '0.0.0.0', port = 7779,
            debug=True,
            threaded = True)