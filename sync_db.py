# -*- coding: utf-8 -*-
from sqlalchemy import *

from model import *
from conn import engine, session
from datetime import datetime

engine.echo = True;

metadata.drop_all(engine)
metadata.create_all(engine, checkfirst=False)

session.query(EventType).delete()
session.add(EventType('live', u'Концерт'))

it = ImageType(Entity.EVENT, u'Афиша события');
it.max_thumb_width = 126;
it.max_thumb_height = 126;
it.transform_type = ImageType.TRANSFORM_STD;
it.base_dir = 'event';
session.add(it)

for e in session.query(EventType):
    print e

event_type = e
e = Event(event_type, 'First')
e.time_start = datetime.now()
session.add(e)

session.commit()

print e.event_id
print e.main_image
print e.time_start
