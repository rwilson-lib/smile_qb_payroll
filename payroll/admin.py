from django.contrib import admin

from .models import Deductable
from .models import DeductionPlan
from .models import PayrollDeduction
from .models import Payroll
from .models import PayrollEmployee
from .models import PayrollExtra
from .models import ExchangeRate
from .models import Contribution
from .models import EmployeeContribution
from .models import EmployeeTax



admin.site.register(Contribution)
admin.site.register(Deductable)
admin.site.register(DeductionPlan)
admin.site.register(PayrollDeduction)
admin.site.register(Payroll)
admin.site.register(PayrollEmployee)
admin.site.register(PayrollExtra)
admin.site.register(ExchangeRate)
admin.site.register(EmployeeContribution)
admin.site.register(EmployeeTax)
