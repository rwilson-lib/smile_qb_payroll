from decimal import Decimal
from functools import reduce

from djmoney.money import Money


def create_money(amount, currency):
    """create_money(amount, currency) -> Money"""
    return Money(Decimal(amount), currency)


def total_amount(amounts, init_value=None):
    """ add money """
    if init_value:
        return reduce(lambda a, b: a + b, amounts, init_value)
    return reduce(lambda a, b: a + b, amounts)
