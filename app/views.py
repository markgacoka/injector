import boto3
import requests
from io import BytesIO
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
            current_url = ''
            filename = request.session['current_url'] = current_url
            relative_filename = filename.rsplit('/', 1)[-1]

            s3 = boto3.client("s3")
            try:
                # s3.head_object(Bucket='cysuite-bucket', Key='media/' + relative_filename)
                s3.download_file('cysuite-bucket', 'media/' + relative_filename, 'media/payloads/' + relative_filename)
                new_filename = 'media/payloads/' + relative_filename
                response = requests.get(filename)
                img = Image.open(BytesIO(response.content))
                width, height = img.size
                hex_dump = next(full_hex_viewer(filename))
            
                context['hex_dump'] = hex_dump
                context['ipaddress'] = ip_address
                context['dimensions'] = (width, height)
                context['file_type'] = puremagic.magic_file(new_filename)[0].name 
                context['file_size'] = str(os.path.getsize(new_filename)) + ' bytes'
                context['filename'] = relative_filename
                context['extension'] = puremagic.magic_file(new_filename)[0].extension
                context['mime_type'] = puremagic.magic_file(new_filename)[0].mime_type
                context['byte_match'] = puremagic.magic_file(new_filename)[0].byte_match.decode('UTF-8','ignore').strip()
                context['download'] = request.session['current_url']
                context['status'] = 'Viewing full hex code'
                context.update(csrf(request))
                os.remove('media/payloads/' + relative_filename)
                return render(request, 'dashboard/injector.html', context)
            except ClientError:
                dimensions, filename = None, None

        elif (request.POST.get('filename') == None or request.POST.get('filename') == '' or '.' not in request.POST.get('filename')) and 'clear' not in request.POST.keys():
            context['status'] = 'Not injected'
            context['error_message'] = 'Filename does not follow the correct filename pattern'
            filename, dimensions = None, (None, None)
        elif (request.POST.get('filename') == None or request.POST.get('filename') == '' or '.' not in request.POST.get('filename')) and 'clear' in request.POST.keys():
            context['status'] = 'Cleared'
            filename, dimensions = None, (None, None)
        elif type(width) != int or type(height) != int or width < 0 or height < 0:
            context['status'] = 'Not injected'
            context['error_message'] = 'Dimension value should be an integer!'
            filename, dimensions = None, (None, None)
        else:
            filename = 'media/payloads/' + request.POST.get('filename')
            injection = Injector(file_type, width, height, payload, filename)
            filename, dimensions = injection.main()

        if filename != None and dimensions != None:
            new_filename = re.sub(r'^.*?/', '', filename)
            current_url = filename

            if new_filename != current_url and current_url != 'https://cysuite-bucket.s3.us-west-2.amazonaws.com/media/default.png':
                try:
                    del request.session['current_url']
                except:
                    print("Tried to remove a non-existent payload image")
            request.session['current_url'] = current_url

            final_filename = re.sub(r'^.*?/', '', new_filename)
            hex_dump = hex_viewer(filename)
            context['hex_dump'] = hex_dump
            context['ipaddress'] = ip_address
            context['dimensions'] = dimensions
            context['file_type'] = puremagic.magic_file(filename)[0].name 
            context['file_size'] = str(os.path.getsize(filename)) + ' bytes'
            context['filename'] = final_filename
            context['extension'] = puremagic.magic_file(filename)[0].extension
            context['mime_type'] = puremagic.magic_file(filename)[0].mime_type
            context['byte_match'] = puremagic.magic_file(filename)[0].byte_match.decode('UTF-8','ignore').strip()
            context['download'] = request.session['current_url']
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