"""
Manages employee payroll info.

This Models handles deductions and addition.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Q, Sum
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import CurrencyField, MoneyField
from djmoney.money import Money
from djmoney.settings import CURRENCY_CHOICES

# from djmoney.settings import CURRENCY_CHOICES, DEFAULT_CURRENCY

from collections import namedtuple

from accounting.models import (
    Account,
    GeneralLedger,
    LineItem,
    # Transaction,
)
from employee.models import Employee, EmployeePosition, EmployeeAccount
from payroll.income import Income, IncomeType, PayPeriod
from tax.models import PayBy, Revision, TaxContribution
from tax.tax_calc import calculate_tax


def get_default_credit_account():
    """Return default credit account."""
    item = 1
    return item


def get_default_currency():
    """Return default currency."""
    currency = "USD"
    return currency


def get_default_secondary_currency():
    """Return secondary default currency if dual currency."""
    currency = "LRD"
    return currency


def get_local_currency():
    """Return default local currency."""
    currency = "LRD"
    return currency


def check_money(money_one, money_two):
    """Check if money is of the same type."""
    if type(money_one) is Money and type(money_two) is Money:
        if money_one == money_two:
            return True
    return False


def automatic_convertion_allow():
    """Check if automatic convertion is allow."""
    return True


class ExchangeRate(models.Model):
    """Model for storing and managing User define exchange rate."""

    foreign = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
    )
    local = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
    )
    date = models.DateField(default=timezone.now)

    def exchange(self, money):
        """Try to convert currency."""
        if not type(money) is Money:
            raise ValueError("must be of the class Money")

        if money.currency == self.foreign.currency:
            value = money.amount * self.local.amount
            return Money(value, self.local.currency)
        if money.currency == self.local.currency:
            value = money.amount / self.local.amount
            return Money(value, self.foreign.currency)

        raise ValueError("Operation not allowed")

    def __str__(self):
        """Overide tostring."""
        return f"{self.foreign.amount} {self.foreign_currency}\
        -> {self.local.amount} {self.local_currency}"


class Payroll(models.Model):
    """Model for managing payroll master record."""

    class Status(models.IntegerChoices):
        """Payroll stages enums."""

        CREATED = 0
        REVIEW = 1
        CLOSED = 2
        APPROVED = 3
        PAID = 4

    number = models.CharField(max_length=25, blank=True, null=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    pay_period = models.PositiveIntegerField(
        choices=PayPeriod.choices, default=PayPeriod.MONTHLY
    )
    date = models.DateField()
    currency = CurrencyField(
        choices=CURRENCY_CHOICES, default=get_default_currency
    )
    tax_revision = models.ForeignKey(Revision, on_delete=models.CASCADE)
    fraction = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    rate = models.ForeignKey(
        ExchangeRate, on_delete=models.CASCADE, null=True, blank=True
    )
    status = models.IntegerField(
        choices=Status.choices, default=Status.CREATED
    )
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    __lines = None

    def __get_lines(self):
        self.__lines = PayrollEmployee.objects.filter(payroll=self.id)

    @property
    def count_lines(self):
        """Lazy line count."""
        if self.__lines is None:
            self.__get_lines()

        return self.__lines.aggregate(lines=Count("id"))["lines"]

    @property
    def total_salary(self):
        """Calculate total salary on payroll."""
        if self.__lines is None:
            self.__get_lines()
        return Money(
            self.__lines.aggregate(earnings=Sum("earnings"))["earnings"],
            self.currency,
        )

    @property
    def total_gross(self):
        """Calculate total gross income on payroll."""
        if self.__lines is None:
            self.__get_lines()

        return Money(
            self.__lines.aggregate(gross_income_sum=Sum("gross_income"))[
                "gross_income_sum"
            ],
            self.currency,
        )

    @property
    def total_credit_deduction(self):
        """Calculate total credit deducted."""
        deductions = PayrollDeduction.objects.filter(
            payroll_employee__payroll=self.id
        )
        return Money(
            deductions.aggregate(deduction=Sum("amount"))["deduction"],
            self.currency,
        )

    @property
    def total_addition(self):
        """Calculate the total addition on salary."""
        addition = Addition.objects.filter(payroll_employee__payroll=self.id)
        return Money(
            addition.aggregate(addition=Sum("amount"))["addition"],
            self.currency,
        )

    @property
    def total_taxes(self):
        """Calculate the total taxes."""
        taxes = TaxContributionCollector.objects.filter(
            payroll_employee__payroll=self.id
        )
        return Money(
            taxes.aggregate(total=Sum("amount"))["total"], self.currency
        )

    @classmethod
    def pre_create(cls, sender, instance, *args, **kwargs):
        """Call before a record is save."""
        # transaction = Transaction(comment="")
        pass

    @classmethod
    def post_create_or_update(cls, sender, instance, created, *args, **kwargs):
        """Call after a record is create or updated."""
        if instance.status in range(
            instance.Status.REVIEW, instance.Status.CLOSED
        ):
            taxes = TaxContributionCollector.objects.filter(
                payroll_employee__payroll=instance
            )
            deductions = PayrollDeduction.objects.filter(
                payroll_employee__payroll=instance
            )
            taxes.delete()
            deductions.delete()

        if instance.status == instance.Status.CLOSED:
            if instance.__lines is None:
                instance.__get_lines()

            for item in instance.__lines:
                item.update_calc_props()
                taxncontribs = item._calc_taxes().collection
                deductions = item._calc_deduction().collection
                TaxContributionCollector.objects.bulk_create(taxncontribs)
                PayrollDeduction.objects.bulk_create(deductions)

        elif instance.status == instance.Status.APPROVED:
            if instance.__lines is None:
                instance.__get_lines()

            total_gross = instance.total_gross

            GeneralLedger(
                transaction_id=1,
                debit_account=instance.account,
                debit_amount=total_gross * -1.00,
                credit_account=instance.account,
                credit_amount=total_gross,
            ).save()

        elif instance.status == instance.Status.PAID:
            if instance.__lines is None:
                instance.__get_lines()

            for item in instance.__lines:
                account = (
                    EmployeeAccount.objects.filter(
                        employee=item.employee.employee,
                        current=True,
                        active=True,
                    )
                    or None
                )
                if account is None:
                    # Call some function function
                    print(f"None {item.employee}")
                elif len(account) > 1:
                    # Call some function function
                    print(f"Many current account {item.employee}")
                else:
                    GeneralLedger(
                        transaction_id=1,
                        debit_account=account[0].bank,
                        debit_amount=item.net_income * -1.00,
                        credit_account=account[0].link_acc,
                        credit_amount=item.net_income,
                    ).save()

            # GeneralLedger.objects.bulk_create(ledger)

    def __str__(self):
        """Overide tostring."""
        return f'{self.date.strftime("%b %d %Y")}'


class Credit(models.Model):
    """Model for storing and managing employee Credit."""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    item = models.CharField(max_length=100)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
    )
    amount_currency = CurrencyField(choices=CURRENCY_CHOICES)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    date = models.DateField(default=timezone.now)
    payment_start_date = models.DateField()
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, default=get_default_credit_account
    )
    completed = models.BooleanField(default=False)

    @classmethod
    def post_create_or_update(cls, sender, instance, created, *args, **kwargs):
        """Call after a record is create or updated."""
        if not created:
            status = instance.is_completed
            if status != instance.completed:
                Credit.objects.filter(pk=instance.id).update(completed=status)

    @property
    def is_completed(self):
        """Check if a payment on a plan have been completed."""
        balance = self.balance
        if balance > Money(0.00, balance.currency):
            return False
        return True

    @property
    def total_deduction(self):
        """Return the total amount deductions."""
        deduction_plans = self.creditpaymentplan_set.all()
        total_paid = Money(0.00, self.amount_currency)
        for deduction_plan in deduction_plans:
            total_paid += deduction_plan.total_paid_on_plan

        return total_paid

    @property
    def balance(self):
        """Calculate the balance due."""
        total_paid = self.total_deduction
        debt = self.amount
        interest = self.interest
        total = debt + interest
        balance = total - total_paid

        return balance

    @property
    def interest(self):
        """Calculate the interest rate."""
        money = Money(0.00, self.amount.currency)
        if not self.interest_rate:
            return money
        money.amount = self.amount.amount * self.interest_rate
        return money

    class Meta:
        """Meta class attributes."""

        ordering = ["-date"]

    def clean(self):
        """Validate form data."""
        errors = {}

        if self.date > timezone.now().date():
            errors["date"] = _("date cannot be set to the future")

        if self.payment_start_date < timezone.now().date():
            errors["payment_start_date"] = _(
                "payment cannot begin in the pass"
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        """Overide tostring."""
        return f"{self.employee} {self.item} {self.amount} {self.date}"


class CreditPaymentPlan(models.Model):
    """Model for storing and managing payment plan."""

    class Status(models.IntegerChoices):
        """Credit Payment Plan Status Enum."""

        CANCEL = 0
        ACTIVE = 1
        PAUSED = 2
        SKIP_NEXT_PAID = 3
        COMPLETED = 4

    credit = models.ForeignKey(Credit, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    deduct_from = models.IntegerField(
        choices=IncomeType.choices, default=IncomeType.NET
    )
    percent = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.IntegerField(choices=Status.choices, default=Status.ACTIVE)

    def deduct(self):
        """Deduct the value speficed by a payment plan."""
        default = Money("0.00", self.credit.amount_currency)
        if self.credit.completed:
            return default

        balance = self.credit.balance
        value = self.credit.amount * self.percent
        if balance <= default:
            return default
        if value >= balance:
            return balance
        return value

    @property
    def total_paid_on_plan(self):
        """Calculate the total paid on a payment plan."""
        total = (
            self.payrolldeduction_set.aggregate(sum=Sum("amount"))["sum"]
            or 0.00
        )
        return Money(total, get_default_currency())

    def __str__(self):
        """Overide tostring."""
        return f"{self.name}, {self.credit}, {self.percent}"


class PayrollEmployee(models.Model):
    """Model holds Payroll line item."""

    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)
    employee = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)
    hour_worked = models.PositiveIntegerField(blank=True, null=True)
    gross_income = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
        editable=False,
    )
    income_tax = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
        editable=False,
    )
    net_income = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
        editable=False,
    )
    deductions = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
        editable=False,
    )
    extra_income = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
        editable=False,
    )
    earnings = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
        editable=False,
    )

    def _select_income_function(self, income, *args, **kwargs):
        if not isinstance(income, IncomeType):
            raise TypeError(f"income must be of type {IncomeType}")
        if income == IncomeType.SALARY:
            return self._earnings(*args, **kwargs)
        if income == IncomeType.NET:
            return self._net_income(*args, **kwargs)
        if income == IncomeType.GROSS:
            return self._gross_income(*args, **kwargs)
        if income == IncomeType.EXTRA:
            return self._extra_income(*args, **kwargs)

        raise NotImplementedError("Not Implemented")

    def _calc_taxes(self):
        employee_current_position = self.employee
        queryset = TaxContribution.objects.filter(
            active=True, mandatory=True
        ).union(
            TaxContribution.objects.filter(
                employeetaxcontribution__employee=employee_current_position,
                employeetaxcontribution__active=True,
            )
        )

        collection = namedtuple(
            "TaxCollection",
            ["collection", "total_by_employee", "total_by_employer"],
        )
        collection.collection = []
        collection.total_by_employee = Income(
            PayPeriod(self.payroll.pay_period),
            Money(0.00, self.payroll.currency),
        )
        collection.total_by_employer = Income(
            PayPeriod(self.payroll.pay_period),
            Money(0.00, self.payroll.currency),
        )

        for emp_tax_n_contrib in queryset:
            income = self._select_income_function(
                IncomeType(emp_tax_n_contrib.taken_from)
            )
            if emp_tax_n_contrib.currency != income.money.currency.code:
                tax = calculate_tax(
                    emp_tax_n_contrib, self._try_convert_currency(income)
                )
                tax = self._try_convert_currency(
                    tax.convert_to(income.pay_period)
                )

                if emp_tax_n_contrib.pay_by == PayBy.EMPLOYEE:
                    collection.total_by_employee = (
                        collection.total_by_employee + tax
                    )
                if emp_tax_n_contrib.pay_by == PayBy.EMPLOYER:
                    collection.total_by_employer = (
                        collection.total_by_employer + tax
                    )

                collection.collection.append(
                    TaxContributionCollector(
                        contribution=emp_tax_n_contrib,
                        payroll_employee=self,
                        amount=tax.money,
                    )
                )

            else:
                tax = calculate_tax(emp_tax_n_contrib, income)
                tax = tax.convert_to(income.pay_period)

                if emp_tax_n_contrib.pay_by == PayBy.EMPLOYEE:
                    collection.total_by_employee = (
                        collection.total_by_employee + tax
                    )
                if emp_tax_n_contrib.pay_by == PayBy.EMPLOYER:
                    collection.total_by_employer = (
                        collection.total_by_employer + tax
                    )

                collection.collection.append(
                    TaxContributionCollector(
                        contribution=emp_tax_n_contrib,
                        payroll_employee=self,
                        amount=tax.money,
                    )
                )

        return collection

    def _calc_deduction(self):
        queryset = CreditPaymentPlan.objects.filter(
            Q(credit__employee=self.employee.employee.id)
            & Q(credit__completed=False)
            & Q(status=CreditPaymentPlan.Status.ACTIVE)
        )

        collection = namedtuple(
            "PayrollDeductionCollection", ["collection", "total"]
        )
        collection.collection = []
        collection.total = Income(
            PayPeriod(self.payroll.pay_period),
            Money(0.00, self.payroll.currency),
        )

        for item in queryset:
            income = Income(PayPeriod(self.payroll.pay_period), item.deduct())
            if self.payroll.currency != income.money.currency.code:
                if self.payroll.rate:
                    if not automatic_convertion_allow():
                        raise TypeError(
                            "currency dont match and auto convert is not allow"
                        )
                    collection.total = (
                        collection.total + self._try_convert_currency(income)
                    )
                    collection.collection.append(
                        PayrollDeduction(
                            payroll_employee=self,
                            payment_plan=item,
                            amount=self._try_convert_currency(income).money,
                        )
                    )
            else:
                collection.total = collection.total + income
                collection.collection.append(
                    PayrollDeduction(
                        payroll_employee=self,
                        payment_plan=item,
                        amount=income.money,
                    )
                )
        return collection

    def _try_convert_currency(self, income):

        if self.payroll.currency == income.money.currency:
            return income

        if self.payroll.rate is None:
            raise TypeError("rate is needed for the convertion")

        if (
            not self.payroll.rate.foreign_currency == self.payroll.currency
            and not self.payroll.rate.local_currency == self.payroll.currency
        ):
            raise TypeError("rate can not be use for convertion")

        if not self.payroll.rate.foreign_currency == str(
            income.money.currency
        ) and not self.payroll.rate.local_currency == str(
            income.money.currency
        ):
            raise TypeError("rate can not be use for convertion")

        income.money = self.payroll.rate.exchange(income.money)
        return income

    def _earnings(self, faction=None):
        income = None

        if (
            self.employee.position.wage_type
            == self.employee.position.WageType.SALARIED
        ):
            income = self.employee.total_earnings
            if income.money.currency.code != self.payroll.currency:
                if not automatic_convertion_allow():
                    raise TypeError(
                        "currency dont match and auto convert is not allow"
                    )
                income = self._try_convert_currency(
                    income.convert_to(PayPeriod(self.payroll.pay_period))
                )
            else:
                income = income.convert_to(PayPeriod(self.payroll.pay_period))

        elif (
            self.employee.position.wage_type
            == self.employee.position.WageType.PER_RATE
        ):
            if self.hour_worked is None:
                raise TypeError(
                    "can't perform calculation for\
                    {self.employee.position.wage_type}"
                )
            income = self.employee.negotiated_salary_wage * self.hour_worked
            Income(PayPeriod(self.employee.pay_period), income)

        if self.payroll.fraction:
            income = income * self.payroll.fraction

        return income

    def _extra_income(self):

        queryset = self.addition_set.values("amount_currency").annotate(
            sum=Sum("amount")
        )
        earings = self._earnings()
        extra_income = Income(
            PayPeriod(self.payroll.pay_period),
            Money(0.00, self.payroll.currency),
        )

        for item in queryset:
            income = Income(
                PayPeriod(self.payroll.pay_period),
                Money(item.get("sum"), item.get("amount_currency")),
            )
            if item.get("amount_currency") != earings.money.currency.code:
                if self.payroll.rate:
                    if not automatic_convertion_allow():
                        raise TypeError(
                            "currency dont match and auto convert is not allow"
                        )
                    extra_income = extra_income + self._try_convert_currency(
                        income
                    )
            else:
                extra_income = extra_income + income

        return extra_income

    def _gross_income(self):
        total = self._extra_income() + self._earnings()
        return total

    def _income_tax(self):
        return self._calc_taxes().total_by_employee

    def _deductions(self):
        return self._calc_deduction().total

    def _net_income(self):
        net = self._gross_income() - self._income_tax()
        return net

    def update_calc_props(self):
        """Update calculate props at runtime."""
        self.earnings = self._earnings().money
        self.net_income = self._net_income().money
        self.gross_income = self._gross_income().money
        self.income_tax = self._income_tax().money
        self.extra_income = self._extra_income().money
        self.deductions = self._deductions().money
        # Fixed this prevent from sending signal
        self.save()

    @classmethod
    def pre_create(cls, sender, instance, *args, **kwargs):
        """Call before a record is created."""
        instance.earnings = instance._earnings().money
        instance.net_income = instance._net_income().money
        instance.gross_income = instance._gross_income().money
        instance.income_tax = instance._income_tax().money
        instance.extra_income = instance._extra_income().money
        instance.deductions = instance._deductions().money

    @classmethod
    def post_create_or_update(cls, sender, instance, created, *args, **kwargs):
        """Call after a record is created or updated."""
        pass

    def clean(self):
        """Validate form data."""
        errors = {}

        if self.payroll.status > Payroll.Status.REVIEW:
            errors["payroll"] = _(
                f"cant add to a {self.payroll.get_status_display()} payroll"
            )
        if not self.employee.employee.active:
            errors["employee"] = _("can't add an inactive employee to payroll")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        """Overide tostring."""
        return f"{self.payroll} {self.employee}"

    class Meta:
        """Meta class attributes."""

        unique_together = ("payroll", "employee")
        ordering = ["-payroll"]


class Addition(models.Model):
    """Model for managing additional entry to payroll."""

    payroll_employee = models.ForeignKey(
        PayrollEmployee, on_delete=models.CASCADE
    )
    item = models.ForeignKey(LineItem, on_delete=models.CASCADE)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
    )

    class Meta:
        """Meta class attributes."""

        unique_together = ("payroll_employee", "item")

    @classmethod
    def post_create_or_update(cls, sender, instance, *args, **kwargs):
        """Call after a record is create or updated."""
        instance.payroll_employee.update_calc_props()

    @classmethod
    def post_delete(cls, sender, instance, *args, **kwargs):
        """Call after a record is deleted."""
        instance.payroll_employee.update_calc_props()

    def clean(self):
        """Validate form data."""
        errors = {}
        if self.payroll_employee.payroll.currency != self.amount_currency:
            errors["amount"] = _(
                f" Item currency {self.amount.currency} does not match payroll\
                currency {self.payroll_employee.payroll.currency }"
            )

        if self.payroll_employee.payroll.status > Payroll.Status.REVIEW:
            errors["payroll_employee"] = _(
                f"cant add to a {self.payroll_employee.payroll.get_status_display()}\
                payroll"
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        """Overide tostring."""
        return f"{self.payroll_employee} {self.item} {self.amount}"


class PayrollDeduction(models.Model):
    """Model for managing payroll deduction record."""

    payroll_employee = models.ForeignKey(
        PayrollEmployee, on_delete=models.CASCADE
    )
    payment_plan = models.ForeignKey(
        CreditPaymentPlan, on_delete=models.CASCADE
    )
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
    )

    class Meta:
        """Meta class attributes."""

        unique_together = ("payroll_employee", "payment_plan")

    def mark_as_completed(self):
        """Mark the deductable as completed when the balance is zero."""
        if self.payment_plan.credit.is_completed is True:
            self.payment_plan.credit.completed = True
            self.payment_plan.status = CreditPaymentPlan.Status.COMPLETED
            self.payment_plan.credit.save()
            self.payment_plan.save()
        else:
            self.payment_plan.credit.completed = False
            self.payment_plan.status = CreditPaymentPlan.Status.ACTIVE
            self.payment_plan.credit.save()
            self.payment_plan.save()

    @classmethod
    def post_create_or_update(cls, sender, instance, created, *args, **kwargs):
        """Call after a record is create or updated."""
        instance.mark_as_completed()

    @classmethod
    def post_delete(cls, sender, instance, *args, **kwargs):
        """Call after the record is deleted."""
        instance.mark_as_completed()

    def clean(self):
        """Validate form data."""
        errors = {}

        payroll_emp_id = self.payroll_employee.employee.employee.id
        plan_emp_id = self.payment_plan.credit.employee.id

        if payroll_emp_id != plan_emp_id:
            errors["plan"] = _("deducting from the wrong employee")

        if self.amount.amount == 0.00:
            errors["amount"] = _("amount cannot be zero")

        if self.amount_currency != self.plan.credit.amount_currency:
            errors["amount"] = _("wrong currency")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        """Overide tostring."""
        return f"{self.payroll_employee} {self.payment_plan} {self.amount}"


class EmployeeTaxContribution(models.Model):
    """Model for holding employee Tax and Contribution."""

    employee = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)
    tax = models.ForeignKey(
        TaxContribution,
        on_delete=models.CASCADE,
        limit_choices_to={"active": True, "mandatory": False},
    )
    active = models.BooleanField(default=True)

    class Meta:
        """Meta class attributes."""

        unique_together = ("employee", "tax")

    def clean(self):
        """Validate form data."""
        errors = {}

        if self.tax.mandatory:
            errors["tax"] = _("mandatory item are added by default")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        """Overide tostring."""
        TaxContribution
        return f"{self.employee} {self.tax}"


class TaxContributionCollector(models.Model):
    """Model for storing and managing Tax and Contribution collection."""

    contribution = models.ForeignKey(TaxContribution, on_delete=models.CASCADE)
    payroll_employee = models.ForeignKey(
        PayrollEmployee, on_delete=models.CASCADE
    )
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
    )

    def __str__(self):
        """Overide tostring."""
        return f"{self.contribution}, {self.amount}"


class TimeSheet(models.Model):
    """Collect and store employee timesheet information."""

    employee = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)
    date = models.DateField()
    clock_start_time = models.TimeField()
    clock_end_time = models.TimeField()
    break_start_time = models.TimeField()
    break_end_time = models.TimeField()

    def employee_total_hours(self, employee_id):
        """Calculate employee total hour work."""
        TimeSheet.objects.filter(employee=self.employee)


pre_save.connect(Payroll.pre_create, sender=Payroll)
post_save.connect(Payroll.post_create_or_update, sender=Payroll)

pre_save.connect(PayrollEmployee.pre_create, sender=PayrollEmployee)
post_save.connect(
    PayrollEmployee.post_create_or_update, sender=PayrollEmployee
)

post_save.connect(Addition.post_create_or_update, sender=Addition)
post_delete.connect(Addition.post_delete, sender=Addition)

post_save.connect(
    PayrollDeduction.post_create_or_update, sender=PayrollDeduction
)
post_delete.connect(PayrollDeduction.post_delete, sender=PayrollDeduction)

post_save.connect(Credit.post_create_or_update, sender=Credit)
