from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from djmoney.models.fields import MoneyField
from djmoney.models.fields import CurrencyField
from country.models import Country

from payroll.income import PayPeriod, IncomeType
from utils import create_money


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
    pay_period = models.PositiveIntegerField(choices=PayPeriod.choices)
    currency = CurrencyField()
    date = models.DateField()

    def __str__(self):
        return self.version


class TaxContribution(models.Model):

    revision = models.ForeignKey(Revision, on_delete=models.CASCADE)
    tax = models.CharField(max_length=25)
    type = models.PositiveIntegerField(choices=TaxType.choices)
    pay_by = models.PositiveIntegerField(choices=PayBy.choices)
    taken_from = models.PositiveIntegerField(choices=IncomeType.choices)
    percental = models.DecimalField(max_digits=19, decimal_places=4)
    percental = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    fixed_deduction_amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
        blank=True,
        null=True,
    )
    mandatory = models.BooleanField(default=True)

    def clean(self):
        errors = {}

        if self.fixed_deduction_amount:
            if self.percental:
                errors["fixed_deduction_amount"] = _("cannot set both")
        if self.percental:
            if self.fixed_deduction_amount:
                errors["percental"] = _("cannot set both")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.tax}"


class Clause(models.Model):
    revision = models.ForeignKey(Revision, on_delete=models.CASCADE)
    line_num = models.CharField(max_length=19)
    start = models.DecimalField(max_digits=19, decimal_places=4)
    end = models.DecimalField(max_digits=19, decimal_places=4, blank=True, null=True)
    excess_over = models.DecimalField(max_digits=19, decimal_places=4, default=0.00)
    percent = models.DecimalField(max_digits=19, decimal_places=4, default=1.00)
    addition = models.DecimalField(max_digits=19, decimal_places=4, default=0.00)

    def __str__(self):
        return f"{self.revision} {self.line_num} {self.percent}"

    class Meta:
        unique_together = ("revision", "line_num")
