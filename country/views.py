from django.shortcuts import render
from django.http import JsonResponse
from django.core import serializers

from .models import Country

def get_country_states(request, id):
    if request.method == 'GET':
        states = Country.objects.get(pk=id).state_set.all().order_by('name')
        data = serializers.serialize("json", states, fields=("id", "name"))
        return JsonResponse(data, safe=False)

