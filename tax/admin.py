from django.contrib import admin

from .models import Revision
from .models import Clause
from .models import Tax


admin.site.register(Revision)
admin.site.register(Clause)
admin.site.register(Tax)
