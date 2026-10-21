from django.shortcuts import render
from .models import StoreSettings, Banner


def store_settings(request):
    settings = StoreSettings.get()
    return {"store": settings}
