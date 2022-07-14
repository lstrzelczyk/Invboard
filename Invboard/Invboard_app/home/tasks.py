from celery import shared_task
import urllib.parse
import pycurl
import certifi
from io import BytesIO
import json
import collections
from .models import *
from django.utils import timezone

@shared_task
def synchro_stan():

    t = UstawieniaStan.objects.get(nazwa="Ustawienia")
    t.czy_zlecono_synchronizacje = True
    t.save()

    kateg = Kategorie.objects.get(kategoria_nazwa="wszystkie")

    dane_dostepowe = UstawieniaBaselinker.objects.all()
    dane_baselinker = {}

    for dane in dane_dostepowe:
        if dane.nazwa == "newstyling":
            kategorie = kateg.kategoria_id
        else:
            kategorie = ""
        dane_baselinker[dane.nazwa] = {
            "token":dane.token,
            "inventory_id":dane.inventory_id,
            "categories": kategorie #1494973
            }

    tablica_NS = (pobierz_liste_produktow(dane_baselinker["newstyling"]["token"],
                                  dane_baselinker["newstyling"]["inventory_id"],
                                  dane_baselinker["newstyling"]["categories"]))


    tablica_TEST = (pobierz_liste_produktow(dane_baselinker["test"]["token"],
                                          dane_baselinker["test"]["inventory_id"],
                                          dane_baselinker["test"]["categories"]))



    #print(tablica_NS)
    #print(tablica_TEST)

    tablica_NS_TEST = porownaj_tablice(tablica_NS, tablica_TEST) #zwraca dict różnicy pomiedzy ns (głowny) a test
    wynik = zaaktualizuj_stany(dane_baselinker["test"]["token"], dane_baselinker["test"]["inventory_id"], tablica_NS_TEST)
    print(wynik)

    t = UstawieniaStan.objects.get(nazwa="Ustawienia")
    t.ostatnia_data = timezone.now()
    t.czy_zlecono_synchronizacje = False
    t.save()



def pobierz_liste_produktow(token, inventory_id, categories):
    #pobiera podstawowa liste produktow (samo id, nazwa)
    for page in range(1, 100):
        try:
            b_obj = BytesIO()
            url = 'https://api.baselinker.com/connector.php'

            methodParams = {"inventory_id":inventory_id, "filter_category_id": categories, "page": page}

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
            return("Błąd pobierania getInventoryProductsList")
        else:
            data = get_body.decode()
            data_json = json.loads(data)
            s = json.dumps(data_json, ensure_ascii=False, indent=4)
            print("Pobrano: "+str(len(data_json['products'])))
            print("strona: "+str(page))
            print("Nowa paczka:")
            print(data_json['products'].keys())
            if len(data_json['products']) < 1000: #sprawdz czy jest coś jeszcze do pobrania
                break

    tablica_products = json.loads(s)
    tab_stan_obrobiona = wyciagnij_id(tablica_products) #wyciaganie id baselinkera produktow
    tab_data = produkt_data(tab_stan_obrobiona, token, inventory_id) #na podstawie product id (listy) wyciaganie danych
    temp_kod_producenta = wyciagnij_nr_katalogowy_producenta(tab_data) #na podstawie listy danych wyciaganie nuemerow producenta
    lista_producentow = wyciagnij_nazwe_producenta(produkt_producenci(token)) #tworzenie listy producentow
    tablica_gotowa = przypisz_nazwe_kategorii(lista_producentow, temp_kod_producenta)
    return(tablica_gotowa)

def wyciagnij_id(tablica_stany):
    tab_stan_obrobiona = []
    #print(tablica_stany)
    for elm in tablica_stany['products']:
        tab_stan_obrobiona.append(elm)
    return(tab_stan_obrobiona)



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
        #print("Pobrano:".(data_json["products"]))
        return(data_json["products"])

def wyciagnij_nr_katalogowy_producenta(tablica_stany):
    tab_stan_obrobiona = []
    #print(tablica_stany)
    for key, value in tablica_stany.items():
        inven = collections.OrderedDict(value["stock"])
        keys = list(inven)
        manufacturer_id = value["manufacturer_id"]
        numer_katalogowy_producenta = value["text_fields"]["features"]["Numer katalogowy producenta"]
        numer_katalogu = str(keys[0])
        ilosc = int(value["stock"][keys[0]])
        numer_produktu_baselinker = int(key)
        tab_stan_obrobiona.append([manufacturer_id, numer_katalogowy_producenta, numer_katalogu, ilosc, numer_produktu_baselinker])
    return(tab_stan_obrobiona)

def produkt_producenci(token):
    try:
        b_obj = BytesIO()
        url = 'https://api.baselinker.com/connector.php'

        methodParams = {}

        params = {
            # 46-2561-F00633A9B89B76FFB045886D3D5231F64431B734397F3BE66CC7A96AC7E128B2,
            'token': token,
            "method": "getInventoryManufacturers",
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
        return("Błąd pobierania getInventoryManufacturers")
    else:
        data = get_body.decode()
        data_json = json.loads(data)
        s = json.dumps(data_json, ensure_ascii=False, indent=4)
        #print(data_json["products"])
        return(data_json["manufacturers"])

def wyciagnij_nazwe_producenta(tablica_producenci):
    tab_producenci_obrobiona = []
    #print(tablica_producenci)
    for elm in tablica_producenci:
        temp_tab = []
        temp_tab.append(elm["manufacturer_id"])
        temp_tab.append(elm["name"])
        tab_producenci_obrobiona.append(temp_tab)
    return(tab_producenci_obrobiona)

def przypisz_nazwe_kategorii(tablica_producentow, dane_produktow):
    dane_produktow_poprawione = []
    for elm in dane_produktow:
        for prod in tablica_producentow:
            if elm[0] == prod[0]:
                dane_produktow_poprawione.append([prod[1], elm[1], elm[2], elm[3], elm[4]])
    return dane_produktow_poprawione

def porownaj_tablice(tablica_ns, tablica_pozostale):
    tab_popr_stany = {}
    for elm_pozostale in tablica_pozostale:
        for elm_ns in tablica_ns:
            if elm_ns[1] == elm_pozostale[1]: #czy numery się zgadzaja
                if elm_ns[0] == elm_pozostale[0]: #czy producenci się zgadzaja
                    if elm_ns[3] != elm_pozostale[3]: #czy ilość się zgadzają
                        #print("Tablica NS:")
                        #print(elm_ns)
                        #print("tablica: pozostala: ")
                        #print(elm_pozostale)
                        tab_popr_stany[elm_pozostale[4]] = {elm_pozostale[2]:elm_ns[3]}
    #print(tab_popr_stany)
    return tab_popr_stany

def zaaktualizuj_stany(token, inventory_id, produkty):
    try:
        b_obj = BytesIO()
        url = 'https://api.baselinker.com/connector.php'

        methodParams = {"inventory_id": inventory_id, "products": produkty}

        params = {
            # 46-2561-F00633A9B89B76FFB045886D3D5231F64431B734397F3BE66CC7A96AC7E128B2,
            'token': token,
            "method": "updateInventoryProductsStock",
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
        #print(data_json["products"])
        return(s)

if __name__ == '__main__':
    synchro_stan()