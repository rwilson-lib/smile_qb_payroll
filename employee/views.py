from rest_framework import viewsets

from .models import (
    Benefit,
    Employee,
    EmployeeBenefit,
    Address,
    Department,
    DepartmentHead,
    Job,
    JobBenefit,
    EmployeePosition,
    EmployeePositionBenefit,
    Earning,
)

from .serializers import (
    BenefitSerializer,
    EmployeeSerializer,
    EmployeeBenefitSerializer,
    AddressSerializer,
    DepartmentSerializer,
    DepartmentHeadSerializer,
    JobSerializer,
    JobBenefitSerializer,
    EmployeePositionSerializer,
    EmployeePositionBenefitSerializer,
    EarningSerializer,
)


class BenefitView(viewsets.ModelViewSet):
    queryset = Benefit.objects.all()
    serializer_class = BenefitSerializer


class EmployeeView(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


class EmployeeBenefitView(viewsets.ModelViewSet):
    queryset = EmployeeBenefit.objects.all()
    serializer_class = EmployeeBenefitSerializer


class AddressView(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer


class DepartmentView(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DepartmentHeadView(viewsets.ModelViewSet):
    queryset = DepartmentHead.objects.all()
    serializer_class = DepartmentHeadSerializer


class JobView(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer


class JobBenefitView(viewsets.ModelViewSet):
    queryset = JobBenefit.objects.all()
    serializer_class = JobBenefitSerializer


class EmployeePositionView(viewsets.ModelViewSet):
    queryset = EmployeePosition.objects.all()
    serializer_class = EmployeePositionSerializer


class EmployeePositionBenefitView(viewsets.ModelViewSet):
    queryset = EmployeePositionBenefit.objects.all()
    serializer_class = EmployeePositionBenefitSerializer


class EarningView(viewsets.ModelViewSet):
    queryset = Earning.objects.all()
    serializer_class = EarningSerializer
