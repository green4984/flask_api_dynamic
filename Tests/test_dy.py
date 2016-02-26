# -*- coding: utf-8 -*-
import flask_sqlalchemy
import simplejson as json
from flask import current_app as app
from wtforms import StringField
from wtforms.validators import Length

from Tests import TestCase
from dynamic_obj.dynamic_object_base import DynamicObjectBase, Segment
from run_test import dy


class TestObj(TestCase):
    def test_get(self):
        # test get field
        rv = self.get("/api/testobj")
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("fields"))
        self.assertGreater(len(cont.get("fields")), 1)

        # invalid query, domain and ip is too short
        rv = self.get("/api/testobj?domain=www&ip=1")
        self.assertGreaterEqual(rv.status_code, 400)
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("error"))
        self.assertGreaterEqual(len(cont.get("error")), 1)

        rv = self.get("/api/testobj?domain=www&ip=1")
        self.assertGreaterEqual(rv.status_code, 400)
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("error"))
        self.assertGreaterEqual(len(cont.get("error")), 1)

        rv = self.get("/api/testobj?domain=www.360.cn&a=1")
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("error"))
        self.assertIn('not support', cont['error'])

        rv = self.get("/api/testobj?domain=www.360.cn")
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("data"))

        # add DyClass
        dy.create_api(DyClass)

        dy.create_api(Show)
        rv = self.get("/api/show")
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("fields"))
        self.assertGreaterEqual(len(cont.get("fields")), 1)

        rv = self.get("/api/show?url=1")
        cont = json.loads(rv.data)
        self.assertTrue(cont.has_key("data"))
        self.assertGreaterEqual(len(cont.get("data")), 1)
        self.output(cont.get("data")[0].get("url"))

    def test_db(self):
        dy.create_api(DbShow)
        rv = self.get("/api/dbshow?name=John")
        cont = json.loads(rv.data)
        self.assertIn('John', cont.get("data"))


class DyClass(DynamicObjectBase):
    host = Segment(StringField, [Length(min=1, max=20)])

    def perform(self, *args, **kwargs):
        return {"dynamic": "dynamic add DyClass"}


class Show(DynamicObjectBase):
    url = Segment(StringField, [Length(min=0)])

    def perform(self, *args, **kwargs):
        urls = []
        for rule in app.url_map._rules:
            urls.append(str(rule))
        return {"url": urls}


class DbShow(DynamicObjectBase, flask_sqlalchemy.Model):
    name = Segment(StringField, [])

    def perform(self, *args, **kwargs):
        return self.name


class AddClass(DynamicObjectBase):
    class_name = Segment(StringField, [Length(min=1, max=10)])
    ret_val = Segment(StringField, [Length(min=1)])

    def perform(self, *args, **kwargs):
        return self.ret_val
