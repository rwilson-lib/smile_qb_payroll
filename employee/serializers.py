from rest_framework import serializers

from .models import (
    Benefit,
    Employee,
    EmployeeBenefit,
    Address,
    Department,
    DepartmentHead,
    Job,
    JobBenefit,
    EmployeePosition,
    EmployeePositionBenefit,
    Earning,
)


class EmployeeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Employee
        fields = [
            "url",
            "id",
            "employee_position",
            "employee_benefit",
            "employee_id_number",
            "first_name",
            "middle_name",
            "last_name",
            "maiden_name",
            "gender",
            "marital_status",
            "date_of_birth",
            "nationality",
            "hire_date",
            "employment_type",
            "tin",
            "social_security_number",
            "employment_end_date",
            "personal_email",
            "work_email",
            "personal_phone",
            "work_phone",
            "active",
        ]


class BenefitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Benefit
        fields = [
            "id",
            "url",
            "name",
            "scope",
            "account",
            "calc_mode",
            "apply_to",
            "percental",
            "fixed_amount",
            "rules",
            "active",
        ]


class EmployeeBenefitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EmployeeBenefit
        fields = ["id", "url", "employee", "benefit"]


class AddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "url",
            "employee",
            "address_one",
            "address_two",
            "city",
            "state",
            "country",
            "label",
        ]


class DepartmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "url", "head_of_department"]


class DepartmentHeadSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DepartmentHead
        fields = ["id", "url", "employee", "department"]


class JobSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Job
        fields = [
            "id",
            "url",
            "job_benefit",
            "currency",
            "position",
            "department",
            "wage_type",
            "pay_period",
            "base_salary_wage",
            "grade",
            "job_description",
        ]


class JobBenefitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = JobBenefit
        fields = ["id"]


class EmployeePositionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EmployeePosition
        fields = [
            "id",
            "url",
            "employee",
            "position",
            "employee_position_benefit",
            "grade",
            "pay_period",
            "negotiated_salary_wage",
            "negotiated_salary_wage_currency",
            "state",
            "position_date",
        ]


class EmployeePositionBenefitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EmployeePositionBenefit
        fields = ["id", "employee", "benefit"]


class EarningSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Earning
        fields = ["id"]
