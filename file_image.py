from os import path,mkdir
from shutil import copyfile
from random import randint
import Image

class FileImageException(Exception):
    pass

class FileProcess:
    base_dir = path.realpath(path.curdir)
    base_url = ''
    img_subdir = None

    @staticmethod
    def fullPath(file_path):
        return path.join(FileProcess.base_dir, str(file_path))

    @staticmethod
    def fullUrl(file_path):
        return FileProcess.base_url + '/' + file_path

    @staticmethod
    def imageInfo(image_path):
        ii = ImageInfo(FileProcess.fullPath(image_path))
        if not ii.is_image():
            return ii
        ii.short_path = image_path
        return ii

    def __init__(self):
        self.dir_max = 99
        self.file_max = 999999999

    def copyFile(self, source_file, copy_func = None, short_dir = None, ext = None):
        if not path.isfile(source_file):
            raise FileImageException('Cant find source file')
        if ext is None:
            (_, ext) = path.splitext(source_file)
        while True:
            p = []
            if short_dir:
                p.extend(short_dir.split(path.sep))
            p.append(str(randint(1, self.dir_max)))
            for pp in [p[0:v] for v in range(1,len(p)+1)]:
                rand_dir = self.fullPath(path.join(*pp))
                if not path.isdir(rand_dir):
                    mkdir(rand_dir)
            p.append(str(randint(1, self.file_max)) + str(ext))
            target_file = path.join(*p) 
            full_target_path = self.fullPath(target_file)
            if not path.isfile(full_target_path):
                break;
        if copy_func is None:
            copy_func = copyfile
        copy_func(source_file, full_target_path)
        return target_file

    def copyImage(self, source_file, transform = None, short_dir = None): 
        source_info = ImageInfo(source_file)
        if not source_info.is_image():
            return None
        if transform is None:
            copy_func = None
        else:
            copy_func = lambda source, target: transform.process(source, target)
        p = [v for v in [self.img_subdir, short_dir] if v]
        if p:
            short_dir = path.join(*p)
        #print source_info.content_type
        target_file = self.copyFile(source_file, copy_func = copy_func, short_dir = short_dir,\
                ext = source_info.file_ext)
        return FileProcess.imageInfo(target_file)

class ImageTransform:
    STD = 1
    
    @staticmethod
    def create(transform_type, width = None, height = None):
        types = { 
            ImageTransform.STD: ImageTransformStd 
        }
        if transform_type in types:
            it = types[transform_type]
            it.width = width
            it.height = height
            return it()
        else:
            raise FileImageException('Cant find this type')

    def process(self, source_file, target_file):
        raise FileImageException('Cant process empty for this transfer type')

class ImageTransformStd(ImageTransform):
    def process(self, source_file, target_file):
        try:
            i = Image.open(source_file)
            (i_width, i_height) = i.size
            i_ratio = float(i_width) / float(i_height)
            #print i_ratio, i_width, i_height
            ratio = float(self.width) / float(self.height)
            if i_ratio < ratio:
                h = self.height
                w = int(self.height * i_ratio)
            else:
                w = self.width
                h = int(float(self.width) / float(i_ratio))
            i.resize((w, h)).save(target_file)
        except IOError:
            return False
        return True

class ImageInfo:
    JPEG = 1
    GIF = 2 
    PNG = 3

    file_exts = {
        JPEG: '.jpg',
        GIF: '.gif',
        PNG: '.png'
    }

    pil_formats = {
        'JPEG': JPEG,
        'GIF': GIF,
        'PNG': PNG
    }

    def __init__(self, file_path):
        self.file_path = file_path
        self.width = 0
        self.height = 0
        self.content_type = None
        self.initInfo()
        if not path.isfile(self.file_path):
            return

    def initInfo(self):
        try:
            im = Image.open(self.file_path)
            self.content_type = self.pil_formats[im.format]
        except IOError:
            return
        except NameError:
            return
        (self.width, self.height) = im.size

    @property
    def file_ext(self):
        try:
            return self.file_exts[self.content_type]
        except NameError:
            raise FileImageException('Cant find file extension for this content type')
        except KeyError as e:
            raise e

    def __bool__(self):
        return self.is_image()

    def is_image(self):
        return (not self.content_type is None)
