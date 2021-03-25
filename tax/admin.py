from django.contrib import admin

from .models import Revision
from .models import Clause

from .models import TaxContribution


admin.site.register(Revision)
admin.site.register(Clause)
admin.site.register(TaxContribution)
