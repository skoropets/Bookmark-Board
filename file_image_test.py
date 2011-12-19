import unittest

from file_image import FileProcess, ImageInfo, ImageTransform
from model import Image, ImageType
from conn import engine, session
from tempfile import mkdtemp, mkstemp 
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
    def testFirst(self):
        pass

if __name__ == '__main__':
    unittest.main()