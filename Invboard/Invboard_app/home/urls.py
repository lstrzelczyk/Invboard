# -*- encoding: utf-8 -*-

from django.urls import path, re_path
from Invboard_app.home import views

urlpatterns = [

    # The home page
    path('', views.index, name='home'),

    #stany views
    re_path(r'stany/', views.stany, name='stany'),
    re_path(r"synchronizacja_stanow", views.ajax_stany),
    re_path(r"zapisz_kategorie", views.zapisz_kategorie),
    re_path(r"dane_baselinker", views.zapisz_dane_baselinker),

    #strony home
    re_path(r'home/', views.home, name='home'),

    path('dashboard.html', views.index, name='home'),

]
