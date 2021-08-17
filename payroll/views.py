import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Q, Sum
from django.forms import formset_factory
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from utils import create_money

from .forms import (
    AddEmployeeForm,
    PayrollForm,
    ExchangeRateForm,
    CreditForm,
    CreditPaymentPlanForm,
    EmployeeTaxContributionForm,
)
from .models import EmployeePosition, Payroll, PayrollEmployee, ExchangeRate


# Disable all the unused-variable violations in this function
# pylint: disable=unused-variable
def home(request):
    payroll = Payroll.objects.all().annotate(total_amount=Count("payrollemployee"))
    template = "payroll_list.html"
    context = {
        "payroll_items": payroll,
    }

    return render(request, template, context)


def get_query_ajax(request):
    employee_ids = request.POST.get("content")
    results = []
    if employee_ids:
        employee_ids = employee_ids[1:-1].split(",")
        for emp_id in employee_ids:
            emp_id = int(emp_id)
            employee_positions = (
                EmployeePosition.objects.filter(
                    employee=emp_id, state=EmployeePosition.State.CURRENT
                )
                .select_related("employee", "position")
                .latest()
            )
            results.append(
                {
                    "employee_id_number": employee_positions.employee.employee_id_number,
                    "social_security_number": employee_positions.employee.social_security_number,
                    "tin": employee_positions.employee.tin,
                    "first_name": employee_positions.employee.first_name,
                    "middle_name": employee_positions.employee.middle_name,
                    "last_name": employee_positions.employee.last_name,
                    "gender": employee_positions.employee.gender,
                    "job_title": employee_positions.position.position,
                    "department": employee_positions.position.department.department,
                    "salary": employee_positions.negotiated_salary.amount,
                    "currency": employee_positions.negotiated_salary.currency,
                    "pay_period": employee_positions.pay_period,
                }
            )
    if results:
        serialized_q = json.dumps(list(results), cls=DjangoJSONEncoder)
        return JsonResponse(serialized_q, safe=False)


def payroll_create(request):
    template = "payroll_create.html"

    PayrollEmployeeFormSet = formset_factory(AddEmployeeForm, min_num=29)
    exchangerate_form = ExchangeRateForm()
    payroll_form = PayrollForm()
    formset = PayrollEmployeeFormSet()

    context = {
        "payroll_form": payroll_form,
        "payroll_item_formset": formset,
        "exchangerate_form": exchangerate_form,
    }

    ajax_employee_id = request.GET.get("emp_id")
    ajax_employee_fn = request.GET.get("fn")
    ajax_employee_mn = request.GET.get("mn")
    ajax_employee_ln = request.GET.get("ln")

    results = None

    if ajax_employee_id:
        results = (
            EmployeePosition.objects.filter(
                Q(employee__employee_id_number__icontains=ajax_employee_id)
                & Q(state=EmployeePosition.State.CURRENT)
            )
            .select_related("employee", "position")
            .values(
                "id",
                "employee__employee_id_number",
                "employee__social_security_number",
                "employee__tin",
                "employee__first_name",
                "employee__middle_name",
                "employee__last_name",
                "employee__gender",
                "position__position",
                "position__department__department",
                "negotiated_salary",
                "negotiated_salary_currency",
                "pay_period",
            )
        )
    elif ajax_employee_fn:
        results = EmployeePosition.objects.filter(
            Q(employee__first_name__icontains=ajax_employee_fn)
            & Q(state=EmployeePosition.State.CURRENT)
        ).select_related("employee", "position")
    elif ajax_employee_mn:
        results = EmployeePosition.objects.filter(
            Q(employee__middle_name__icontains=ajax_employee_mn)
            & Q(state=EmployeePosition.State.CURRENT)
        ).select_related("employee", "position")
    elif ajax_employee_ln:
        results = EmployeePosition.objects.filter(
            Q(employee__last_name__icontains=ajax_employee_ln)
            & Q(state=EmployeePosition.State.CURRENT)
        ).select_related("employee", "position")

    if results:
        serialized_q = json.dumps(list(results), cls=DjangoJSONEncoder)
        return JsonResponse(serialized_q, safe=False)

    if request.method == "POST":
        payroll_form = PayrollForm(request.POST)
        formsets = PayrollEmployeeFormSet(request.POST)
        if payroll_form.is_valid() and formsets.is_valid():
            new_payroll = payroll_form.save()
            counter = 0
            # check with all browsers having issues with safari
            for data in formsets:
                if data.cleaned_data.get("employee_id"):
                    counter += 1
                    payroll_employee_id = data.cleaned_data.get("employee_id")
                    new_payroll_employee = PayrollEmployee(
                        employee_id=payroll_employee_id, payroll_id=new_payroll.id
                    )
                    new_payroll_employee.save()

            if counter == 0:
                new_payroll.delete()
            else:
                return HttpResponseRedirect(f"/payroll/{new_payroll.id}")

        else:
            print(formsets.errors)

    return render(request, template, context)


def payroll_get(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    payroll_employee_items = payroll.payrollemployee_set.all()

    template = "payroll_detail.html"
    context = {"payroll_employee_items": payroll_employee_items, "payroll": payroll}

    return render(request, template, context)


def payroll_employee_get(request, pk, line_pk):

    payroll = get_object_or_404(Payroll, pk=pk)
    payroll_employee = payroll.payrollemployee_set.get(pk=line_pk)
    extra_incomes = payroll_employee.addition_set.all()
    deductions = payroll_employee.payrolldeduction_set.all()
    earnings = payroll_employee.employee.earning_set.all()

    extra_sum = create_money(
        payroll_employee.addition_set.aggregate(sum=Sum("amount"))["sum"] or 0.00,
        payroll_employee.earnings.currency,
    )
    deduction_sum = create_money(
        payroll_employee.payrolldeduction_set.aggregate(sum=Sum("amount"))["sum"]
        or 0.00,
        payroll_employee.earnings.currency,
    )

    template = "payroll_employee_detail.html"
    context = {
        "payroll_employee": payroll_employee,
        "earnings": earnings,
        "extra_incomes": extra_incomes,
        "total_extra_income": extra_sum,
        "deductions": deductions,
        "total_deduction": deduction_sum,
    }

    return render(request, template, context)


def deduction_create(request):
    template = "deduction_create.html"

    CreditPaymentPlanFormSet = formset_factory(
        CreditPaymentPlanForm, min_num=1, extra=0, max_num=10
    )

    deductable_form = CreditForm()
    deduction_plan_formset = CreditPaymentPlanFormSet()

    context = {
        "deductable_form": deductable_form,
        "deduction_plan_formset": deduction_plan_formset,
    }
    return render(request, template, context)


def payroll_deduction(request, pk):

    employee = PayrollEmployee.objects.get(pk=pk)
    employee_deductions = employee.payrolldeduction_set.all()

    template = "deductions.html"
    context = {"employee_deductions": employee_deductions}
    return render(request, template, context)


def payroll_extra(request, pk):

    employee = PayrollEmployee.objects.get(pk=pk)
    employee_extras = employee.addition_set.all()

    template = "extras.html"
    context = {"employee_extras": employee_extras}
    return render(request, template, context)
