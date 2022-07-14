from celery import shared_task
import urllib.parse
from datetime import timedelta, datetime
import pycurl
import certifi
from io import BytesIO
import json
import collections
#from Invboard_app.home.models import *
from django.utils import timezone

token = "3010303-3033261-P9RYU1VP0NHZZXULX9C0NDY1WY7CD455S3QSRKGF1QCFGU43OT28CJBD3FHDVKPB"

def pobierz_statusy_anulowanych():
    try:
        b_obj = BytesIO()
        url = 'https://api.baselinker.com/connector.php'

        methodParams = {}

        params = {
            'token': token,
            "method": "getOrderStatusList",
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
        return ("Błąd pobierania getInventoryProductsList")
    else:
        data = get_body.decode()
        data_json = json.loads(data)
        s = json.dumps(data_json, ensure_ascii=False, indent=4)
        anulowane_statusy = []
        for elm in data_json['statuses']:
            if "Anulowane" in elm["name"]:
                anulowane_statusy.append(elm['id'])
        return(anulowane_statusy)

def pobierz_zamowienia(pobierz_od):
    pobrane_zamowienia = []
    lista_anulowanych = pobierz_statusy_anulowanych()
    while(True):
        try:
            b_obj = BytesIO()
            url = 'https://api.baselinker.com/connector.php'

            methodParams = {"date_confirmed_from": pobierz_od, "get_unconfirmed_orders": "false"}

            params = {
                'token': token,
                "method": "getOrders",
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
            return ("Błąd pobierania getInventoryProductsList")
        else:
            data = get_body.decode()
            data_json = json.loads(data)
            s = json.dumps(data_json, ensure_ascii=False, indent=4)
            for zam in data_json['orders']:
                if zam['order_status_id'] not in lista_anulowanych:
                    #print("Status {} nie jest w anulowanych {}".format(zam['order_status_id'], lista_anulowanych))
                    for prod in zam['products']:
                        if len(prod['product_id']) >= 9:
                            pobrane_zamowienia.append([prod['ean'], prod['quantity']])
            #print(len(data_json['orders']))
            if(len(data_json['orders']) < 100):
                #print("koniec pobierania")
                break
            #print("jade dalej")
            pobierz_od = data_json['orders'][99]['date_confirmed']

    print("Ile pobranych zamowien: "+str(len(pobrane_zamowienia)))
    return(pobrane_zamowienia)

def sprawdz_do_zmiany(ean, inventory_id):
    pobrane_zamowienia = []
    lista_anulowanych = pobierz_statusy_anulowanych()

    try:
        b_obj = BytesIO()
        url = 'https://api.baselinker.com/connector.php'

        methodParams = {"filter_ean": ean, "inventory_id": inventory_id}

        params = {
            'token': token,
            "method": "getInventoryProductsList",
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
        return ("Błąd pobierania getInventoryProductsList")
    else:
        data = get_body.decode()
        data_json = json.loads(data)
        s = json.dumps(data_json, ensure_ascii=False, indent=4)
        #print(data_json['products'])
        if(len(data_json['products']) == 1):
            return 0
        najwieksza_ilosc = znajdz_najwieksza_ilosc(data_json['products'])
        tablica_roznicowa = policz_roznice(najwieksza_ilosc, data_json['products'])
        return tablica_roznicowa

def znajdz_najwieksza_ilosc(produkty):
    numery_id = list(produkty.keys())
    najwieksza_ilosc = 0
    klucze = list(produkty[numery_id[0]]['stock'].keys())
    numer_magazynu = klucze[0] #numer magazynu bl_42111
    for idx in range(0, len(produkty)):
        if(idx+1 == len(produkty)):
            return najwieksza_ilosc
        else:
            if(produkty[numery_id[idx]]['stock'][numer_magazynu] > produkty[numery_id[idx + 1]]['stock'][numer_magazynu]):
                najwieksza_ilosc = produkty[numery_id[idx]]['stock'][numer_magazynu]


def policz_roznice(najwieksza_ilosc, produkty):
    roznica = 0
    numery_id = list(produkty.keys())
    klucze = list(produkty[numery_id[0]]['stock'].keys())
    numer_magazynu = klucze[0]  # numer magazynu bl_42111

    for prod in produkty.values():
        if (int(prod['stock'][numer_magazynu]) < int(najwieksza_ilosc)):
            roznica_produktu = int(najwieksza_ilosc) - int(prod['stock'][numer_magazynu])
            roznica = roznica +  roznica_produktu# jezeli jest mniejsze niz roznica, to dodaj do zmiennej roznica roznice miedzy najwieksza iloscia a tym produktem

    stan_do_zmiany = int(najwieksza_ilosc) - roznica
    lst_do_zmiany = {}
    for prod in produkty.values():
        lst_do_zmiany[prod['id']] = {numer_magazynu: stan_do_zmiany}
    return lst_do_zmiany

if __name__ == '__main__':
    dt = datetime.now() - timedelta(days = 1) #pobieraj z dnia wczesniej od tej godziny co jest teraz
    produkty_z_zamowienia = pobierz_zamowienia(datetime.timestamp(dt)) #pobieranie tylko produktow z zamowien
    lst_do_zmiany = {}
    for prod in produkty_z_zamowienia:
        lst_do_zmiany_part = sprawdz_do_zmiany(prod[0], 32811)
        if(lst_do_zmiany_part != 0):
            lst_do_zmiany['products'] = (lst_do_zmiany_part)
    print(lst_do_zmiany)