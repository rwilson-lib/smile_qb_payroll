from django import forms
from django.forms import ModelForm

from .models import Payroll


# Disable all the unused-variable violations in this function
# pylint: disable=unused-variable
class PayrollForm(ModelForm):
    class Meta:
        model = Payroll
        exclude = ["id", "status"]


class AddEmployeeForm(forms.Form):
    employee_id = forms.CharField(label="", widget=forms.HiddenInput(), required=False)
    employee_id_number = forms.CharField(label="", required=False)
    social_security_number = forms.CharField(label="", required=False)
    tin = forms.CharField(label="", required=False)
    first_name = forms.CharField(label="", required=False)
    middle_name = forms.CharField(label="", required=False)
    last_name = forms.CharField(label="", required=False)
    gender = forms.CharField(label="", required=False)
    job_title = forms.CharField(label="", required=False)
    department = forms.CharField(label="", required=False)
    salary = forms.CharField(label="", required=False)
    currency = forms.CharField(label="", required=False)
    pay_period = forms.CharField(label="", required=False)

    employee_id_number.widget.attrs["class"] = "employee-id-number"
    social_security_number.widget.attrs["class"] = "employee-social_security_number"
    tin.widget.attrs["class"] = "employee-tin"
    first_name.widget.attrs["class"] = "employee-first-name"
    middle_name.widget.attrs["class"] = "employee-middle-name"
    last_name.widget.attrs["class"] = "employee-last-name"

    gender.widget.attrs["readonly"] = "readonly"
    salary.widget.attrs["readonly"] = "readonly"
    currency.widget.attrs["readonly"] = "readonly"
    pay_period.widget.attrs["readonly"] = "readonly"
