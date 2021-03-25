from collections import OrderedDict
from functools import reduce

from django.db import models
from djmoney.money import Money


class PayPeriod(models.IntegerChoices):
    ANNUALLY = 6
    QUARTERLY = 5
    MONTHLY = 4
    BI_WEEKLY = 3
    WEEKLY = 2
    DAILY = 1
    HOURLY = 0


class IncomeType(models.IntegerChoices):
    SALARY = 0
    GROSS = 1
    NET = 2
    TAKE_HOME = 3
    EXTRA = 4
    DEDUCTION = 5
    OTHER = 6


TABLE = (
    OrderedDict([("HOURLY", 24), ("DAILY", 1)]),
    OrderedDict([("DAILY", 7), ("WEEKLY", 1)]),
    OrderedDict([("WEEKLY", 4), ("MONTHLY", 1)]),
    OrderedDict([("MONTHLY", 12), ("ANNUALLY", 1)]),
)


def convert(from_unit, value, to_unit):
    if from_unit == to_unit:
        return value

    if from_unit == PayPeriod.BI_WEEKLY or from_unit == PayPeriod.QUARTERLY:
        value *= 2
        if to_unit == PayPeriod.QUARTERLY:
            return (
                convertion_factor(PayPeriod.MONTHLY, PayPeriod.ANNUALLY) * value
            ) * 0.5
        elif to_unit == PayPeriod.BI_WEEKLY:
            return (
                convertion_factor(PayPeriod.ANNUALLY, PayPeriod.MONTHLY) * value
            ) * 0.5
        else:
            if from_unit == PayPeriod.BI_WEEKLY:
                return convertion_factor(PayPeriod.MONTHLY, to_unit) * value
            if from_unit == PayPeriod.QUARTERLY:
                return convertion_factor(PayPeriod.ANNUALLY, to_unit) * value

    if to_unit == PayPeriod.BI_WEEKLY or to_unit == PayPeriod.QUARTERLY:
        if from_unit == PayPeriod.QUARTERLY:
            return (
                convertion_factor(PayPeriod.MONTHLY, PayPeriod.ANNUALLY) * value
            ) * 0.5
        elif from_unit == PayPeriod.BI_WEEKLY:
            return (
                convertion_factor(PayPeriod.ANNUALLY, PayPeriod.MONTHLY) * value
            ) * 0.5
        else:
            if to_unit == PayPeriod.BI_WEEKLY:
                return (convertion_factor(from_unit, PayPeriod.MONTHLY) * value) * 0.5
            if to_unit == PayPeriod.QUARTERLY:
                return (convertion_factor(from_unit, PayPeriod.ANNUALLY) * value) * 0.5

    return convertion_factor(from_unit, to_unit) * value


def convertion_factor(from_unit, to_unit):
    if to_unit.value > from_unit.value:
        include = False
        value = 1
        for item in TABLE:
            if list(item.keys())[0].upper() == from_unit.label.upper() or include:
                include = True
                value *= reduce(lambda x, y: x * y, item.values())
            if list(item.keys())[1].upper() == to_unit.label.upper():
                break
        return value
    elif from_unit.value > to_unit.value:
        include = False
        value = None
        l = len(TABLE)
        for index in range(l):
            access_index = l - (index + 1)
            if (
                list(TABLE[access_index].keys())[1].upper() == from_unit.label.upper()
                or include
            ):
                include = True
                item = list(TABLE[access_index].values())
                if value is None:
                    value = item[1] / item[0]
                else:
                    value = value / item[0]
            if list(TABLE[access_index].keys())[0].upper() == to_unit.label.upper():
                break
        return value
    return 1


class Income:
    def __init__(self, pay_period, money):
        if not isinstance(pay_period, PayPeriod):
            raise TypeError(f"pay_period must be of type {PayPeriod}")
        if not isinstance(money, Money):
            raise TypeError(f"money must be of type {Money}")
        self.pay_period = pay_period
        self.money = money

    def convert_to(self, to_unit):
        value = convert(self.pay_period, self.money, to_unit)
        return Income(to_unit, value)

    def __add__(self, value):
        if isinstance(value, Income):
            if self.pay_period != value.pay_period:
                raise TypeError(
                    "unsupported operations cannot add two different periods"
                )
            return Income(self.pay_period, self.money + value.money)
        return Income(self.pay_period, self.money + value)

    def __sub__(self, value):
        if isinstance(value, Income):
            if self.pay_period != value.pay_period:
                raise TypeError(
                    "unsupported operations cannot subtract two different periods"
                )
            return Income(self.pay_period, self.money - value.money)
        return Income(self.pay_period, self.money - value)

    def __mul__(self, value):
        if isinstance(value, Income):
            raise TypeError("unsupported operations cannot multiple two Income")
        return Income(self.pay_period, self.money * value)

    def __eq__(self, value):
        v = self.convert_to(value.pay_period)
        if v.money == value.money:
            return True
        return False

    def __gt__(self, value):
        v = self.convert_to(value.pay_period)
        if v.money > value.money:
            return True
        return False

    def __ge__(self, value):
        v = self.convert_to(value.pay_period)
        if v.money >= value.money:
            return True
        return False

    def __lt__(self, value):
        v = self.convert_to(value.pay_period)
        if v.money < value.money:
            return True
        return False

    def __le__(self, value):
        v = self.convert_to(value.pay_period)
        if v.money <= value.money:
            return True
        return False

    def __str__(self):
        return f"{self.money} {self.pay_period.label.upper()}"

    def __repr__(self):
        return f"< Income: {self.money} {self.pay_period.label.upper()} >"
