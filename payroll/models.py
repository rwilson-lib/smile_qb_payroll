from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Q, Sum
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import CurrencyField, MoneyField
from djmoney.money import Currency, Money
from djmoney.settings import CURRENCY_CHOICES, DEFAULT_CURRENCY

from accounting.models import (
    Account,
    GeneralLedger,
    LineItem,
    Transaction,
    TransactionType,
)
from employee.models import Employee, EmployeePosition
from payroll.income import Income, IncomeType, PayPeriod
from tax.models import PayBy, Revision, TaxContribution
from tax.tax_calc import calculate_tax 

from .queries import (
    get_addition_group_by_addition,
    get_deductions_group_by_credit,
    get_tax_contributions_group_by_taxes,
)


def get_default_credit_account():
    item = 1
    return item


def get_default_currency():
    currency = "USD"
    return currency


def get_default_secondary_currency():
    currency = "LRD"
    return currency


def get_local_currency():
    currency = "LRD"
    return currency


def check_money(money_one, money_two):
    if type(money_one) is Money and \
       type(money_two) is Money:
        if money_one == money_two:
            return True
            
    return False


def automatic_convertion_allow():
    return True


# {{{ ExchangeRate
class ExchangeRate(models.Model):
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
        # Disable all the no-member violations in this function
        # pylint: disable=no-member

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
        return f"{self.foreign.amount} {self.foreign_currency} -> {self.local.amount} {self.local_currency}"

# }}}

# {{{ Payroll

class Payroll(models.Model):
    class Status(models.IntegerChoices):
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
    currency = CurrencyField(choices=CURRENCY_CHOICES, default=get_default_currency)
    tax_revision = models.ForeignKey(Revision, on_delete=models.CASCADE)
    fraction = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    rate = models.ForeignKey(
        ExchangeRate, on_delete=models.CASCADE, null=True, blank=True
    )
    status = models.IntegerField(choices=Status.choices, default=Status.CREATED)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    __lines = None

    def __get_total(self):
        self.__lines = PayrollEmployee.objects.filter(payroll=self.id)

    @property
    def count_lines(self):
        if self.__lines is None:
            self.__get_total()

        return self.__lines.aggregate(lines=Count("id"))["lines"]

    @property
    def total_salary(self):
        if self.__lines is None:
            self.__get_total()
        return Money(
            self.__lines.aggregate(earnings=Sum("earnings"))["earnings"], self.currency
        )

    @property
    def total_gross(self):
        if self.__lines is None:
            self.__get_total()

        return Money(
            self.__lines.aggregate(gross_income_sum=Sum("gross_income"))[
                "gross_income_sum"
            ],
            self.currency,
        )

    @property
    def total_credit_deduction(self):
        deductions = PayrollDeduction.objects.filter(payroll_employee__payroll=self.id)
        return Money(
            deductions.aggregate(deduction=Sum("amount"))["deduction"], self.currency
        )

    @property
    def total_addition(self):
        addition = Addition.objects.filter(payroll_employee__payroll=self.id)
        return Money(
            addition.aggregate(addition=Sum("amount"))["addition"], self.currency
        )

    @property
    def total_taxes(self):
        taxes = TaxContributionCollector.objects.filter(
            payroll_employee__payroll=self.id
        )
        return Money(taxes.aggregate(total=Sum("amount"))["total"], self.currency)

    @classmethod
    def pre_create(cls, sender, instance, *args, **kwargs):
        transaction = Transaction(comment="")

    @classmethod
    def post_create_or_update(cls, sender, instance, created, *args, **kwargs):
        if instance.status == instance.Status.APPROVED:
            taxes_results = get_tax_contributions_group_by_taxes(instance)
            additions = get_addition_group_by_addition(instance)
            deductions = get_deductions_group_by_credit(instance)
            ledger = []
            for result in taxes_results:
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        account_id=instance.account_id,
                        transaction_type=TransactionType.DEBIT,
                        amount=Money(result["total"], "USD") * -1.00,
                    )
                )
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        account_id=result["contribution__account"],
                        transaction_type=TransactionType.CREDIT,
                        amount=Money(result["total"], "USD"),
                    )
                )
            for result in additions:
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        account_id=instance.account_id,
                        transaction_type=TransactionType.DEBIT,
                        amount=Money(result["total"], "USD") * -1.00,
                    )
                )
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        account_id=result["item__account"],
                        transaction_type=TransactionType.CREDIT,
                        amount=Money(result["total"], "USD"),
                    )
                )
            for result in deductions:
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        account_id=instance.account_id,
                        transaction_type=TransactionType.DEBIT,
                        amount=Money(result["total"], "USD") * -1.00,
                    )
                )
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        account_id=result["payment_plan__credit__account"],
                        transaction_type=TransactionType.CREDIT,
                        amount=Money(result["total"], "USD"),
                    )
                )
            GeneralLedger.objects.bulk_create(ledger)
        elif instance.status == instance.Status.PAID:
            taxes_results = get_tax_contributions_group_by_taxes(instance)
            additions = get_addition_group_by_addition(instance)
            deductions = get_deductions_group_by_credit(instance)
            ledger = []
            for result in taxes_results:
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        account_id=result["contribution__account"],
                        transaction_type=TransactionType.DEBIT,
                        amount=Money(result["total"], "USD") * -1.00,
                    )
                )
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        account_id=8,
                        transaction_type=TransactionType.CREDIT,
                        amount=Money(result["total"], "USD"),
                    )
                )
            for result in additions:
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        account_id=result["item__account"],
                        transaction_type=TransactionType.DEBIT,
                        amount=Money(result["total"], "USD") * -1.00,
                    )
                )
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        # hard cored bank
                        account_id=8,
                        transaction_type=TransactionType.CREDIT,
                        amount=Money(result["total"], "USD"),
                    )
                )
            for result in deductions:
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        account_id=result["payment_plan__credit__account"],
                        transaction_type=TransactionType.DEBIT,
                        amount=Money(result["total"], "USD") * -1.00,
                    )
                )
                ledger.append(
                    GeneralLedger(
                        transaction_id=1,
                        # hard cored bank
                        account_id=8,
                        transaction_type=TransactionType.CREDIT,
                        amount=Money(result["total"], "USD"),
                    )
                )
            GeneralLedger.objects.bulk_create(ledger)

    def __str__(self):
        return f'{self.date.strftime("%b %d %Y")}'
# }}}

# {{{ Credit

class Credit(models.Model):
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
        if not created:
            status = instance.is_completed
            if status != instance.completed:
                Credit.objects.filter(pk=instance.id).update(completed=status)

    @property
    def is_completed(self):
        balance = self.balance
        if balance > Money(0.00, balance.currency):
            return False
        return True

    @property
    def total_deduction(self):
        deduction_plans = self.creditpaymentplan_set.all()
        total_paid = Money(0.00, self.amount_currency)
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
        # Disable all the no-member violations in this function
        # pylint: disable=no-member
        money = Money(0.00, self.amount.currency)
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

# }}}

# {{{ CreditPaymentPlan

class CreditPaymentPlan(models.Model):
    class Status(models.IntegerChoices):
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
        if self.credit.completed:
            return None
        default = Money("0.00", get_default_currency())
        balance = self.credit.balance
        value = self.credit.amount * self.percent
        if balance <= default:
            return None
        if value >= balance:
            return balance
        return value

    @property
    def total_paid_on_plan(self):
        total = self.payrolldeduction_set.aggregate(sum=Sum("amount"))["sum"] or 0.00
        return Money(total, get_default_currency())

    def __str__(self):
        return f"{self.name}, {self.credit}, {self.percent}"


# }}}

# {{{ PayrollEmployee

class PayrollEmployee(models.Model):
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

    __taxes = None
    __deductions = None
    __pay_period = None

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

        collection = namedtuple('TaxCollection', ['collection', 'total_by_employee', 'total_by_employer'])
        collection.collection = []
        collection.total_by_employee=Income(PayPeriod(self.payroll.pay_period), Money(0.00, self.payroll.currency))
        collection.total_by_employer=Income(PayPeriod(self.payroll.pay_period), Money(0.00, self.payroll.currency))

        for emp_tax_n_contrib in queryset:
            income = self._select_income_function(IncomeType(emp_tax_n_contrib.taken_from))
            if emp_tax_n_contrib.currency != income.money.currency.code: 
                tax = calculate_tax(emp_tax_n_contrib, self._try_convert_currency(income))
                tax = self._try_convert_currency(tax.convert_to(income.pay_period))

                if emp_tax_n_contrib.pay_by == PayBy.EMPLOYEE:
                    collection.total_by_employee = collection.total_by_employee + tax
                if emp_tax_n_contrib.pay_by == PayBy.EMPLOYER:
                    collection.total_by_employer = collection.total_by_employer + tax
                    
                collection.collection.append(
                    TaxContributionCollector(
                        contribution = emp_tax_n_contrib,
                        payroll_employee = self,
                        amount = tax.money
                    )
                )

            else:
                l.append(calculate_tax(emp_tax_n_contrib, income))

        return l

    def _calc_deduction(self):
        queryset = CreditPaymentPlan.objects.filter(
                Q(credit__employee=self.employee.employee.id)
              & Q(credit__completed=False)
              & Q(status=CreditPaymentPlan.Status.ACTIVE)
        )

        collection = namedtuple('PayrollDeductionCollection',['collection', 'total'])
        collection.collection = []
        collection.total=Income(PayPeriod(self.payroll.pay_period), Money(0.00, self.payroll.currency))

        for item in queryset:
            income =  Income(PayPeriod(self.payroll.pay_period), item.deduct())
            if self.payroll.currency != income.money.currency.code:
                if self.payroll.rate:
                    if not automatic_convertion_allow():
                        raise TypeError('currency dont match and auto convert is not allow')
                    collection.total = collection.total + self._try_convert_currency(income)
                    collection.collection.append(
                        PayrollDeduction(
                            payroll_employee=self,
                            payment_plan=item,
                            amount=self._try_convert_currency(income).money
                        )
                    )
            else:
                collection.total = collection.total + income
                collection.collection.append(
                    PayrollDeduction(
                        payroll_employee=self,
                        payment_plan=item,
                        amount=income.money
                    )
                )
        return collection


    def _try_convert_currency(self, income):

        if self.payroll.currency == income.money.currency:
            return income

        if self.payroll.rate is None:
            raise TypeError("rate is needed for the convertion")

        if  not self.payroll.rate.foreign_currency == self.payroll.currency and \
            not self.payroll.rate.local_currency == self.payroll.currency:
            raise TypeError("rate can not be use for convertion")

        if  not self.payroll.rate.foreign_currency == str(income.money.currency) and \
            not self.payroll.rate.local_currency == str(income.money.currency):
            raise TypeError("rate can not be use for convertion")

        income.money = self.payroll.rate.exchange(income.money)
        return income

    def _earnings(self, faction=None):
        income = None 

        if self.employee.position.wage_type == self.employee.position.WageType.SALARIED:
            income = self.employee.total_earnings
            if income.money.currency.code != self.payroll.currency:
                if not automatic_convertion_allow():
                    raise TypeError('currency dont match and auto convert is not allow')
                income = self._try_convert_currency(income.convert_to(PayPeriod(self.payroll.pay_period)))
            else:
                income = income.convert_to(PayPeriod(self.payroll.pay_period))

        elif (
            self.employee.position.wage_type == self.employee.position.WageType.PER_RATE
        ):
            if self.hour_worked is None:
                raise TypeError(
                    "can't perform calculation for {self.employee.position.wage_type}"
                )
            income = self.employee.negotiated_salary_wage * hour_worked
            Income(PayPeriod(self.employee.pay_period), income)

        if self.payroll.fraction:
            income = income * self.payroll.fraction
          
        return income


    def _extra_income(self):
        extra_sum = self.addition_set.aggregate(sum=Sum("amount"))["sum"] or 0.00
        return Income(
            PayPeriod(self.payroll.pay_period),
            Money(extra_sum, self.earnings.currency),
        )

    def _gross_income(self):
        total = self.extra_income + self.earnings
        return Income(PayPeriod(self.payroll.pay_period), total)

    def _income_tax(self):
        if self.__taxes is None:
            self._total_deductions()

        return Income(
            PayPeriod(self.payroll.pay_period),
            self._gross_income().money - self.__taxes,
        )

    def _net_income(self):
        net = self._gross_income() - self._income_tax()
        return net


    def _total_deductions(self):
        total_emp_tax = sum(
            t.amount
            for t in self._calc_taxes()
            if t.contribution.pay_by == PayBy.EMPLOYEE
        )
        total_emp_deduction = sum(t.amount for t in self._calc_deduction())
        self.__taxes = total_emp_tax
        self.__deductions = total_emp_deduction
        return {
            "tax_n_contribution": self.__taxes,
            "deduction": self.__deductions,
            "total": self.__taxes + self.__deductions,
        }

    def update_calc_props(self):
        self.earnings = self._earnings().money
        self.net_income = self._net_income().money
        self.gross_income = self._gross_income().money
        self.income_tax = self._income_tax().money
        self.extra_income = self._extra_income().money
        self.deductions = self._total_deductions()["total"]
        self.save()

    @classmethod
    def pre_create(cls, sender, instance, *args, **kwargs):
        instance.earnings = instance._earnings().money
        instance.net_income = instance._net_income().money
        instance.gross_income = instance._gross_income().money
        instance.income_tax = instance._income_tax().money
        instance.extra_income = instance._extra_income().money
        instance.deductions = instance._total_deductions()["total"]

    @classmethod
    def post_create_or_update(cls, sender, instance, created, *args, **kwargs):
        if created:
            PayrollDeduction.objects.bulk_create(instance._calc_deduction())
            TaxContributionCollector.objects.bulk_create(instance._calc_taxes())
            instance.update_calc_props()

    def clean(self):
        errors = {}

        if self.payroll.status > Payroll.Status.REVIEW:
            errors["payroll"] = _(
                f"cant add to a {self.payroll.get_status_display()} payroll"
            )
        if not self.employee.employee.active:
            errors["employee"] = _(f"can't add an inactive employee to payroll")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.payroll} {self.employee}"

    class Meta:
        unique_together = ("payroll", "employee")
        ordering = ["-payroll"]


# }}}

# {{{ Addition
class Addition(models.Model):
    payroll_employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE)
    item = models.ForeignKey(LineItem, on_delete=models.CASCADE)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
    )

    def convert_currency(self):
        pass
    
    class Meta:
        unique_together = ("payroll_employee", "item")

    @classmethod
    def post_create_or_update(cls, sender, instance, *args, **kwargs):
        instance.payroll_employee.update_calc_props()

    @classmethod
    def post_delete(cls, sender, instance, *args, **kwargs):
        instance.payroll_employee.update_calc_props()

    def clean(self):

        errors = {}
        if self.payroll_employee.payroll.currency != self.amount_currency: 
            errors["amount"] = _(
                f" Item currency {self.amount.currency} does not match payroll currency {self.payroll_employee.payroll.currency }"
            )

        if self.payroll_employee.payroll.status > Payroll.Status.REVIEW:
            errors["payroll_employee"] = _(
                f"cant add to a {self.payroll_employee.payroll.get_status_display()} payroll"
            )


        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.payroll_employee} {self.item} {self.amount}"


# }}}

# {{{ PayrollDeduction

class PayrollDeduction(models.Model):
    payroll_employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE)
    payment_plan = models.ForeignKey(CreditPaymentPlan, on_delete=models.CASCADE)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
    )

    class Meta:
        unique_together = ("payroll_employee", "payment_plan")

    def mark_as_completed(self):
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
        instance.mark_as_completed()
        instance.payroll_employee.update_calc_props()

    @classmethod
    def post_delete(cls, sender, instance, *args, **kwargs):
        instance.mark_as_completed()
        instance.payroll_employee.update_calc_props()

    def clean(self):
        # Disable all the no-member violations in this function
        # pylint: disable=no-member
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
        return f"{self.payroll_employee} {self.payment_plan} {self.amount}"
# }}}

# {{{ EmployeeTaxContribution

class EmployeeTaxContribution(models.Model):
    employee = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)
    tax = models.ForeignKey(
        TaxContribution,
        on_delete=models.CASCADE,
        limit_choices_to={
            'active': True,
            'mandatory': False
        },
)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("employee", "tax")

    def clean(self):
        # Disable all the no-member violations in this function
        # pylint: disable=no-member
        errors = {}

        if self.tax.mandatory:
            errors["tax"] = _("mandatory item are added by default")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.employee} {self.tax}"

# }}}

# {{{ TaxContributionCollector
class TaxContributionCollector(models.Model):
    contribution = models.ForeignKey(TaxContribution, on_delete=models.CASCADE)
    payroll_employee = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", get_default_currency()),
        default_currency=get_default_currency(),
    )

    def __str__(self):
        return f"{self.contribution}, {self.amount}"
# }}}

# {{{ TimeSheet
class TimeSheet(models.Model):
    employee = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)
    date  = models.DateField()
    clock_start_time =  models.TimeField()
    clock_end_time = models.TimeField()
    break_start_time =  models.TimeField()
    break_end_time = models.TimeField()

    def employee_total_hours(self, employee_id):
        TimeSheet.objects.filter(employee=self.employee)
# }}}

# {{{ Models Signals

pre_save.connect(Payroll.pre_create, sender=Payroll)
post_save.connect(Payroll.post_create_or_update, sender=Payroll)

pre_save.connect(PayrollEmployee.pre_create, sender=PayrollEmployee)
post_save.connect(PayrollEmployee.post_create_or_update, sender=PayrollEmployee)

post_save.connect(Addition.post_create_or_update, sender=Addition)
post_delete.connect(Addition.post_delete, sender=Addition)

post_save.connect(PayrollDeduction.post_create_or_update, sender=PayrollDeduction)
post_delete.connect(PayrollDeduction.post_delete, sender=PayrollDeduction)

post_save.connect(Credit.post_create_or_update, sender=Credit)

# }}}
