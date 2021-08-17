from django.db import models
from django.db.models import Sum
from django.utils import timezone
from djmoney.models.fields import CurrencyField, MoneyField
from djmoney.money import Money
from djmoney.settings import CURRENCY_CHOICES
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class TransactionType(models.IntegerChoices):
    DEBIT = 0
    CREDIT = 1


class AccountType(models.IntegerChoices):
    BANK = 0
    ACCOUNTSRECEIVABLE = 1
    OTHERCURRENTASSET = 2
    FIXEDASSET = 3
    OTHERASSET = 4
    ACCOUNTSPAYABLE = 5
    CREDITCARD = 6
    OTHERCURRENTLIABILITY = 7
    LONGTERMLIABILITY = 8
    EQUITY = 9
    INCOME = 10
    COST_OF_GOODSSOLD = 11
    EXPENSE = 12
    OTHERINCOME = 13
    OTHEREXPENSE = 14
    NONPOSTING = 15


def account_num_is_required():
    return True


class Account(models.Model):
    type = models.IntegerField(choices=AccountType.choices)
    currency = CurrencyField(choices=CURRENCY_CHOICES)
    name = models.CharField(max_length=50, unique=True)
    account_num = models.CharField(max_length=30, unique=True, blank=True, null=True)
    bank_number = models.CharField(max_length=25, unique=True, blank=True, null=True)
    ending_balance_amt = models.DecimalField(
        max_digits=14, decimal_places=2, default=0.00, blank=True, null=True
    )
    parent_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_hidden = models.BooleanField(default=False)

    @property
    def balance(self):
        balance = GeneralLedger.objects.filter(account=self).aggregate(
            balance=Sum("amount")
        )["balance"]
        return balance

    def clean(self):
        errors = {}

        if self.type == AccountType.BANK:
            if self.bank_number is None:
                errors["bank_number"] = _(
                    "Account of type BANK must have a bank number"
                )
        if account_num_is_required():
            if self.account_num is None:
                errors["account_num"] = _("account number is required")

        if self.type == TransactionType.CREDIT:
            if self.amount.amount < 0:
                errors["transaction_type"] = _("credit balance must be positive")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.account_num} - {self.name}, {self.balance}"


class Journal(models.Model):
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now)
    credit_account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="credit_account"
    )
    debit_account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="debit_account"
    )

    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
    )


class Transaction(models.Model):
    class Status(models.IntegerChoices):
        OPEN = 0
        CLOSED = 1

    comment = models.CharField(max_length=25, blank=True, null=True)
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=25, blank=True, null=True, editable=False)
    status = models.IntegerField(choices=Status.choices, default=Status.OPEN)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}"


class GeneralLedger(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    account = models.ForeignKey(
        Account, related_name="account", on_delete=models.CASCADE
    )
    # change to entry_type
    transaction_type = models.IntegerField(choices=TransactionType.choices)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
    )

    @classmethod
    def write(cls, transaction, account, entry_type, value):
        gl = GeneralLedger(
            transaction_id=transaction,
            account=account,
            transaction_type=entry_type,
            amount=value,
        )
        gl.save()

    def clean(self):
        errors = {}

        if self.transaction_type == TransactionType.DEBIT:
            if self.amount.amount > 0:
                errors["transaction_type"] = _("debit balance must be negative")

        if self.transaction_type == TransactionType.CREDIT:
            if self.amount.amount < 0:
                errors["transaction_type"] = _("credit balance must be positive")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.account.name} {self.amount}"


class LineItem(models.Model):
    name = models.CharField(max_length=25)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"
