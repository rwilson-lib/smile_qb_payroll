from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.db.models.signals import pre_save
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from country.models import Country, State
from payroll.income import Income, PayPeriod
from utils import create_money


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

    hire_date = models.DateField()
    employee_id_number = models.CharField(max_length=25, unique=True)
    tin = models.CharField(max_length=25, null=True, blank=True, unique=True)
    social_security_number = models.CharField(
        max_length=25, null=True, blank=True, unique=True
    )
    employment_type = models.IntegerField(choices=EmploymentType.choices)
    employment_end_date = models.DateField()

    first_name = models.CharField(max_length=25)
    middle_name = models.CharField(max_length=25, blank=True, null=True)
    last_name = models.CharField(max_length=25)
    maiden_name = models.CharField(max_length=25, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=Gender.choices)
    marital_status = models.CharField(max_length=2, choices=MaritalStatus.choices)
    date_of_birth = models.DateField()

    personal_email = models.EmailField(unique=True, blank=True, null=True)
    work_email = models.EmailField(unique=True, blank=True, null=True)
    personal_phone = models.CharField(max_length=25, unique=True, blank=True, null=True)
    work_phone = models.CharField(max_length=25, unique=True, blank=True, null=True)

    nationality = models.ForeignKey(Country, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)

    @property
    def age(self) -> int:
        return ((timezone.now().date() - self.date_of_birth) / 365).days

    @property
    def total_owed(self):
        return self.deductable_set.all()

    def clean(self):
        errors = {}

        if self.maiden_name:
            if self.gender == self.Gender.MALE:
                errors["maiden_name"] = _(f"Not allow for male must be a Female")
            if self.marital_status == self.MaritalStatus.SINGLE:
                errors["maiden_name"] = _(f"field not allow for single individual")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}"

    class Meta:
        ordering = ["employee_id_number"]


class Address(models.Model):
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
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.department.department} {self.employee}"


class Job(models.Model):
    position = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    pay_period = models.PositiveIntegerField(choices=PayPeriod.choices)
    base_salary = MoneyField(
        max_digits=14,
        decimal_places=2,
        default=Money("0.00", "USD"),
        default_currency="USD",
    )
    grade = models.CharField(max_length=2)
    job_description = models.TextField()

    def __str__(self):
        return f"{self.position} {self.department.department} GRADE:{self.grade}"


class EmployeePosition(models.Model):
    class State(models.IntegerChoices):
        CURRENT = 0
        PROMOTED = 1
        TRANSFER = 2
        RESIGNED = 3
        TERMINATED = 4

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    position = models.ForeignKey(Job, on_delete=models.CASCADE)
    grade = models.CharField(max_length=2, blank=True, null=True)
    negotiated_salary = MoneyField(
        max_digits=14, decimal_places=2, blank=True, null=True
    )
    pay_period = models.PositiveIntegerField(
        choices=PayPeriod.choices, default=PayPeriod.MONTHLY
    )
    state = models.IntegerField(choices=State.choices, default=State.CURRENT)
    position_date = models.DateField(default=timezone.now)

    @property
    def other_earnings(self):
        sum = self.earning_set.aggregate(sum=Sum("amount"))["sum"] or 0.00
        return create_money(sum, self.negotiated_salary.currency)

    @property
    def total_earnings(self):
        total = self.other_earnings + self.negotiated_salary
        return Income(PayPeriod(self.pay_period), total)

    class Meta:
        get_latest_by = ["position_date"]

    def clean(self):
        errors = {}
        minimum_wage = create_money(1.00, self.negotiated_salary_currency)

        if self.negotiated_salary:
            if self.negotiated_salary < minimum_wage:
                errors["negotiated_salary"] = _(
                    f"salary cannot less than MinimumWage {minimum_wage}"
                )

        if errors:
            raise ValidationError(errors)

    @classmethod
    def pre_create(cls, sender, instance, *args, **kwargs):
        if not instance.negotiated_salary:
            instance.negotiated_salary = instance.position.base_salary
            instance.negotiated_salary_currency = instance.position.base_salary_currency
            instance.pay_period = instance.position.pay_period

        if not instance.grade:
            instance.grade = instance.position.grade

    def __str__(self):
        return f"{self.employee} {self.position}"


class Earning(models.Model):
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


pre_save.connect(EmployeePosition.pre_create, sender=EmployeePosition)
