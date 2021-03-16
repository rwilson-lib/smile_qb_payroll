
from django.forms import ModelForm

from .models import Employee
from .models import Address
from .models import EmployeePosition


class EmployeeForm(ModelForm):
    class Meta:
        model = Employee
        exclude = ['id']


class AddressForm(ModelForm):
    # def __init__(self, country, *args,**kwargs):
        # super (AddressForm, self ).__init__(*args,**kwargs) # populates the post
        # self.fields['state'].queryset = Country.objects.get(pk=country).state_set.all()

    class Meta:
        model = Address
        exclude = ['id', 'employee']


class EmployeePositionForm(ModelForm):
    class Meta:
        model = EmployeePosition
        exclude = ['id', 'employee', 'state']
