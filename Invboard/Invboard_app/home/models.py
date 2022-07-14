# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Kategorie(models.Model):
    def __str__(self):
        return self.kategoria_nazwa
    kategoria_id = models.CharField(max_length=3500, blank=True, null=True)
    kategoria_nazwa = models.CharField(max_length=200, blank=True, null=True)

class UstawieniaStan(models.Model):
    def __str__(self):
        return self.nazwa
    nazwa = models.CharField(max_length=200, blank=True, null=True)
    czy_sprawdzony = models.BooleanField(default=False)
    czy_zlecono_synchronizacje = models.BooleanField(default=False)
    ostatnia_data = models.DateTimeField(default='2021-01-05 06:00:00.000000-09:00')

class UstawieniaBaselinker(models.Model):
    def __str__(self):
        return self.nazwa
    nazwa = models.CharField(max_length=200, blank=True, null=True)
    token = models.CharField(max_length=200, blank=True, null=True)
    inventory_id = models.IntegerField(blank=True, null=True)