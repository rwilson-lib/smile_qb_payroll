from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.forms import modelformset_factory
from django.forms import inlineformset_factory

from .forms import EmployeeForm
from .forms import EmployeePositionForm

from .models import Employee
from .models import EmployeePosition
from .models import Address

import json


def home(request):
    template = 'employee_list.html'
    # employees = Employee.objects.all()
    items = []

    for employee in Employee.objects.iterator(500):
        item = employee.__dict__
        item['age'] = employee.age
        item['gender'] = employee.get_gender_display()
        item['marital_status'] = employee.get_marital_status_display()
        item['nationality'] = employee.nationality.name
        item['employment_type'] = employee.get_employment_type_display()
        del item['nationality_id']
        del item['_state']
        items.append(item)

    json.dumps(items, cls=DjangoJSONEncoder)

    context = {
        'employees': items,
    }

    return render(request,template, context)


def employee_get(request, id):
    template = 'employee_detail.html'
    employee = get_object_or_404(Employee, pk=id)

    context = {
        'employee': employee,
    }
    return render(request,template, context)


def employee_create(request):

    template = 'employee_create.html'
    context = {}

    AddressFormSet = modelformset_factory(
        Address, exclude=['id', 'employee'], extra = 1
    )

    employee_form = EmployeeForm(instance=Employee())
    address_formset = AddressFormSet(queryset=Address.objects.none())
    employee_position_form = EmployeePositionForm(instance=EmployeePosition())

    context['employee_form']   = employee_form
    context['address_formset'] = address_formset
    context['employee_position_form'] = employee_position_form

    if request.method == "POST":
        employee_form     = EmployeeForm(request.POST, instance=Employee())
        address_formset   = AddressFormSet(request.POST)
        employee_position_form = EmployeePositionForm(request.POST, instance=EmployeePosition())

        if employee_form.is_valid() and\
           employee_position_form.is_valid() and\
           address_formset.is_valid():
            new_employee = employee_form.save()
            new_position = employee_position_form.save(commit=False)
            new_addresses  = address_formset.save(commit=False)
            for new_address in new_addresses:
                new_address.employee  = new_employee
                new_address.save()
            new_position.employee = new_employee
            new_position.save()
            return HttpResponseRedirect('/employee')

        else:
            context['employee_form']   = employee_form
            context['address_formset'] = address_formset
            context['employee_position_form'] = employee_position_form
    return render(request, template, context)


def employee_edit(request, id):
    template = 'employee_update.html'
    context = {}

    AddressFormSet = inlineformset_factory(Employee, Address, extra=1, exclude=['id', 'employee'])

    employee = get_object_or_404(Employee, pk=id)
    employee_current_position = employee.employeeposition_set.last()
    employee_addresses = employee.address_set.all()

    employee_form = EmployeeForm(request.POST or None, instance=employee)
    address_formset = AddressFormSet(request.POST or None, instance=employee)
    employee_position_form = EmployeePositionForm(request.POST or None, instance=employee_current_position)

    context['employee_form']   = employee_form
    context['address_formset'] = address_formset
    context['employee_position_form'] = employee_position_form
    context['employee_id'] = employee.id

    if request.method == "POST":
        if employee_form.is_valid() and\
           employee_position_form.is_valid() and\
           address_formset.is_valid():
            update_employee = employee_form.save()
            update_employee_position = employee_position_form.save(commit=False)
            update_employee_position.employee = update_employee

            update_employee_position.save()
            address_formset.save()
        else:
            context['employee_form']   = employee_form
            context['address_formset'] = address_formset
            context['employee_position_form'] = employee_position_form

    else:
        context['employee_form']   = employee_form
        context['address_formset'] = AddressFormSet(instance=employee)
        context['employee_position_form'] = employee_position_form


    return render(request, template, context)


def employee_search(request):
    data = {}
    id = 1
    if request.method == 'GET':
        employees = Employee.objects.filter(pk=id)
        data = serializers.serialize("json", employees, fields=("id", "name"))

    for query in request.GET:
       print(query, request.GET[query])

    return JsonResponse(data, safe=False)
