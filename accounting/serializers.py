from rest_framework import serializers

from .models import Account, Journal, Transaction, GeneralLedger, LineItem


class AccountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
        ]


class JournalSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Journal
        fields = [
            "id",
        ]


class TransactionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
        ]


class GeneralLedgerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GeneralLedger
        fields = [
            "id",
        ]


class LineItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LineItem
        fields = [
            "id",
        ]
