from django.db import models


class PayPeriod(models.IntegerChoices):
    ANNUALLY = 6
    QUARTER = 5
    MONTHLY = 4
    BI_WEEKLY = 3
    WEEKLY = 2
    DAILY = 1
    HOURLY = 0
