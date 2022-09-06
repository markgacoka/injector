import boto3
import urllib.request

import glob
from botocore.errorfactory import ClientError

import os, re
import puremagic

from django.shortcuts import render
from PIL import Image
from django.template.context_processors import csrf
from scripts.IPAddress.get_ip import get_client_ip
from scripts.HexViewer.hexviewer import hex_viewer
from scripts.CodeInjection.injector import Injector
from scripts.HexViewer.full_hexviewer import full_hex_viewer

def index(request):
    context = {}
    ip_address = get_client_ip(request)

    if request.method == "POST":
        payload = request.POST.get('payload').encode() if request.POST.get('payload') != None else None
        width = int(request.POST.get('width')) if request.POST.get('width') != '' and request.POST.get('width') != None else 0
        height = int(request.POST.get('height')) if request.POST.get('height') != '' and request.POST.get('width') != None else 0
        file_type = request.POST.get('file_type') if request.POST.get('file_type') != None else None
        
        if 'full_hex' in request.POST.keys():
            try:
                list_of_files = glob.glob('media/payloads/*')
                if len(list_of_files) < 1:
                    try:
                        urllib.request.urlretrieve("https://cysuite-bucket.s3.us-west-2.amazonaws.com/media/default.png", "media/payloads/default.png")
                    except:
                        context['hex_dump'] = ''
                        context['ipaddress'] = ip_address
                        context['dimensions'] = '(0, 0)'
                        context['file_type'] = 'None'
                        context['file_size'] = '0 bytes'
                        context['filename'] = 'None'
                        context['extension'] = 'None'
                        context['mime_type'] = 'None'
                        context['byte_match'] = 'None'
                        context['status'] = 'Not injected: Error downloading the image from S3 bucket'
                        return render(request, 'index.html', context)
                    else:
                        relative_filename = 'default.png'
                        latest_file = 'media/payloads/default.png'
                        new_filename = 'media/payloads/default.png'
                        context['status'] = 'Loaded default image'
                else:
                    latest_file = max(list_of_files, key=os.path.getctime)
                    relative_filename = latest_file.rsplit('/', 1)[-1]
                    new_filename = 'media/payloads/' + relative_filename
                    context['status'] = 'Viewing full hex code'

                img = Image.open(latest_file)
                width, height = img.size
                hex_dump = next(full_hex_viewer(latest_file))
            
                context['hex_dump'] = hex_dump
                context['ipaddress'] = ip_address
                context['dimensions'] = (width, height)
                context['file_type'] = puremagic.magic_file(new_filename)[0].name 
                context['file_size'] = str(os.path.getsize(new_filename)) + ' bytes'
                context['filename'] = relative_filename
                context['extension'] = puremagic.magic_file(new_filename)[0].extension
                context['mime_type'] = puremagic.magic_file(new_filename)[0].mime_type
                context['byte_match'] = puremagic.magic_file(new_filename)[0].byte_match.decode('UTF-8','ignore').strip()
                context.update(csrf(request))
                if new_filename != 'media/payloads/default.png':
                    os.remove('media/payloads/' + relative_filename)
                return render(request, 'index.html', context)
            except ClientError:
                dimensions, filename = None, None

        elif (request.POST.get('filename') == None or request.POST.get('filename') == '' or '.' not in request.POST.get('filename')) and 'clear' not in request.POST.keys():
            context['status'] = 'Not injected: Filename does not follow the correct filename pattern'
            filename, dimensions = None, (None, None)
        elif (request.POST.get('filename') == None or request.POST.get('filename') == '' or '.' not in request.POST.get('filename')) and 'clear' in request.POST.keys():
            context['status'] = 'Cleared'
            filename, dimensions = None, (None, None)
        elif type(width) != int or type(height) != int or width < 0 or height < 0:
            context['status'] = 'Not injected: Dimension value should be an integer!'
            filename, dimensions = None, (None, None)
        elif file_type == 'PNG' and (width > 256 or height > 256):
            context['status'] = 'Not injected: PNG files have a 256 maximum byte size!'
            filename, dimensions = None, (None, None)
        else:
            filename = 'media/payloads/' + request.POST.get('filename')
            injection = Injector(file_type, width, height, payload, filename)
            filename, dimensions = injection.main()

        if filename != None and dimensions != None:
            list_files = glob.glob('media/payloads/*')
            for file_ in list_files:
                if filename != 'media/payloads/default.png' and file_ != filename:
                    try:
                        os.remove(file_)
                    except:
                        print("Tried to remove a non-existent payload image")

            relative_filename = filename.rsplit('/', 1)[-1]
            hex_dump = hex_viewer(filename)
            context['hex_dump'] = hex_dump
            context['ipaddress'] = ip_address
            context['dimensions'] = dimensions
            context['file_type'] = puremagic.magic_file(filename)[0].name 
            context['file_size'] = str(os.path.getsize(filename)) + ' bytes'
            context['filename'] = relative_filename
            context['extension'] = puremagic.magic_file(filename)[0].extension
            context['mime_type'] = puremagic.magic_file(filename)[0].mime_type
            context['byte_match'] = puremagic.magic_file(filename)[0].byte_match.decode('UTF-8','ignore').strip()
            context['download'] = relative_filename
            context['status'] = 'Injected successfully'
            context['success_message'] = 'Your payload has been injected successfully!'
            return render(request, 'index.html', context)
        elif 'clear' in request.POST.keys():
            context['status'] = 'Cleared'
        else:
            context['status'] = 'Not injected'
        context['ipaddress'] = ip_address
        context['hex_dump'] = ''
        context['dimensions'] = '(0, 0)'
        context['file_type'] = 'None'
        context['file_size'] = '0 bytes'
        context['filename'] = 'None'
        context['extension'] = 'None'
        context['mime_type'] = 'None'
        context['byte_match'] = 'None'
        return render(request, 'index.html', context)
    else:
        context['hex_dump'] = ''
        context['ipaddress'] = ip_address
        context['dimensions'] = '(0, 0)'
        context['file_type'] = 'None'
        context['file_size'] = '0 bytes'
        context['filename'] = 'None'
        context['extension'] = 'None'
        context['mime_type'] = 'None'
        context['byte_match'] = 'None'
        context['status'] = 'Not injected'
    return render(request, 'index.html', context)