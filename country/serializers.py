from rest_framework import serializers
from .models import Country, State


class CountrySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Country
        fields = ["id"]


class StateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = State
        fields = ["id"]
