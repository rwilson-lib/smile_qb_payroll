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
from django.urls import include

from . import views
from rest_framework import routers


router = routers.DefaultRouter()

router.register("account", views.AccountView)
router.register("transaction", views.TransactionView)
router.register("general_ledger", views.GeneralLedgerView)
router.register("line_item", views.LineItemView)

# Disable all the unused-variable violations in this function
# pylint: disable=unused-variable
urlpatterns = [
    # path('', views.home, name='country_home'),
    path("/", include(router.urls))
]
