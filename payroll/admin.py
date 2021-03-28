from django.contrib import admin

from .models import (
    Deductable,
    DeductionPlan,
    EmployeeTaxContribution,
    ExchangeRate,
    Payroll,
    PayrollDeduction,
    PayrollEmployee,
    PayrollExtra,
    TaxContributionCollector,
)

admin.site.register(Deductable)
admin.site.register(DeductionPlan)
admin.site.register(EmployeeTaxContribution)
admin.site.register(ExchangeRate)
admin.site.register(Payroll)
admin.site.register(PayrollDeduction)
admin.site.register(PayrollEmployee)
admin.site.register(PayrollExtra)
admin.site.register(TaxContributionCollector)
