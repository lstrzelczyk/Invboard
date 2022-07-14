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

token = "46-2561-F00633A9B89B76FFB045886D3D5231F64431B734397F3BE66CC7A96AC7E128B2"

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
                    print("Status {} nie jest w anulowanych {}".format(zam['order_status_id'], lista_anulowanych))
                    for prod in zam['products']:
                        if len(prod['product_id']) == 10:
                            pobrane_zamowienia.append([prod['product_id'], prod['quantity']])
            #print(len(data_json['orders']))
            if(len(data_json['orders']) < 100):
                print("koniec pobierania")
                break
            print("jade dalej")
            pobierz_od = data_json['orders'][99]['date_confirmed']

    print(len(pobrane_zamowienia))
    print(pobrane_zamowienia)
    return(pobrane_zamowienia)

def recoding_tablicy_produktow(tablica_produktow):
    new_tablica_produktow = []
    for elm in tablica_produktow:
        print(elm[0])
        new_tablica_produktow.append(elm[0])
    return new_tablica_produktow

def produkt_data(product_id_tab, token, inventory_id):
    try:
        b_obj = BytesIO()
        url = 'https://api.baselinker.com/connector.php'

        methodParams = {"inventory_id":inventory_id, "products": product_id_tab}

        params = {
            # 46-2561-F00633A9B89B76FFB045886D3D5231F64431B734397F3BE66CC7A96AC7E128B2,
            'token': token,
            "method": "getInventoryProductsData",
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
        return("Błąd pobierania getInventoryProductsData")
    else:
        data = get_body.decode()
        data_json = json.loads(data)
        s = json.dumps(data_json, ensure_ascii=False, indent=4)
        print(s)
        return(data_json["products"])

def wyciagnij_nr_katalogowy_producenta(tablica_stany):
    tab_stan_obrobiona = []
    #print(tablica_stany)
    for key, value in tablica_stany.items():
        print("klucz "+key)
        inven = collections.OrderedDict(value["stock"])
        keys = list(inven)
        manufacturer_id = value["manufacturer_id"]
        numer_katalogowy_producenta = value["text_fields"]["features"]["Numer katalogowy producenta"]
        numer_katalogu = str(keys[0])
        ilosc = int(value["stock"][keys[0]])
        numer_produktu_baselinker = int(key)
        tab_stan_obrobiona.append([manufacturer_id, numer_katalogowy_producenta, numer_katalogu, ilosc, numer_produktu_baselinker])
    return(tab_stan_obrobiona)

if __name__ == '__main__':
    dt = datetime.now() - timedelta(hours = 1) #pobieraj z dnia wczesniej od tej godziny co jest teraz
    produkty_z_zamowienia = pobierz_zamowienia(datetime.timestamp(dt)) #pobieranie tylko produktow z zamowien
    re_produkty_z_zamowienia = recoding_tablicy_produktow(produkty_z_zamowienia) #wyciaganie tylko id, ilosc póżniej
    print(re_produkty_z_zamowienia)
    tab_data = produkt_data(re_produkty_z_zamowienia, token, 1480) #na podstawie product id (listy) wyciaganie danych
    temp_kod_producenta = wyciagnij_nr_katalogowy_producenta(tab_data) #na podstawie listy danych wyciaganie nuemerow producenta

    print(temp_kod_producenta)