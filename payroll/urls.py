"""smile_qb_payroll URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from . import views

# Disable all the unused-variable violations in this function
# pylint: disable=unused-variable
urlpatterns = [
    path("", views.home, name="payroll_list"),
    path("create/", views.payroll_create, name="payroll_create"),
    path("<int:id>/", views.payroll_get, name="payroll_detail"),
    path(
        "<int:id>/employee/<int:line_id>",
        views.payroll_employee_get,
        name="payroll_employee_detail",
    ),
    path("deduction/create", views.deduction_create, name="deduction_create"),
    path("<int:id>/deduction", views.payroll_deduction, name="payroll_deduction"),
    path("<int:id>/extras", views.payroll_extra, name="payroll_extra"),
]
