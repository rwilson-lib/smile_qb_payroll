from django.contrib import admin

from .models import (
    Credit,
    CreditPaymentPlan,
    EmployeeTaxContribution,
    ExchangeRate,
    Payroll,
    PayrollDeduction,
    PayrollEmployee,
    Addition,
    TaxContributionCollector,
    TimeSheet,
)

class PayrollEmployeeAdmin(admin.ModelAdmin):
    readonly_fields=(
        'earnings',
        'extra_income',
        'gross_income',
        'income_tax',
        'deductions',
        'net_income'
    )

class PayrollDeductionAdmin(admin.ModelAdmin):
    readonly_fields=(
        'payroll_employee',
        'payment_plan',
        'amount',
    )

class TaxContributionCollectorAdmin(admin.ModelAdmin):
    readonly_fields=(
        'contribution',
        'payroll_employee',
        'amount',
        'amount_currency'
    )
 
admin.site.register(Credit)
admin.site.register(CreditPaymentPlan)
admin.site.register(EmployeeTaxContribution)
admin.site.register(ExchangeRate)
admin.site.register(Payroll)
admin.site.register(PayrollDeduction, PayrollDeductionAdmin)
admin.site.register(PayrollEmployee, PayrollEmployeeAdmin)
admin.site.register(Addition)
admin.site.register(TaxContributionCollector, TaxContributionCollectorAdmin)
admin.site.register(TimeSheet)
