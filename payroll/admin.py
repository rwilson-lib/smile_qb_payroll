from django.contrib import admin

from .models import (
    Deductable,
    DeductionPlan,
    PayrollDeduction,
    Payroll,
    PayrollEmployee,
    PayrollExtra,
    ExchangeRate,
    EmployeeTaxContribution,
    TaxContributionCollector,
)


admin.site.register(Deductable)
admin.site.register(DeductionPlan)
admin.site.register(PayrollDeduction)
admin.site.register(Payroll)
admin.site.register(PayrollEmployee)
admin.site.register(PayrollExtra)
admin.site.register(ExchangeRate)
admin.site.register(EmployeeTaxContribution)
admin.site.register(TaxContributionCollector)
