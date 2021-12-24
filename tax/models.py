from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Count
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import CurrencyField, MoneyField
from djmoney.money import Money

from country.models import Country
from payroll.income import IncomeType, PayPeriod
from accounting.models import Account
from utils import create_money

from djmoney.settings import CURRENCY_CHOICES


class TaxType(models.IntegerChoices):
    INCOME = 0
    SOCIAL_SECURITY = 1
    OTHER = 2


class PayBy(models.IntegerChoices):
    EMPLOYEE = 0
    EMPLOYER = 1


class Revision(models.Model):
    version = models.CharField(max_length=10)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"Version: {self.version}"


class TaxContribution(models.Model):
    # Disable all the unused-variable violations in this function
    # pylint: disable=unused-variable
    class CalcMode(models.IntegerChoices):
        RuleBase = 0
        Percentage = 1
        Fixed = 2

    class AllowIncomeType(models.IntegerChoices):
        SALARY = IncomeType.SALARY
        GROSS = IncomeType.GROSS
        NET = IncomeType.NET
        DEDUCTION = IncomeType.DEDUCTION
        EXTRA = IncomeType.EXTRA

    tax_period = models.PositiveIntegerField(choices=PayPeriod.choices)
    tax = models.CharField(max_length=25)
    type = models.PositiveIntegerField(choices=TaxType.choices)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    revision = models.ForeignKey(
        Revision, on_delete=models.CASCADE, blank=True, null=True
    )
    calc_mode = models.IntegerField(
        choices=CalcMode.choices, default=CalcMode.Percentage
    )
    pay_by = models.PositiveIntegerField(choices=PayBy.choices)
    taken_from = models.PositiveIntegerField(choices=AllowIncomeType.choices)
    currency = CurrencyField(choices=CURRENCY_CHOICES)
    value = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    mandatory = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.tax}"


class Clause(models.Model):
    # Disable all the unused-variable violations in this function
    # pylint: disable=unused-variable
    tax_contrib = models.ForeignKey(TaxContribution, on_delete=models.CASCADE)
    line_num = models.CharField(max_length=19)
    start = models.DecimalField(max_digits=19, decimal_places=4)
    end = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    excess_over = models.DecimalField(max_digits=19, decimal_places=4, default=0.00)
    percent = models.DecimalField(max_digits=19, decimal_places=4, default=1.00)
    addition = models.DecimalField(max_digits=19, decimal_places=4, default=0.00)

    def __str__(self):
        return f"{self.tax_contrib} {self.line_num}"

    class Meta:
        unique_together = ("tax_contrib", "line_num")
