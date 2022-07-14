from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# Create your views here.
def dashboard(request):
    template = loader.get_template('dashboard/index.html')
    context = {}
    return HttpResponse(template.render(context, request))