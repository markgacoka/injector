from django.shortcuts import render

def index(request):
    context = {}
    context['hex_dump'] = ''
    context['ipaddress'] = 'None'
    context['download'] = []
    context['dimensions'] = '(0, 0)'
    context['file_type'] = 'None'
    context['file_size'] = '0 bytes'
    context['filename'] = 'None'
    context['extension'] = 'None'
    context['mime_type'] = 'None'
    context['byte_match'] = 'None'
    context['status'] = 'Not injected'
    return render(request, 'index.html', context)