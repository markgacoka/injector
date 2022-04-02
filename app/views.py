from django.shortcuts import render

def test(request):
    context = {}
    return render(request, 'index.html', context)