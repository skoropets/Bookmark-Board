from sqlalchemy import *
from sqlalchemy import event as alchemy_event
from sqlalchemy.orm import relationship, backref, collections
from sqlalchemy.ext.declarative import declarative_base

from file_image import FileProcess,ImageTransform, mkImageWithFrame
import os

class MyBase(object):
    pass

def file_column(column):
    def set_event_listner(target, value, oldvalue, initiator):
        if oldvalue:
            full_path = FileProcess.fullPath(oldvalue)
            if (os.path.isfile(full_path)):
                os.unlink(full_path)
    alchemy_event.listen(column, 'set', set_event_listner)

Base = declarative_base(cls=MyBase)
metadata = Base.metadata

class EventSourceType:
    EMPTY = 0
    STD = 1
    LASTFM = 2
    VK = 3

class Entity:
    EVENT = 1

event_persons = Table('event_persons', metadata,
    Column('event_id', Integer, ForeignKey('events.event_id')),
    Column('person_id', Integer, ForeignKey('persons.person_id')),
    Column('order', Integer)
)

event_links = Table('event_links', metadata,
    Column('event_id', Integer, ForeignKey('events.event_id')),
    Column('link_id', Integer, ForeignKey('links.link_id')),
    Column('order', Integer)
)

class Event(Base):
    __tablename__ = 'events'

    event_id = Column(Integer, Sequence('event_id_seq'), primary_key=True)
    place_id = Column(Integer, ForeignKey('places.place_id')) 
    main_image_id = Column(Integer, ForeignKey('images.image_id'))
    title = Column(String(255))
    time_start = Column(DateTime)
    time_end = Column(DateTime)
    description = Column(Text)
    event_type_id = Column(Integer, ForeignKey('event_types.event_type_id')) 
    source_type = Column(Integer) 
    source_url = Column(String(255))
    last_status = Column(Integer)

    place = relationship("Place", backref=backref('events'))
    main_image = relationship("Image")
    event_type = relationship("EventType")
    event_status_list = relationship("EventStatus", backref=backref('event'))
    persons = relationship('Person', secondary=event_persons, backref=backref('events'))
    links = relationship('Link', secondary=event_links)

    def __init__(self, event_type, title = None):
        self.event_type = event_type
        if title is None:
            title = ''
        self.title = title

    def __repr__(self):
        return "Event('%s')" % (self.title)

def event_status_append_listener(target, value, initiator):
    target.last_status = value.status

alchemy_event.listen(Event.event_status_list, 'append', event_status_append_listener)

class EventStatus(Base):
    EMPTY = 0
    WANT = 1
    MAYBE = 2

    __tablename__ = 'event_status'

    event_status_id = Column(Integer, Sequence('event_status_id_seq'), primary_key=True) 
    event_id = Column(Integer, ForeignKey('events.event_id'))
    time_change = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP')) 
    status = Column(Integer) 
    description = Column(Text)

    def __init__(self, status):
        self.status = status

    def __repr__(self):
        return "EventStatus('%s')" % (self.status)


class Place(Base):
    __tablename__ = 'places'

    place_id = Column(Integer, Sequence('place_id_seq'), primary_key=True)
    title_name = Column(String(255))
    address = Column(String(255))
    phone = Column(String(255))
    site_url = Column(String(255))

    def __init__(self, title_name):
        self.title_name = title_name

    def __repr__(self):
        return "Place('%s')" % (self.title_name)

class Image(Base):
    __tablename__ = 'images'

    image_id = Column(Integer, Sequence('image_id_seq'), primary_key=True) 
    image_path = Column(String(255))
    image_width = Column(Integer)
    image_height = Column(Integer)
    thumb_path = Column(String(255))
    thumb_width = Column(Integer)
    thumb_height = Column(Integer)
    image_type_id = Column(Integer, ForeignKey('image_types.image_type_id')) 
    content_type = Column(Integer)

    image_type = relationship('ImageType')

    def __init__(self, image_type):
        self.image_type = image_type

    def __repr__(self):
        return "Image('%s')" % (self.image_path)

    def uploadFromFile(self, source_file):
        image_type = self.image_type
        fp = FileProcess()
        thumb_info = fp.copyImage(source_file, transform = image_type.thumb_transform_image,\
                short_dir = image_type.base_dir)
        if not thumb_info or not thumb_info.is_image():
            return False
        image_info = fp.copyImage(source_file, short_dir = image_type.base_dir)
        if not image_info or not image_info.is_image():
            return False
        self.thumb_path = thumb_info.short_path
        self.thumb_width = thumb_info.width
        self.thumb_height = thumb_info.height
        self.image_path = image_info.short_path
        self.image_width = image_info.width
        self.image_height = image_info.height
        self.content_type = image_info.content_type
        return True

file_column(Image.image_path)
file_column(Image.thumb_path)

class ImageType(Base):
    TARGET_NONE = 0
    TARGET_EVENT = 1

    __tablename__ = 'image_types'

    image_type_id = Column(Integer, Sequence('image_type_id_seq'), primary_key=True)
    target_type = Column(Integer)
    title_name = Column(String(255))
    max_thumb_width = Column(Integer)
    max_thumb_height = Column(Integer)
    def_thumb_path = Column(String(255))
    base_dir = Column(String(255))
    transform_type = Column(Integer)

    def __init__(self, target_type, title_name = ''):
        self.target_type = target_type
        self.title_name = title_name

    def __repr__(self):
        return "ImageType('%s')" % (self.title_name)

    def mkDefThumb(self):
        info = mkImageWithFrame(self.max_thumb_width, self.max_thumb_height)
        if not info.is_image():
            return False
        fp = FileProcess()
        image_info = fp.copyImage(info.file_path, short_dir = self.base_dir)
        if not image_info or not image_info.is_image():
            return False
        self.def_thumb_path = image_info.short_path
        return True

    @property
    def thumb_transform_image(self):
        return ImageTransform.create(self.transform_type,\
                width = self.max_thumb_width,\
                height = self.max_thumb_height)

file_column(ImageType.def_thumb_path)

class Person(Base):
    MUSICIAN = 1

    __tablename__ = 'persons'

    person_id = Column(Integer, Sequence('person_id_seq'), primary_key=True)
    name = Column(String(255))
    source_url = Column(String(255))
    thumb_image_id = Column(Integer, ForeignKey('images.image_id'))
    person_type = Column(Integer)

    thumb_image = relationship('Image')

    def __init__(self, name, person_type):
        self.name = name

    def __repr__(self):
        return "Person('%s', '%s')" % (self.name, self.person_type)

class EventType(Base):
    __tablename__ = 'event_types'

    event_type_id = Column(Integer, Sequence('event_type_id_seq'), primary_key=True) 
    name = Column(String(255))
    title = Column(String(255))

    def __init__(self, name, title):
        self.name = name
        self.title = title

    def __repr__(self):
        return "EventType('%s')" % (self.name)


class Link(Base):
    TYPE_STD = 0
    TYPE_MAIN = 1

    __tablename__ = 'links'

    link_id = Column(Integer, Sequence('link_id_seq'), primary_key=True)
    title = Column(String(255))
    url = Column(String(255))
    domain_id = Column(String(255), ForeignKey('link_domains.domain_id'))
    link_type = Column(Integer)

    link_domain = relationship('LinkDomain')

    def __init__(self, url):
        self.url = url

    def __repr__(self):
        return "Link('%s')" % (self.url)

class LinkDomain(Base):
    __tablename__ = 'link_domains'

    domain_id = Column(Integer, Sequence('domain_id_seq'), primary_key=True)
    domain = Column(String(255))
    def_link_title = Column(String(255))
    domain_image_id = Column(String(255), ForeignKey('images.image_id')) 

    domain_image = relationship('Image')

    def __init__(self, domain):
        self.domain = domain

    def __repr__(self):
        return "LinkDomain('%s')" % (self.domain)
