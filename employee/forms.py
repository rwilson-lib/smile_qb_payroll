from django.forms import ModelForm

from .models import Address, Earning, Employee, EmployeePosition, Job


class EarningForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EarningForm, self).__init__(*args, **kwargs)
        self.fields["earning"].widget.attrs["placeholder"] = self.fields[
            "earning"
        ].label

    class Meta:
        model = Earning
        exclude = ["id", "employee_position"]


class JobForm(ModelForm):
    class Meta:
        model = Job
        exclude = ["id"]


class EmployeeForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.fields["tin"].widget.attrs["placeholder"] = self.fields["tin"].label
        self.fields["employee_id_number"].widget.attrs["placeholder"] = self.fields[
            "employee_id_number"
        ].label
        self.fields["social_security_number"].widget.attrs["placeholder"] = self.fields[
            "social_security_number"
        ].label
        self.fields["first_name"].widget.attrs["placeholder"] = self.fields[
            "first_name"
        ].label
        self.fields["middle_name"].widget.attrs["placeholder"] = self.fields[
            "middle_name"
        ].label
        self.fields["last_name"].widget.attrs["placeholder"] = self.fields[
            "last_name"
        ].label
        self.fields["maiden_name"].widget.attrs["placeholder"] = self.fields[
            "maiden_name"
        ].label

        self.fields["personal_phone"].widget.attrs["placeholder"] = self.fields[
            "personal_phone"
        ].label

        self.fields["personal_email"].widget.attrs["placeholder"] = "email.example.com"

        self.fields["work_phone"].widget.attrs["placeholder"] = self.fields[
            "work_phone"
        ].label

        self.fields["work_email"].widget.attrs["placeholder"] = "email@company.com"

    class Meta:
        model = Employee
        exclude = ["id", "employee_position"]


class AddressForm(ModelForm):
    # def __init__(self, country, *args,**kwargs):
    # super (AddressForm, self ).__init__(*args,**kwargs) # populates the post
    # self.fields['state'].queryset = Country.objects.get(pk=country).state_set.all()

    class Meta:
        model = Address
        exclude = ["id", "employee"]


class EmployeePositionForm(ModelForm):
    class Meta:
        model = EmployeePosition
        exclude = ["id", "employee", "state"]
