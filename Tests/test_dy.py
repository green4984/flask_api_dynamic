# -*- coding: utf-8 -*-
import simplejson as json
from flask import current_app as app
from wtforms import StringField
from wtforms.validators import Length

from Tests import TestCase
from dynamic_obj.dynamic_object import DynamicObject, Segment


class TestObj(TestCase):
    def test_get(self):
        # test get field
        rv = self.get("/api/testobj")
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("fields"))
        self.assertGreater(len(cont.get("fields")), 1)

        # invalid query, domain and ip is too short
        rv = self.get("/api/testobj?domain=www&ip=1")
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("error"))
        self.assertGreaterEqual(len(cont.get("error")), 1)

        rv = self.get("/api/testobj?domain=www.360.cn")
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("data"))
        self.assertGreaterEqual(len(cont.get("data")), 1)

        # add DyClass
        DynamicObject.create_api(DyClass)

        DynamicObject.create_api(Show)
        rv = self.get("/api/show")
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("fields"))
        self.assertGreaterEqual(len(cont.get("fields")), 1)

        rv = self.get("/api/show?url=1")
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("data"))
        self.assertGreaterEqual(len(cont.get("data")), 1)
        self.output(cont.get("data").get("url"))


class DyClass(DynamicObject):
    host = Segment(StringField, [Length(min=1, max=20)])

    def perform(self, *args, **kwargs):
        return {"dynamic": "dynamic add DyClass"}


class Show(DynamicObject):
    url = Segment(StringField, [Length(min=0)])

    def perform(self, *args, **kwargs):
        urls = []
        for rule in app.url_map._rules:
            urls.append(str(rule))
        return {"url": urls}
