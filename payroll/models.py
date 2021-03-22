from django.db import models
from django.db.models import Sum, Q
from django.db.models.signals import pre_save, post_save, post_delete
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from djmoney.models.fields import MoneyField
from djmoney.models.fields import CurrencyField

from tax.models import Revision
from tax.models import Tax
from employee.models import Employee
from employee.models import EmployeePosition
from employee.models import Department
from payroll.income import PayPeriod
from payroll.income import Income
from utils import create_money
from utils import total_amount

from tax.tax_calc import test_tax
from collections import namedtuple


class IncomeType(models.IntegerChoices):
    SALARY = 0
    NET = 1
    GROSS = 2
    EXTRA = 3


class ExchangeRate(models.Model):
    foreign = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
    )
    local = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
    )
    date = models.DateField(default=timezone.now)

    def exchange(self, money):
        if money.currency == self.foreign.currency:
            value = money.amount * self.local.amount
            return create_money(value, self.local.currency)
        elif money.currency == self.local.currency:
            value = money.amount / self.local.amount
            return create_money(value, self.foreign.currency)

        raise ValueError("Operation not allowed")

    def __str__(self):
        return f"{self.foreign} {self.local}"


class Payroll(models.Model):
    class Status(models.IntegerChoices):
        CREATED = 3
        REVIEW = 2
        POSTED = 1
        CLOSE = 0

    pay_period = models.PositiveIntegerField(
        choices=PayPeriod.choices, default=PayPeriod.MONTHLY
    )
    date = models.DateField()
    tax_revision = models.ForeignKey(Revision, on_delete=models.CASCADE)
    rate = models.ForeignKey(ExchangeRate, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, default=Status.CREATED)

    def __str__(self):
        return f"{self.date}"


class Deductable(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    item = models.CharField(max_length=100)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
    )
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    date = models.DateField(default=timezone.now)
    payment_start_date = models.DateField()
    completed = models.BooleanField(default=False, editable=False)

    @classmethod
    def post_create_or_update(cls, sender, instance, created, *args, **kwargs):
        if not created:
            c = instance.is_completed
            if c != instance.completed:
                Deductable.objects.filter(pk=instance.id).update(completed=c)

    @property
    def is_completed(self):
        balance = self.balance
        if balance > create_money(0.00, balance.currency):
            return False
        return True

    @property
    def total_deduction(self):
        deduction_plans = self.deductionplan_set.all()
        total_paid = create_money(0.00, self.amount_currency)
        for deduction_plan in deduction_plans:
            total_paid += deduction_plan.total_paid_on_plan

        return total_paid

    @property
    def balance(self):
        total_paid = self.total_deduction
        debt = self.amount
        interest = self.interest
        total = debt + interest
        balance = total - total_paid

        return balance

    @property
    def interest(self):
        i = create_money(0.00, self.amount.currency)
        if not self.interest_rate:
            return i
        i.amount = self.amount.amount * self.interest_rate
        return i

    class Meta:
        ordering = ["-date"]

    def clean(self):
        errors = {}

        if self.date > timezone.now().date():
            errors["date"] = _(f"date cannot be set to the future")

        if self.payment_start_date < timezone.now().date():
            errors["payment_start_date"] = _(f"payment cannot begin in the pass")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return "%s %s %s %s" % (self.employee, self.item, self.amount, self.date)


class EmployeeTax(models.Model):
    employee = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)
    tax = models.ForeignKey(Tax, on_delete=models.CASCADE)


class DeductionPlan(models.Model):
    class Status(models.IntegerChoices):
        CANCEL = 0
        ACTIVE = 1
        PAUSED = 2
        SKIP_NEXT_PAID = 3
        COMPLETED = 4

    deductable = models.ForeignKey(Deductable, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    deduct_from = models.IntegerField(
        choices=IncomeType.choices, default=IncomeType.NET
    )
    percent = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.IntegerField(choices=Status.choices, default=Status.ACTIVE)

    def mark_as_completed(self):
        self.status = self.Status.COMPLETED
        self.deductable.completed = True
        self.save()
        self.deductable.save()

    def deduct(self, amount):
        if self.deductable.completed:
            return
        default = create_money("0.00", "USD")
        balance = self.deductable.balance
        value = amount * self.percent
        if balance <= default:
            self.mark_as_completed()
            return
        elif value >= balance:
            self.mark_as_completed()
            return balance
        return value

    @property
    def total_paid_on_plan(self):
        sum = self.payrolldeduction_set.aggregate(sum=Sum("amount"))["sum"] or 0.00
        return create_money(sum, "USD")

    def __str__(self):
        return f"{self.name}, {self.deductable}, {self.percent}"


class Contribution(models.Model):
    class For(models.IntegerChoices):
        GOVERNMENT = 0
        WORK_UNION = 1
        OTHER = 2

    class DeductedFrom(models.IntegerChoices):
        SALARY = 0
        NET = 1
        GROSS = 2
        EXTRA = 3

    item = models.CharField(max_length=50)
    to = models.IntegerField(choices=For.choices)
    deducted_from = models.IntegerField(choices=DeductedFrom.choices)
    fix_amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
        blank=True,
        null=True,
    )
    percent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def clean(self):
        errors = {}

        if self.fix_amount:
            if self.percent:
                errors["fix_amount"] = _(f"cannot set both")

        if self.percent:
            if self.fix_amount:
                errors["percent"] = _(f"cannot set both")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.item}"


class PayrollEmployee(models.Model):

    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)
    employee = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)
    gross_income = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
        editable=False,
    )
    income_tax = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
        editable=False,
    )
    net_income = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
        editable=False,
    )
    total_deductions = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
        editable=False,
    )
    extra_income = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
        editable=False,
    )
    earnings = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
        editable=False,
    )
    take_home = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
        editable=False,
    )

    @property
    def calc_taxes(self):
        emp_taxes = self.employee.employeetax_set.all()
        taxes = {
            "employee": [],
            "employer": [],
        }

        def percental_or_fixed(tax, item):
            if tax.percental:
                percentage = item * tax.percental
                return percentage
            elif tax.fixed_value:
                return item - tax.fixed_value

        for emp_tax in emp_taxes:
            if emp_tax.tax.taken_from == emp_tax.tax.TakenFrom.SALARY:
                salary = self._earnings().money
                value = percental_or_fixed(emp_tax.tax, salary)
                if emp_tax.tax.pay_by == emp_tax.tax.PayBy.EMPLOYEE:
                    taxes["employee"].append(value)
                elif emp_tax.tax.pay_by == emp_tax.tax.PayBy.EMPLOYER:
                    taxes["employer"].append(value)
            elif emp_tax.tax.taken_from == emp_tax.tax.TakenFrom.GROSS:
                gross = self._gross_income()
                value = percental_or_fixed(emp_tax.tax, gross)
            elif emp_tax.tax.taken_from == emp_tax.tax.TakenFrom.NET:
                net = self._net_income()
                value = percental_or_fixed(emp_tax.tax, net)
            elif emp_tax.tax.taken_from == emp_tax.tax.TakenFrom.TAKE_HOME:
                take_home = self._take_home()
                value = percental_or_fixed(emp_tax.tax, take_home)
            elif emp_tax.tax.taken_from == emp_tax.tax.TakenFrom.EXTRA:
                extras = self._extra_income()
                value = percental_or_fixed(emp_tax.tax, extras)

        return taxes

    def _earnings(self):
        return self.employee.total_earnings.convert_to(
            PayPeriod(self.payroll.pay_period)
        )

    def _extra_income(self):
        sum = self.payrollextra_set.aggregate(sum=Sum("amount"))["sum"] or 0.00
        return Income(
            PayPeriod(self.payroll.pay_period),
            create_money(sum, self.earnings.currency),
        )

    def _select_income_function(self, income, *args, **kwargs):
        if not isinstance(income, IncomeType):
            raise TypeError(f"income must be of type {IncomeType}")
        elif income == IncomeType.SALARY:
            return self._earnings(*args, **kwargs)
        elif income == IncomeType.NET:
            return self._net_income(*args, **kwargs)
        elif income == IncomeType.GROSS:
            return self._gross_income(*args, **kwargs)
        elif income == IncomeType.EXTRA:
            return self._extra_income(*args, **kwargs)

        raise NotImplementedError()

    def _calc_deduction(self):
        active_plans = DeductionPlan.objects.filter(
            Q(status=DeductionPlan.Status.ACTIVE)
            & Q(deductable__completed=False)
            & Q(deductable__employee=self.employee.employee.id)
        )
        deductions = []
        for active_plan in active_plans:
            amount = active_plan.deduct(
                self._select_income_function(IncomeType(active_plan.deduct_from)).money
            )
            if amount:
                payroll_deduction = PayrollDeduction(
                    payroll_employee=self, plan=active_plan, amount=amount
                )
                deductions.append(payroll_deduction)
        return deductions

    def _total_deductions(self):
        sum = self.payrolldeduction_set.aggregate(sum=Sum("amount"))["sum"] or 0.00
        return Income(
            PayPeriod(self.payroll.pay_period),
            create_money(sum, self.earnings.currency),
        )

    def _gross_income(self):
        total = self.extra_income + self.earnings
        return Income(PayPeriod(self.payroll.pay_period), total)

    def _income_tax(self):
        rev = self.payroll.tax_revision
        rate = None
        if rev.currency != self.earnings.currency.code:
            rate = self.payroll.rate

        income = Income(PayPeriod(self.payroll.pay_period), self.gross_income)
        tax = test_tax(income, rev, rate)
        income_tax = tax.tax.convert_to(PayPeriod(self.payroll.pay_period))

        if rate:
            income_tax.money = rate.exchange(income_tax.money)
            return income_tax

        return income_tax

    def _net_income(self):
        other_emp_taxes = self.calc_taxes["employee"]
        total_other_emp_taxes = sum(other_emp_taxes)
        net = self._gross_income() - self._income_tax() - total_other_emp_taxes
        return net

    def _take_home(self):
        take_home = self._net_income() - self._total_deductions()
        return take_home

    def update_calc_props(self):
        self.earnings = self._earnings().money
        self.net_income = self._net_income().money
        self.gross_income = self._gross_income().money
        self.income_tax = self._income_tax().money
        self.extra_income = self._extra_income().money
        self.total_deductions = self._total_deductions().money
        self.take_home = self._take_home().money
        self.save()

    @classmethod
    def pre_create(cls, sender, instance, *args, **kwargs):
        instance.earnings = instance._earnings().money
        instance.net_income = instance._net_income().money
        instance.gross_income = instance._gross_income().money
        instance.income_tax = instance._income_tax().money
        instance.extra_income = instance._extra_income().money
        instance.total_deductions = instance._total_deductions().money
        instance.take_home = instance._take_home().money

    @classmethod
    def post_create_or_update(cls, sender, instance, created, *args, **kwargs):
        if created:
            PayrollDeduction.objects.bulk_create(instance._calc_deduction())
            instance.update_calc_props()

    def clean(self):
        errors = {}

        if self.payroll.status == Payroll.Status.CLOSE:
            errors["payroll"] = _(f"cant add to a close payroll")
        if self.payroll.status == Payroll.Status.POSTED:
            errors["payroll"] = _(f"payroll already posted")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.payroll} {self.employee}"

    class Meta:
        unique_together = ("payroll", "employee")
        ordering = ["-payroll"]


class PayrollExtra(models.Model):
    emp_payroll = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE)
    extra = models.CharField(max_length=25)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
    )

    @classmethod
    def post_create_or_update(cls, sender, instance, *args, **kwargs):
        instance.emp_payroll.update_calc_props()

    @classmethod
    def post_delete(cls, sender, instance, *args, **kwargs):
        instance.emp_payroll.update_calc_props()

    def clean(self):

        errors = {}

        if self.emp_payroll.payroll.status == Payroll.Status.CLOSE:
            errors["extra"] = _(f"cant add to a close payroll")
        if self.emp_payroll.payroll.status == Payroll.Status.POSTED:
            errors["extra"] = _(f"payroll already posted")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.emp_payroll} {self.extra} {self.amount}"


class PayrollDeduction(models.Model):
    payroll_employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE)
    plan = models.ForeignKey(DeductionPlan, on_delete=models.CASCADE)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
    )

    class Meta:
        unique_together = ("payroll_employee", "plan")

    @classmethod
    def post_create_or_update(cls, sender, instance, *args, **kwargs):
        instance.payroll_employee.update_calc_props()
        instance.plan

    @classmethod
    def post_delete(cls, sender, instance, *args, **kwargs):
        instance.payroll_employee.update_calc_props()

    def clean(self):
        errors = {}

        payroll_emp_id = self.payroll_employee.employee.employee.id
        plan_emp_id = self.plan.deductable.employee.id

        if payroll_emp_id != plan_emp_id:
            errors["plan"] = _(f"deducting from the wrong employee")

        if self.amount.amount == 0.00:
            errors["amount"] = _(f"amount cannot be zero")

        if self.amount_currency != self.plan.deductable.amount_currency:
            errors["amount"] = _(f"wrong currency")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.payroll_employee} {self.plan} {self.amount}"


class EmployeeContribution(models.Model):
    contribution = models.ForeignKey(Contribution, on_delete=models.CASCADE)
    employee = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)


pre_save.connect(PayrollEmployee.pre_create, sender=PayrollEmployee)
post_save.connect(PayrollEmployee.post_create_or_update, sender=PayrollEmployee)
post_save.connect(PayrollExtra.post_create_or_update, sender=PayrollExtra)
post_delete.connect(PayrollExtra.post_delete, sender=PayrollExtra)
post_save.connect(PayrollDeduction.post_create_or_update, sender=PayrollDeduction)
post_delete.connect(PayrollDeduction.post_delete, sender=PayrollDeduction)

post_save.connect(Deductable.post_create_or_update, sender=Deductable)
