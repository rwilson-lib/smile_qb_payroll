from django.contrib import admin

from .models import EmployeePosition
from .models import Job
from .models import Department
from .models import DepartmentHead
from .models import Address
from .models import Employee
from .models import Earning

admin.site.register(Address)
admin.site.register(Earning)
admin.site.register(Employee)
admin.site.register(Job)
admin.site.register(EmployeePosition)
admin.site.register(Department)
admin.site.register(DepartmentHead)
