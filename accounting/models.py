from django.db import models
from djmoney.models.fields import CurrencyField, MoneyField


class TransactionType(models.IntegerChoices):
    DEBIT = 0
    CREDIT = 1


class AccountType(models.IntegerChoices):
    Bank = 0
    AccountsReceivable = 1
    OtherCurrentAsset = 2
    FixedAsset = 3
    OtherAsset = 4
    AccountsPayable = 5
    CreditCard = 6
    OtherCurrentLiability = 7
    LongTermLiability = 8
    Equity = 9
    Income = 10
    CostOfGoodsSold = 11
    Expense = 12
    OtherIncome = 13
    OtherExpense = 14
    NonPosting = 15


class Account(models.Model):

    type = models.IntegerField(choices=AccountType.choices)
    currency = CurrencyField()
    account_num = models.CharField(max_length=30)
    name = models.CharField(max_length=50)
    description = models.TextField()
    is_hidden = models.BooleanField(default=False)
    parent_id = models.IntegerField(null=True, blank=True)
    ending_balance_amt = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    bank_number = models.CharField(max_length=25)


class Journal(models.Model):

    transaction_type = models.IntegerField(choices=TransactionType.choices)
    # from_account = models.ForeignKey(Account, on_delete=models.CASCADE)
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
    )


class Transaction(models.Model):
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id


class GeneralLedger(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    from_account = models.ForeignKey(
        Account, related_name="to_account", on_delete=models.CASCADE
    )
    from_account_transaction_type = models.IntegerField(choices=TransactionType.choices)
    to_account = models.ForeignKey(
        Account, related_name="from_account", on_delete=models.CASCADE
    )
    to_account_transaction_type = models.IntegerField(choices=TransactionType.choices)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
    )


class LineItem(models.Model):
    class ItemType(models.IntegerChoices):
        tax = 0
        deduction = 1
        addition = 2

    type = models.IntegerField(choices=ItemType.choices)
    name = models.CharField(max_length=25)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
