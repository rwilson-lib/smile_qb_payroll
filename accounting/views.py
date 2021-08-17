from django.shortcuts import render

# Create your views here.


from rest_framework import viewsets

from .models import Account, Journal, Transaction, GeneralLedger, LineItem

from .serializers import (
    AccountSerializer,
    JournalSerializer,
    TransactionSerializer,
    GeneralLedgerSerializer,
    LineItemSerializer,
)


class AccountView(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class JournalView(viewsets.ModelViewSet):
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer


class TransactionView(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class GeneralLedgerView(viewsets.ModelViewSet):
    queryset = GeneralLedger.objects.all()
    serializer_class = GeneralLedgerSerializer


class LineItemView(viewsets.ModelViewSet):
    queryset = LineItem.objects.all()
    serializer_class = LineItemSerializer
