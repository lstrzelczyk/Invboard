# -*- encoding: utf-8 -*-


from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from .models import *

import ast
import urllib.parse
import pycurl
import certifi
from io import BytesIO
import json
from .tasks import synchro_stan



@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}
    html_template = loader.get_template('home/dashboard.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def home(request): #tutaj sa wszystkie z home
    print("home")
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        print(request)
        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def stany(request):
    print("stany")
    context = {}
    try:

        load_template = request.path.split('/')[-1]
        context['segment'] = load_template
        #print(UstawieniaStan.objects.filter(nazwa="Ustawienia"))
        context['dane_synchronizacja'] = UstawieniaStan.objects.filter(nazwa="Ustawienia")

        if("stany_kategorie.html" == load_template):
            context['kategorie'] = pobierz_kategorie()
            kategories = Kategorie.objects.get(kategoria_nazwa="wszystkie")
            kategoria_baza_tab = str(kategories.kategoria_id).split(",")
            context['kategorie_zapisane'] = kategoria_baza_tab
        if("stany_dane_baselinker.html" == load_template):
            dane_dostepowe = UstawieniaBaselinker.objects.all()
            context['dane_dostepowe'] = dane_dostepowe
        #print(load_template)

        #print(context)

        html_template = loader.get_template('stany/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))

def ajax_stany(request):
    synchro_stan.delay()
    return HttpResponse('')

def zapisz_kategorie(request):
    if request.is_ajax and request.method == "POST":
        tab_kategorie = request.POST.getlist('kategorie_ids[]')
        kategorie_do_zapisania = ",".join(tab_kategorie)
        t = Kategorie.objects.get(kategoria_nazwa="wszystkie")
        t.kategoria_id = kategorie_do_zapisania
        t.save()
    return HttpResponse('')

def zapisz_dane_baselinker(request):
    if request.is_ajax and request.method == "POST":
        #print(request.POST)
        #print(request.POST.dict())
        tab_dane = request.POST.dict()
        dict_dane = ast.literal_eval(tab_dane['dane_dostepowe'])
        #print(tab_dane['dane_dostepowe'])
        #print(type(dict_dane))
        for key, dane in dict_dane.items():
            print(dane[0])
            t = UstawieniaBaselinker.objects.get(nazwa=key)
            t.token = dane[0]['token']
            t.inventory_id = dane[1]['inventory_id']
            t.save()

        #kategorie_do_zapisania = ",".join(tab_kategorie)
        #t = Kategorie.objects.get(kategoria_nazwa="wszystkie")
        #t.kategoria_id = kategorie_do_zapisania
        #t.save()
    return HttpResponse('')

def pobierz_kategorie():
    try:
        b_obj = BytesIO()
        url = 'https://api.baselinker.com/connector.php'

        methodParams = {"inventory_id": "1480"}

        params = {
            # 46-2561-F00633A9B89B76FFB045886D3D5231F64431B734397F3BE66CC7A96AC7E128B2,
            'token': '46-2561-F00633A9B89B76FFB045886D3D5231F64431B734397F3BE66CC7A96AC7E128B2',
            "method": "getInventoryCategories",
            "parameters": json.dumps(methodParams)
        }

        crl = pycurl.Curl()
        crl.setopt(crl.URL, url)
        crl.setopt(crl.POSTFIELDS, urllib.parse.urlencode(params))
        crl.setopt(crl.CAINFO, certifi.where())
        crl.setopt(crl.WRITEDATA, b_obj)
        crl.perform()
        crl.close()
        get_body = b_obj.getvalue()
    except:
        return ("Błąd pobierania getInventoryCategories")
    else:
        data = get_body.decode()
        data_json = json.loads(data)
        s = json.dumps(data_json, ensure_ascii=False, indent=4)
        #print(data_json["categories"])
        #return (data_json["categories"])
    return data_json["categories"]