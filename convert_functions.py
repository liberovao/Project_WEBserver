import os
import uuid
from pathlib import Path

import ffmpeg
from PIL import Image

PICTURE_SUPPORTED_FORMATS = ['WEBP', 'BMP', 'PPM',
                             'JPEG', 'TIFF', 'GIF', 'PNG', 'SGI', 'JPG']


class PictureConverter(object):

    def __init__(self, path, filename):
        self.convertations = {'BMP': self.to_bmp, 'GIF': self.to_gif, 'JPEG': self.to_jpeg, 'PNG': self.to_png,
                              'MSP': self.to_msp, 'PCX': self.to_pcx, 'PPM': self.to_ppm, 'SGI': self.to_sgi,
                              'TIFF': self.to_tiff, 'WEBP': self.to_webp, 'XBM': self.to_xbm,
                              'JPG': self.to_jpeg}
        self.path = path
        self.file_suffix = Path(filename).suffix
        self.filename = filename[:filename.rfind(Path(filename).suffix)]
        self.original_file = os.path.join(path, filename)

    def get_image_object(self):
        im = Image.open(self.original_file)
        rgb_im = im.convert('RGB')
        return rgb_im