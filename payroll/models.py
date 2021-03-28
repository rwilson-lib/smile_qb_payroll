from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import CurrencyField, MoneyField

from employee.models import Employee, EmployeePosition
from payroll.income import Income, IncomeType, PayPeriod
from tax.models import PayBy, Revision, TaxContribution
from tax.tax_calc import test_tax
from utils import create_money


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
        # Disable all the no-member violations in this function
        # pylint: disable=no-member
        if money.currency == self.foreign.currency:
            value = money.amount * self.local.amount
            return create_money(value, self.local.currency)
        if money.currency == self.local.currency:
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
    amount_currency = CurrencyField()
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    date = models.DateField(default=timezone.now)
    payment_start_date = models.DateField()
    completed = models.BooleanField(default=False, editable=False)

    @classmethod
    def post_create_or_update(cls, sender, instance, created, *args, **kwargs):
        if not created:
            status = instance.is_completed
            if status != instance.completed:
                Deductable.objects.filter(pk=instance.id).update(completed=status)

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
        money = create_money(0.00, self.amount.currency)
        if not self.interest_rate:
            return money
        money.amount = self.amount.amount * self.interest_rate
        return money

    class Meta:
        ordering = ["-date"]

    def clean(self):
        errors = {}

        if self.date > timezone.now().date():
            errors["date"] = _("date cannot be set to the future")

        if self.payment_start_date < timezone.now().date():
            errors["payment_start_date"] = _("payment cannot begin in the pass")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.employee} {self.item} {self.amount} {self.date}"


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
            return None
        default = create_money("0.00", "USD")
        balance = self.deductable.balance
        value = amount * self.percent
        if balance <= default:
            self.mark_as_completed()
            return None
        if value >= balance:
            self.mark_as_completed()
            return balance
        return value

    @property
    def total_paid_on_plan(self):
        total = self.payrolldeduction_set.aggregate(sum=Sum("amount"))["sum"] or 0.00
        return create_money(total, "USD")

    def __str__(self):
        return f"{self.name}, {self.deductable}, {self.percent}"


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
    deductions = MoneyField(
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

        raise NotImplementedError()

    def _calc_taxes(self):
        def percental_or_fixed(tax, item):
            if tax.percental:
                percentage = item * tax.percental
                return percentage
            if tax.fixed_value:
                return item - tax.fixed_value
            return None

        return [
            TaxContributionCollector(
                contribution=emp_tax,
                payroll_employee=self,
                amount=percental_or_fixed(
                    emp_tax.tax,
                    self._select_income_function(
                        IncomeType(emp_tax.tax.taken_from)
                    ).money,
                ),
            )
            for emp_tax in self.employee.employeetaxcontribution_set.all()
        ]

    def _earnings(self):
        return self.employee.total_earnings.convert_to(
            PayPeriod(self.payroll.pay_period)
        )

    def _extra_income(self):
        extra_sum = self.payrollextra_set.aggregate(sum=Sum("amount"))["sum"] or 0.00
        return Income(
            PayPeriod(self.payroll.pay_period),
            create_money(extra_sum, self.earnings.currency),
        )

    def _calc_deduction(self):
        return [
            PayrollDeduction(payroll_employee=self, plan=active_plan, amount=amount)
            for active_plan in DeductionPlan.objects.filter(
                Q(status=DeductionPlan.Status.ACTIVE)
                & Q(deductable__completed=False)
                & Q(deductable__employee=self.employee.employee.id)
            )
            for amount in [
                active_plan.deduct(
                    self._select_income_function(
                        IncomeType(active_plan.deduct_from)
                    ).money
                )
            ]
            if amount
        ]

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
        net = self._gross_income() - self._income_tax()
        return net

    def _take_home(self):
        take_home = self._net_income() - self._total_deductions()["total"]
        return take_home

    def _total_deductions(self):
        total_deductions = {
            "tax_n_contribution": create_money(0.00, "USD"),
            "deduction": create_money(0.00, "USD"),
        }

        for contrib_tax in self._calc_taxes():
            if contrib_tax.contribution.tax.pay_by == PayBy.EMPLOYEE:
                total_deductions["tax_n_contribution"] += contrib_tax.amount
        for deduction in self._calc_deduction():
            total_deductions["deduction"] += deduction.amount

        total_deductions["total"] = (
            total_deductions["tax_n_contribution"] + total_deductions["deduction"]
        )
        return total_deductions

    def update_calc_props(self):
        self.earnings = self._earnings().money
        self.net_income = self._net_income().money
        self.gross_income = self._gross_income().money
        self.income_tax = self._income_tax().money
        self.extra_income = self._extra_income().money
        self.take_home = self._take_home().money
        self.deductions = self._total_deductions()["total"]
        self.save()

    @classmethod
    def pre_create(cls, sender, instance, *args, **kwargs):
        instance.earnings = instance._earnings().money
        instance.net_income = instance._net_income().money
        instance.gross_income = instance._gross_income().money
        instance.income_tax = instance._income_tax().money
        instance.extra_income = instance._extra_income().money
        instance.take_home = instance._take_home().money
        instance.deductions = instance._total_deductions()["total"]

    @classmethod
    def post_create_or_update(cls, sender, instance, created, *args, **kwargs):
        if created:
            PayrollDeduction.objects.bulk_create(instance._calc_deduction())
            TaxContributionCollector.objects.bulk_create(instance._calc_taxes())
            instance.update_calc_props()

    def clean(self):
        errors = {}

        if self.payroll.status == Payroll.Status.CLOSE:
            errors["payroll"] = _("cant add to a close payroll")
        if self.payroll.status == Payroll.Status.POSTED:
            errors["payroll"] = _("payroll already posted")

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
            errors["extra"] = _("cant add to a close payroll")
        if self.emp_payroll.payroll.status == Payroll.Status.POSTED:
            errors["extra"] = _("payroll already posted")

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

    @classmethod
    def post_delete(cls, sender, instance, *args, **kwargs):
        instance.payroll_employee.update_calc_props()

    def clean(self):
        # Disable all the no-member violations in this function
        # pylint: disable=no-member
        errors = {}

        payroll_emp_id = self.payroll_employee.employee.employee.id
        plan_emp_id = self.plan.deductable.employee.id

        if payroll_emp_id != plan_emp_id:
            errors["plan"] = _("deducting from the wrong employee")

        if self.amount.amount == 0.00:
            errors["amount"] = _("amount cannot be zero")

        if self.amount_currency != self.plan.deductable.amount_currency:
            errors["amount"] = _("wrong currency")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.payroll_employee} {self.plan} {self.amount}"


class EmployeeTaxContribution(models.Model):
    employee = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)
    tax = models.ForeignKey(TaxContribution, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.employee} {self.tax}"


class TaxContributionCollector(models.Model):
    contribution = models.ForeignKey(EmployeeTaxContribution, on_delete=models.CASCADE)
    payroll_employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
    )

    def __str__(self):
        return f"{self.contribution}, {self.amount}"


pre_save.connect(PayrollEmployee.pre_create, sender=PayrollEmployee)
post_save.connect(PayrollEmployee.post_create_or_update, sender=PayrollEmployee)
post_save.connect(PayrollExtra.post_create_or_update, sender=PayrollExtra)
post_delete.connect(PayrollExtra.post_delete, sender=PayrollExtra)
post_save.connect(PayrollDeduction.post_create_or_update, sender=PayrollDeduction)
post_delete.connect(PayrollDeduction.post_delete, sender=PayrollDeduction)

post_save.connect(Deductable.post_create_or_update, sender=Deductable)
