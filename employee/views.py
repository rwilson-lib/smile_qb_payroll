import json

from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.forms import inlineformset_factory, formset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render

from .forms import EmployeeForm, EmployeePositionForm, EarningForm, AddressForm, JobForm
from .models import Address, Employee, EmployeePosition, Earning, Job


# Disable all the unused-variable violations in this function
# pylint: disable=unused-variable
def home(request):
    template = "employee_list.html"
    # employees = Employee.objects.all()
    items = []

    for employee in Employee.objects.iterator(500):
        item = employee.__dict__
        item["age"] = employee.age
        item["gender"] = employee.get_gender_display()
        item["marital_status"] = employee.get_marital_status_display()
        item["nationality"] = employee.nationality.name
        item["employment_type"] = employee.get_employment_type_display()
        del item["nationality_id"]
        del item["_state"]
        items.append(item)

    json.dumps(items, cls=DjangoJSONEncoder)

    context = {
        "employees": items,
    }

    return render(request, template, context)


def employee_get(request, pk):
    template = "employee_detail.html"
    employee = get_object_or_404(Employee, pk=pk)

    context = {
        "employee": employee,
    }
    return render(request, template, context)


def employee_create(request):

    template = "employee_create.html"
    context = {}

    AddressFormSet = formset_factory(AddressForm, extra=1)
    EarningFormSet = formset_factory(EarningForm, extra=4)

    employee_form = EmployeeForm(instance=Employee())
    employee_position_form = EmployeePositionForm(instance=EmployeePosition())
    job_form = JobForm(instance=Job())

    address_formset = AddressFormSet()
    employee_position_earns_formset = EarningFormSet()

    context["employee_form"] = employee_form
    context["employee_position_form"] = employee_position_form
    context["job_form"] = job_form
    context["address_formset"] = address_formset
    context["employee_position_earns_formset"] = employee_position_earns_formset

    if request.method == "POST":
        employee_form = EmployeeForm(request.POST, instance=Employee())
        address_formset = AddressFormSet(request.POST)
        employee_position_form = EmployeePositionForm(
            request.POST, instance=EmployeePosition()
        )

        # Disable all the C0330 violations in this function
        # pylint: disable=C0330
        if (
            employee_form.is_valid()
            and employee_position_form.is_valid()
            and address_formset.is_valid()
        ):
            new_employee = employee_form.save()
            new_position = employee_position_form.save(commit=False)
            new_addresses = address_formset.save(commit=False)
            for new_address in new_addresses:
                new_address.employee = new_employee
                new_address.save()
            new_position.employee = new_employee
            new_position.save()
            return HttpResponseRedirect("/employee")

        context["employee_form"] = employee_form
        context["address_formset"] = address_formset
        context["employee_position_form"] = employee_position_form
    return render(request, template, context)


def employee_edit(request, pk):
    # Disable all the unused-variable violations in this function
    # pylint: disable=unused-variable
    template = "employee_update.html"
    context = {}

    AddressFormSet = inlineformset_factory(
        Employee, Address, extra=1, exclude=["id", "employee"]
    )

    employee = get_object_or_404(Employee, pk=pk)
    employee_current_position = employee.employeeposition_set.last()
    employee_addresses = employee.address_set.all()

    employee_form = EmployeeForm(request.POST or None, instance=employee)
    address_formset = AddressFormSet(request.POST or None, instance=employee)
    employee_position_form = EmployeePositionForm(
        request.POST or None, instance=employee_current_position
    )

    context["employee_form"] = employee_form
    context["address_formset"] = address_formset
    context["employee_position_form"] = employee_position_form
    context["employee_id"] = employee.id

    if request.method == "POST":
        # Disable all the C0330 violations in this function
        # pylint: disable=C0330
        if (
            employee_form.is_valid()
            and employee_position_form.is_valid()
            and address_formset.is_valid()
        ):
            update_employee = employee_form.save()
            update_employee_position = employee_position_form.save(commit=False)
            update_employee_position.employee = update_employee

            update_employee_position.save()
            address_formset.save()
        else:
            context["employee_form"] = employee_form
            context["address_formset"] = address_formset
            context["employee_position_form"] = employee_position_form

    else:
        context["employee_form"] = employee_form
        context["address_formset"] = AddressFormSet(instance=employee)
        context["employee_position_form"] = employee_position_form

    return render(request, template, context)


def employee_search(request):
    data = {}
    pk = 1
    if request.method == "GET":
        employees = Employee.objects.filter(pk=pk)
        data = serializers.serialize("json", employees, fields=("id", "name"))

    return JsonResponse(data, safe=False)
