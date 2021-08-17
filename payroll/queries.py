from django.db.models import Count, Sum
import payroll.models


def get_tax_contributions_group_by_taxes(by_payroll=None):
    results = (
        payroll.models.TaxContributionCollector.objects.filter(
            payroll_employee__payroll=by_payroll
        )
        .values("contribution__tax", "contribution__account")
        .annotate(count=Count("contribution__tax"), total=Sum("amount"))
    )
    return results


def get_addition_group_by_addition(by_payroll=None):
    results = (
        payroll.models.Addition.objects.filter(payroll_employee__payroll=by_payroll)
        .values("item__name", "item__account")
        .annotate(count=Count("item"), total=Sum("amount"))
    )
    return results


def get_deductions_group_by_credit(by_payroll=None):
    results = (
        payroll.models.PayrollDeduction.objects.filter(
            payroll_employee__payroll=by_payroll
        )
        .values("payment_plan__credit__item", "payment_plan__credit__account")
        .annotate(count=Count("payment_plan__credit__account"), total=Sum("amount"))
    )
    return results
