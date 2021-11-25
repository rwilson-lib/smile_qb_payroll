from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.db.models.signals import pre_save
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import CurrencyField, MoneyField
from djmoney.money import Money
from djmoney.settings import CURRENCY_CHOICES

from country.models import Country, State
from payroll.income import Income, PayPeriod, IncomeType
from accounting.models import Account
from utils import create_money


# TODO: Move benefit to a new app call benefit


class Benefit(models.Model):
    class Scope(models.IntegerChoices):
        Employee = 0
        Position = 1
        Job = 2
        Department = 3
        Grade = 4

    class CalcMode(models.IntegerChoices):
        Percentage = 0
        Fixed = 1
        RuleBase = 2

    class AllowIncomeType(models.IntegerChoices):
        SALARY = IncomeType.SALARY
        GROSS = IncomeType.GROSS
        NET = IncomeType.NET
        DEDUCTION = IncomeType.DEDUCTION
        EXTRA = IncomeType.EXTRA

    name = models.CharField(max_length=25)
    scope = models.PositiveIntegerField(choices=Scope.choices)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    calc_mode = models.IntegerField(
    choices=CalcMode.choices, default=CalcMode.Percentage
    )
    apply_to = models.PositiveIntegerField(choices=AllowIncomeType.choices)
    percental = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    fixed_amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=create_money("0.00", "USD"),
        default_currency="USD",
        blank=True,
        null=True,
    )
    rules = models.JSONField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def compute_benefits(self, scope, id=None, value=None):
        def check_param(param):
            if not param is None:
                return
            raise ValueError(f"{param} is required")

        def calc(self):
            if self.CalcMode.Fixed:
                return self.fixed_amount
            if self.CalcMode.Percentage:
                if value is None:
                    raise ValueError("value required")
                return value * self.percental
        if scope == self.Scope.Employee:
            EmployeeBenefit.objects.filter(employee=id)
        elif scope == self.Scope.Position:
            EmployeePositionBenefit.objects.filter(employee=id)
        elif scope == self.Scope.Job:
            JobBenefit.objects.filter(job=id)

        elif scope == self.Scope.Grade:
            pass

        else:
            raise ValueError("unknown type")

        return 0.00

    def __str__(self):
        return self.name


class Employee(models.Model):
    class Gender(models.TextChoices):
        MALE = "M"
        FEMALE = "F"

    class MaritalStatus(models.TextChoices):
        DIVORCED = "DI"
        MARRIED = "MA"
        SEPARATED = "SE"
        SINGLE = "SI"
        WIDOWED = "WI"

    class EmploymentType(models.IntegerChoices):
        FULL_TIME = 0
        PART_TIME = 1
        CONTRACTOR = 2

    employee_benefit = models.ManyToManyField("Benefit", through="EmployeeBenefit")
    employee_position = models.ManyToManyField("Job", through="EmployeePosition")
    employee_id_number = models.CharField(max_length=25, unique=True)
    first_name = models.CharField(max_length=25)
    middle_name = models.CharField(max_length=25, blank=True, null=True)
    last_name = models.CharField(max_length=25)
    maiden_name = models.CharField(max_length=25, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=Gender.choices)
    marital_status = models.CharField(max_length=2, choices=MaritalStatus.choices)
    date_of_birth = models.DateField()
    nationality = models.ForeignKey(Country, on_delete=models.CASCADE)

    hire_date = models.DateField()
    employment_type = models.IntegerField(choices=EmploymentType.choices)
    tin = models.CharField(max_length=25, null=True, blank=True, unique=True)
    social_security_number = models.CharField(
        max_length=25, null=True, blank=True, unique=True
    )
    employment_end_date = models.DateField()

    personal_email = models.EmailField(unique=True, blank=True, null=True)
    work_email = models.EmailField(unique=True, blank=True, null=True)
    personal_phone = models.CharField(max_length=25, unique=True, blank=True, null=True)
    work_phone = models.CharField(max_length=25, unique=True, blank=True, null=True)

    active = models.BooleanField(default=False)

    @property
    def age(self) -> int:
        return ((timezone.now().date() - self.date_of_birth) / 365).days

    @property
    def total_owed(self) -> Money:
        return self.deductable_set.all()

    def clean(self):
        errors = {}

        if self.maiden_name:
            if self.gender == self.Gender.MALE:
                errors["maiden_name"] = _("Not allow for male must be a Female")
            if self.marital_status == self.MaritalStatus.SINGLE:
                errors["maiden_name"] = _("field not allow for single individual")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}"

    class Meta:
        ordering = ["employee_id_number"]


class EmployeeBenefit(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE)


class Address(models.Model):
    # Disable all the unused-variable violations in this function
    # pylint: disable=unused-variable
    class Label(models.TextChoices):
        WORK_PRIMARY = "WP"
        HOME_PRIMARY = "HP"
        WORK_SECONDARY = "WS"
        HOME_SECONDARY = "HS"
        OTHER = "O"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    address_one = models.CharField(max_length=25)
    address_two = models.CharField(max_length=25)
    city = models.CharField(max_length=25)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    label = models.CharField(max_length=2, choices=Label.choices)


class Department(models.Model):
    department = models.CharField(max_length=100)
    head_of_department = models.ManyToManyField(Employee, through="DepartmentHead")

    def __str__(self):
        return self.department


class DepartmentHead(models.Model):
    # Disable all the unused-variable violations in this function
    # pylint: disable=unused-variable
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.department.department} {self.employee}"


class Job(models.Model):
    class WageType(models.IntegerChoices):
        SALARIED = 0
        PER_RATE = 1

    currency = CurrencyField(choices=CURRENCY_CHOICES)
    position = models.CharField(max_length=100)
    job_benefit = models.ManyToManyField("Benefit", through="JobBenefit")
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    wage_type = models.PositiveIntegerField(choices=WageType.choices)
    pay_period = models.PositiveIntegerField(choices=PayPeriod.choices)
    base_salary_wage = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        default_currency="USD",
    )
    grade = models.CharField(max_length=2)
    job_description = models.TextField()

    def __str__(self):
        return f"{self.position} {self.department.department} GRADE:{self.grade}"


class JobBenefit(models.Model):
    Job = models.ForeignKey(Job, on_delete=models.CASCADE)
    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE)


class EmployeePosition(models.Model):
    class State(models.IntegerChoices):
        CURRENT = 0
        PROMOTED = 1
        TRANSFER = 2
        RESIGNED = 3
        TERMINATED = 4

    employee_position_benefit = models.ManyToManyField(
        "Benefit", "EmployeePositionBenefit"
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    position = models.ForeignKey(Job, on_delete=models.CASCADE)
    grade = models.CharField(max_length=2, blank=True, null=True)
    pay_period = models.PositiveIntegerField(
        choices=PayPeriod.choices, default=PayPeriod.MONTHLY
    )
    negotiated_salary_wage = MoneyField(
        max_digits=14, decimal_places=2, blank=True, null=True
    )
    state = models.IntegerField(choices=State.choices, default=State.CURRENT)
    position_date = models.DateField(default=timezone.now)

    @property
    def other_earnings(self):
        # Disable all the no-member violations in this function
        # pylint: disable=no-member
        total = self.earning_set.aggregate(total=Sum("amount"))["total"] or 0.00
        return Money(total, self.negotiated_salary_wage.currency)

    @property
    def total_earnings(self):
        total = self.other_earnings + self.negotiated_salary_wage
        return Income(PayPeriod(self.pay_period), total)

    class Meta:
        get_latest_by = ["position_date"]

    def clean(self):
        # Disable all the no-member violations in this function
        # pylint: disable=no-member
        errors = {}
        minimum_wage = Money(1.00, self.negotiated_salary_wage_currency)

        if self.negotiated_salary_wage:
            if self.negotiated_salary_wage < minimum_wage:
                errors["negotiated_salary_wage"] = _(
                    f"salary cannot less than MinimumWage {minimum_wage}"
                )

        if errors:
            raise ValidationError(errors)

    @classmethod
    def pre_create(cls, sender, instance, *args, **kwargs):
        if not instance.negotiated_salary_wage:
            instance.negotiated_salary_wage = instance.position.base_salary_wage
            instance.negotiated_salary_wage_currency = (
                instance.position.base_salary_wage_currency
            )
            instance.pay_period = instance.position.pay_period

        if not instance.grade:
            instance.grade = instance.position.grade

    def __str__(self):
        return f"{self.employee} {self.position}"


class EmployeePositionBenefit(models.Model):
    employee = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)
    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE)


class Earning(models.Model):
    # Disable all the unused-variable violations in this function
    # pylint: disable=unused-variable
    employee_position = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE)
    earning = models.CharField(max_length=25)
    amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", "USD"),
        default_currency="USD",
    )

    def __str__(self):
        return f"{self.earning}, {self.amount}"


class EmployeeAccount(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    bank = models.ForeignKey(Account, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=25)
    active = models.BooleanField(default=True)


pre_save.connect(EmployeePosition.pre_create, sender=EmployeePosition)
