from django.contrib import admin

from .models import (
    Address,
    Department,
    DepartmentHead,
    Earning,
    Employee,
    EmployeePosition,
    Job,
)

admin.site.register(Address)
admin.site.register(Department)
admin.site.register(DepartmentHead)
admin.site.register(Earning)
admin.site.register(Employee)
admin.site.register(EmployeePosition)
admin.site.register(Job)
