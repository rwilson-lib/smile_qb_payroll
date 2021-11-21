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

admin.site.register(Credit)
admin.site.register(CreditPaymentPlan)
admin.site.register(EmployeeTaxContribution)
admin.site.register(ExchangeRate)
admin.site.register(Payroll)
admin.site.register(PayrollDeduction)
admin.site.register(PayrollEmployee)
admin.site.register(Addition)
admin.site.register(TaxContributionCollector)
admin.site.register(TimeSheet)
