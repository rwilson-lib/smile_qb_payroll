from django.contrib import admin

from .models import (
    Address,
    Benefit,
    Department,
    DepartmentHead,
    Earning,
    Employee,
    EmployeeBenefit,
    EmployeePosition,
    EmployeePositionBenefit,
    EmployeeAccount,
    Job,
    JobBenefit,
)

admin.site.register(Address)
admin.site.register(Benefit)
admin.site.register(Department)
admin.site.register(DepartmentHead)
admin.site.register(Earning)
admin.site.register(Employee)
admin.site.register(EmployeeBenefit)
admin.site.register(EmployeePosition)
admin.site.register(EmployeePositionBenefit)
admin.site.register(EmployeeAccount)
admin.site.register(Job)
admin.site.register(JobBenefit)
