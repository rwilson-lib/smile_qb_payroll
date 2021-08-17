from .models import Country, State
from rest_framework import viewsets
from .serializers import CountrySerializer, StateSerializer


class CountryView(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class StateView(viewsets.ModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
