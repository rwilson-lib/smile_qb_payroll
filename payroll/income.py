from collections import OrderedDict
from functools import reduce

from django.db import models
from djmoney.money import Money
from enum import Enum
from copy import deepcopy


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


class Unit(Enum):
    HOUR = "HOURLY"
    DAY = "DAILY"
    WEEK = "WEEKLY"
    MONTH = "MONTHLY"
    YEAR = "ANNUALLY"


TABLE = (
    OrderedDict([(Unit.HOUR.value, 24), (Unit.DAY.value, 1)]),
    OrderedDict([(Unit.DAY.value, 7), (Unit.WEEK.value, 1)]),
    OrderedDict([(Unit.WEEK.value, 4), (Unit.MONTH.value, 1)]),
    OrderedDict([(Unit.MONTH.value, 12), (Unit.YEAR.value, 1)]),
)


def get_convertion_table(**kwargs):
    LOOKUP_TABLE_LIST = deepcopy(TABLE)

    def change_unit_value(unit, value):
        for item in LOOKUP_TABLE_LIST:
            if not type(unit) is Unit:
                raise TypeError("unit must be a Unit")

            if unit == Unit.HOUR:
                if not (value >= 1 and value <= 24):
                    raise ValueError("HOUR value must be between 1 and 24")
                if unit.value == list(item.keys())[0]:
                    item[unit.value] = value

            elif unit == Unit.DAY:
                if not (value >= 1 and value <= 7):
                    raise ValueError("DAY value must be between 1 and 7")
                if unit.value == list(item.keys())[0]:
                    item[unit.value] = value
            elif unit == Unit.WEEK:
                if not (value >= 1 and value <= 4):
                    raise ValueError("WEEK value must be between 1 and 4")
                if unit.value == list(item.keys())[0]:
                    item[unit.value] = value
            elif unit == Unit.MONTH:
                if not (value >= 1 and value <= 12):
                    raise ValueError("MONTH value must be between 1 and 12")
                if unit.value == list(item.keys())[0]:
                    item[unit.value] = value
            else:
                raise ValueError("unsupported unit value")

        return LOOKUP_TABLE_LIST

    for key, value in kwargs.items():
        change_unit_value(Unit(key), value)
    return LOOKUP_TABLE_LIST


def convert(from_unit, value, to_unit, **kwargs):

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

    return convertion_factor(from_unit, to_unit, **kwargs) * value


def convertion_factor(from_unit, to_unit, **kwargs):

    LOOKUP_TABLE_LIST = get_convertion_table(**kwargs)

    if to_unit.value > from_unit.value:
        include = False
        value = 1
        for item in LOOKUP_TABLE_LIST:
            if list(item.keys())[0].upper() == from_unit.label.upper() or include:
                include = True
                value *= reduce(lambda x, y: x * y, item.values())
            if list(item.keys())[1].upper() == to_unit.label.upper():
                break
        return value
    elif from_unit.value > to_unit.value:
        include = False
        value = None
        l = len(LOOKUP_TABLE_LIST)
        for index in range(l):
            access_index = l - (index + 1)
            if (
                list(LOOKUP_TABLE_LIST[access_index].keys())[1].upper()
                == from_unit.label.upper()
                or include
            ):
                include = True
                item = list(LOOKUP_TABLE_LIST[access_index].values())
                if value is None:
                    value = item[1] / item[0]
                else:
                    value = value / item[0]
            if (
                list(LOOKUP_TABLE_LIST[access_index].keys())[0].upper()
                == to_unit.label.upper()
            ):
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

    def convert_to(self, to_unit, **kwargs):
        value = convert(self.pay_period, self.money, to_unit, **kwargs)
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
