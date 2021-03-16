from django.contrib import admin

# Register your models here.
from .models import Country
from .models import State
from .models import TimeZone


admin.site.register(Country)
admin.site.register(State)
admin.site.register(TimeZone)
