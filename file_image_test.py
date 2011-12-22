import unittest

from file_image import FileProcess, ImageInfo, ImageTransform
from model import Image, ImageType, EventSourceType, EventType, Event, Place, Person
from conn import engine, session
from tempfile import mkdtemp, mkstemp 
from datetime import datetime, date
from sqlalchemy.orm import aliased
import os
import shutil

def mkTempFile(content):
    (fd, source_file) = mkstemp()
    fh = os.fdopen(fd, 'w')
    fh.write(content)
    fh.close()
    return source_file

def getFileContent(file_name):
    fh = open(file_name, 'r')
    s = fh.read()
    fh.close()
    return s

def fileInTestDir(file_path):
    try:
        curr_dir = os.path.dirname(__file__)
    except NameError:
        curr_dir = os.path.realpath(os.curdir)
    return os.path.join(curr_dir, file_path)

class TestFileImage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = mkdtemp() 
        FileProcess.base_dir = self.temp_dir 
        FileProcess.img_subdir = 'img'

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def testFileCopy(self):
        write_str = 'Temp file'
        source_file = mkTempFile(write_str)
        fp = FileProcess()
        target_file = fp.copyFile(source_file, ext='.txt')
        full_target_path = fp.fullPath(target_file)
        s = getFileContent(full_target_path)
        self.assertEquals(s, write_str)
        (_, ext) = os.path.splitext(target_file)
        self.assertEquals(ext, '.txt')
        os.unlink(source_file)

    def testImageInfo(self):
        i = ImageInfo(fileInTestDir('img/test.jpg'))
        self.assertEquals(i.is_image(), True)
        self.assertEquals(i.content_type, ImageInfo.JPEG)
        self.assertEquals(i.width, 418)
        self.assertEquals(i.height, 604) 
        bad_file = mkTempFile('Not image')
        bi = ImageInfo(bad_file)
        self.assertEquals(bi.is_image(), False)
        os.unlink(bad_file)

    def testImageCopy(self):
        it = ImageTransform.create(ImageTransform.STD, 100, 100);
        fp = FileProcess()
        info = fp.copyImage(fileInTestDir('img/test.jpg'), transform = it, short_dir = 'i') 
        self.assertEquals(info.is_image(), True)
        self.assertEquals(info.content_type, ImageInfo.JPEG)
        self.assert_(info.width <= 100)
        self.assert_(info.height <= 100) 
        split_p = info.short_path.split(os.path.sep)
        self.assert_('i' in split_p)
        self.assert_('img' in split_p)
        info = fp.copyImage(fileInTestDir('img/test.jpg')) 
        self.assertEquals(info.is_image(), True)
        self.assertEquals(info.content_type, ImageInfo.JPEG)
        self.assertEquals(info.width, 418)
        self.assertEquals(info.height, 604) 

    def testAddImageToDb(self):
        it = ImageType(ImageType.TARGET_NONE)
        it.max_thumb_height = 50
        it.max_thumb_width = 150
        it.base_dir = 'b'
        it.transform_type = ImageTransform.STD
        session.add(it)
        img = Image(it)
        ret = img.uploadFromFile(fileInTestDir('img/test.jpg'))
        self.assert_(ret)
        session.add(img)
        session.commit()
        self.assert_(os.path.isfile(FileProcess.fullPath(img.thumb_path)))
        self.assert_(os.path.isfile(FileProcess.fullPath(img.image_path)))
        split_p = img.thumb_path.split(os.path.sep)
        print split_p
        self.assert_('b' in split_p)
        self.assert_('img' in split_p)
        split_p = img.image_path.split(os.path.sep)
        self.assert_('b' in split_p)
        self.assert_('img' in split_p)
        self.assert_(img.thumb_width <= 150)
        self.assert_(img.thumb_height <= 50) 
        self.assertEquals(img.content_type, ImageInfo.JPEG)
        self.assertEquals(img.image_width, 418)
        self.assertEquals(img.image_height, 604) 

        session.delete(img)
        session.delete(it)
        session.commit()

class TestEvent(unittest.TestCase):
    def setUp(self):
        session.query(EventType).filter(EventType.name == 'first')
        session.commit()
        self.et = EventType('first', 'First')
        session.add(self.et)
        session.commit()
        
    def tearDown(self):
        session.delete(self.et)
        session.commit()

    @property
    def first_query(self):
        et_alias = aliased(EventType)
        return session.query(Event).\
                join(et_alias, Event.event_type).\
                filter(et_alias.name == 'first').\
                    group_by(Event.event_id)

    def testFirst(self):
        first_query = self.first_query
        session.query(Event).delete()
        session.commit()
        session.flush()

        e = Event(self.et)
        e.title = 'First event'
        e.time_start = datetime(1970, 1, 1, 0, 0)
        e.time_end = datetime(1970, 1, 1, 3, 0)
        e.description = 'First description'
        e.source_type = EventSourceType.EMPTY 
        session.add(e)
        session.commit()

        all_first = first_query.all()
        self.assertEquals(len(all_first), 1)
        e = all_first[0]
        self.assertEquals(e.title, 'First event');
        self.assertEquals(e.time_start, datetime(1970, 1, 1, 0, 0))
        self.assertEquals(e.time_end, datetime(1970, 1, 1, 3, 0))
        self.assertEquals(e.description, 'First description')
        self.assertEquals(e.source_type, EventSourceType.EMPTY)
        self.assertEquals(e.event_type.name, 'first')

        all_date_empty = session.query(Event).filter(Event.time_start == date(1971, 1, 1)).all() 
        self.assertEquals(len(all_date_empty), 0)
        all_date_fine = session.query(Event).filter(Event.time_start == date(1970, 1, 1)).all() 
        self.assertEquals(len(all_date_fine), 1)
        session.delete(e)
        session.commit()

    def testSecond(self):
        session.query(Event).delete()
        session.query(Person).delete()
        session.query(Place).delete()
        session.commit()

        place = Place('First place')
        place.address = 'Address'
        place.phone = 'Phone'
        place.site_url = 'http://localhost';
        persons_list = [] 
        persons_list.append(Person('First', Person.MUSICIAN))
        persons_list.append(Person('Second', Person.MUSICIAN))
        e = Event(self.et)
        e.place = place
        for p in persons_list:
            e.persons.append(p)
        session.add(e)
        session.commit()
        session.flush()

        first_query = self.first_query
        all_first = first_query.all()
        self.assertEquals(len(all_first), 1)
        e = all_first[0]
        place = e.place
        self.assertEquals(place.address, 'Address')
        self.assertEquals(place.phone, 'Phone')
        self.assertEquals(place.site_url, 'http://localhost')
        person_names = []
        for p in e.persons:
            person_names.append(p.name)
        self.assert_('First' in person_names)
        self.assert_('Second' in person_names)
        

if __name__ == '__main__':
    unittest.main()
