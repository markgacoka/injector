import re
import png
import subprocess
from PIL import Image, ImageDraw, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

class Headers:
    def __init__(self):
        pass

    def gif_header_data(self):
        # GIF Header (13 bytes)
        header  = b'\x47\x49\x46\x38\x39\x61'  # Signature and version  (GIF89a)
        header += b'\x0a\x00'                  # Logical Screen Width   (10 pixels)
        header += b'\x0a\x00'                  # Logical Screen Height  (10 pixels)
        header += b'\x00'                      # GCTF
        header += b'\xff'                      # Background Color       (#255)
        header += b'\x00'                      # Pixel Aspect Ratio

        # Global Color Table + Blocks (13 bytes)
        header += b'\x2c'                      # Image Descriptor
        header += b'\x00\x00\x00\x00'          # NW corner position of image in logical screen
        header += b'\x0a\x00\x0a\x00'          # Image width and height in pixels
        header += b'\x00'                      # No local color table
        header += b'\x02'                      # Start of image
        header += b'\x00'                      # End of image data
        header += b'\x3b'                      # GIF file terminator

        return header

    def bmp_header_data(self):
        # BMP Header (14 bytes)
        header  = b'\x42\x4d'          # Magic bytes header       (`BM`)
        header += b'\x1e\x00\x00\x00'  # BMP file size            (30 bytes)
        header += b'\x00\x00'          # Reserved                 (Unused)
        header += b'\x00\x00'          # Reserved                 (Unused)
        header += b'\x1a\x00\x00\x00'  # BMP image data offset    (26 bytes)

        # DIB Header (12 bytes)
        header += b'\x0c\x00\x00\x00'  # DIB header size          (12 bytes)
        header += b'\x01\x00'          # Width of bitmap          (1 pixel)
        header += b'\x01\x00'          # Height of bitmap         (1 pixel)
        header += b'\x01\x00'          # Number of color planes   (1 plane)
        header += b'\x18\x00'          # Number of bits per pixel (24 bits)

        # BMP Image Pixel Array (4 bytes)
        header += b'\x00\x00\xff'      # Red, Pixel (0,1)
        header += b'\x00'              # Padding for 4 byte alignment

        return header

    def png_header_data(self):
        # PNG header 
        header = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'    # PNG signature
        header += b'\x00\x00\x00\x0d'                   # Image header
        header += b'\x49\x48\x44\x52'
        header += b'\x00\x00\x00\x01\x00\x00\x00\x01'
        header += b'\x08\x02\x00\x00\x00\x90'
        header += b'\x77\x53\xde'   
        header += b'\x00\x00\x00\x0c'                    # Image data
        header += b'\x49\x44\x41\x54\x08\xd7\x63\xf8\xcf\xc0'
        header += b'\x00\x00\x03\x01\x01\x00'
        header += b'\x18\xdd\x8d\xb0'

        return header

    def png_end(self):
        header = b'\x00\x00\x00\x00'                    # Image end
        header += b'\x49\x45\x4e\x44\xae\x42\x60\x82'
        return header

    def jpeg_header_data(self):
        # JPEG Header
        header = b'\xff\xd8' # Start of Image
        header += b'\xff\xe0\x00\x10' # Application Default Header
        header += b'\x4a\x46\x49\x46' # JFIF
        header += b'\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00' # Rest of Application Default Header
        header += b'\xff\xdb\x00\x43\x00' # Quantization Table
        header += b'\xff\xdb\x00\x43\x01' # Quantization Table
        header += b'\xff\xc0\x00\x11\x08' # Start of Frame
        header += b'\x00\x02\x00\x06\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01' # Frame continuation
        header += b'\xff\xc4\x00\x15\x00\x01\x01\x00\x00\x00\x00' # Define Huffman Table
        header += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x09' 
        header += b'\xff\xc4\x00\x19\x10\x01\x00\x02\x03\x00\x00\x00\x00\x00' # Define Huffman Table
        header += b'\x00\x00\x00\x00\x00\x00\x00\x00\x06\x08\x38\x88\xb6'
        header += b'\xff\xc4\x00\x15\x01\x01\x01\x00\x00\x00\x00' # Define Huffman Table
        header += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\x0a'
        header += b'\xff\xc4\x00\x1c\x11\x00\x01\x03\x05\x00\x00\x00\x00\x00\x00' # Define Huffman Table
        header += b'\x00\x00\x00\x00\x00\x00\x08\x00\x07\xb8\x09\x38\x39\x76\x78'
        header += b'\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00' # Start of Scan
        return header

    def jpeg_end(self):
        header = b'\x86\xf7\xe7\x1d\xa9\x16\xca\x77\x30\xd0\x14\xf7\x41\xdc\xfa\x8e' # Image data
        header += b'\xfb\x31\x19\x26\xfd\xc4\x2a\xf4\x5c\x81\x7b\xdb\x06\x84\xa0\x75\x17'
        header += b'\xff\xd9' # End of Image
        return header

class Injector:
    def __init__(self, img_type, width, height, payload, filename):
        self.img_type = img_type
        self.width = width
        self.height = height
        self.payload = payload
        self.filename = filename

    def create_txt(self, filename):
        f = open(filename, "w")
        f.close()
        return filename

    def create_gif(self, width, height, filename):
        images = []
        center = width // 2
        color = (0, 0, 0)
        max_radius = int(center * 1.5)
        step = 8

        for i in range(0, max_radius, step):
            im = Image.new('RGB', (width, height), color)
            draw = ImageDraw.Draw(im)
            draw.ellipse((center - i, center - i, center + i, center + i), fill=color)
            images.append(im)

        images[0].save(filename, save_all=True)
        return filename

    def create_png(self, width, height, filename):
        img = []
        for y in range(height):
            row = ()
            for x in range(width):
                row = row + (x, max(0, 255 - x - y), y)
            img.append(row)
        with open(filename, 'wb') as f:
            w = png.Writer(width, height, greyscale=False)
            w.write(f, img)
        return filename

    def create_bmp(self, width, height, filename):
        img = Image.new( 'RGB', (width, height), "black")
        pixels = img.load()
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                pixels[i,j] = (i, j, 100)

        img.save(filename)
        return filename

    def create_jpg(self, width, height, filename):
        img = Image.new( 'RGB', (width, height), "black")
        pixels = img.load()
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                pixels[i,j] = (i, j, 100)

        img.save(filename)
        return filename

    def inject(self, payload, contents, out_file, contents_end=b''):
        f = open(out_file, "w+b")
        f.write(contents)
        f.write(b'\x2f\x2f\x2f\x2f\x2f')
        f.write(payload)
        f.write(b'\x3b')
        f.write(contents_end)
        f.close()

    def main(self):
        if self.img_type == 'PNG':
            if self.width != 0 and self.height != 0:
                final_filename = self.create_png(self.width, self.height, self.filename)
                f = open(final_filename, "r+b")
                f.seek(50)
                f.write(b'\x2f\x2f\x2f\x2f\x2f')
                f.write(self.payload)
                f.write(b'\x3b')
                return final_filename, (self.width, self.height)
            else:
                final_filename = self.create_txt(self.filename)
                png_header = Headers().png_header_data()
                png_end = Headers().png_end()
                self.inject(payload=self.payload, contents=png_header, out_file=final_filename, contents_end=png_end)
                im = Image.open(final_filename)
                width, height = im.size
                im.close()
                return final_filename, (width, height)
        elif self.img_type == 'GIF':
            if self.width != 0 and self.height != 0:
                final_filename = self.create_gif(self.width, self.height, self.filename)
                f = open(final_filename, "ab")
                f.write(b'\x2f\x2f\x2f\x2f\x2f')
                f.write(self.payload)
                f.write(b'\x3b')
                f.close()
                return final_filename, (self.width, self.height)
            else:            
                final_filename = self.create_txt(self.filename)
                gif_header = Headers().gif_header_data()
                self.inject(payload=self.payload, contents=gif_header, out_file=final_filename)
                im = Image.open(final_filename)
                width, height = im.size
                im.close()
                return final_filename, (width, height)
        elif self.img_type == 'BMP':
            if self.width != 0 and self.height != 0:
                final_filename = self.create_bmp(self.width, self.height, self.filename)
                f = open(final_filename, "ab")
                f.write(b'\x2f\x2f\x2f\x2f\x2f')
                f.write(self.payload)
                f.write(b'\x3b')
                f.close()
                return final_filename, (self.width, self.height)
            else:            
                final_filename = self.create_txt(self.filename)
                bmp_header = Headers().bmp_header_data()
                self.inject(payload=self.payload, contents=bmp_header, out_file=final_filename)
                im = Image.open(final_filename)
                width, height = im.size
                im.close()
                return final_filename, (width, height)
        elif self.img_type == 'JPEG':
            if self.width != 0 and self.height != 0:
                final_filename = self.create_jpg(self.width, self.height, self.filename)
                f = open(final_filename, "ab")
                f.write(b'\x2f\x2f\x2f\x2f\x2f')
                f.write(self.payload)
                f.write(b'\x3b')
                f.write(b'\xff\xd9')
                f.close()
                return final_filename, (self.width, self.height)
            else:            
                final_filename = self.create_txt(self.filename)
                jpg_header = Headers().jpeg_header_data()
                jpg_end = Headers().jpeg_end()
                self.inject(payload=self.payload, contents=jpg_header, out_file=final_filename, contents_end=jpg_end)
                image_size = list(map(int, re.findall('(\d+)x(\d+)', subprocess.getoutput("file " + final_filename))[-1]))
                return final_filename, (image_size[0], image_size[1])
        else:
            return None, None