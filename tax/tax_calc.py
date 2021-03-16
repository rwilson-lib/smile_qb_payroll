from collections import namedtuple
from djmoney.money import Money

from payroll.income import PayPeriod
import math


def calc_tax(income, excess_over, percent, extra):
    t = Money(((income.amount - excess_over) * percent) + extra, income.currency)
    return Money(0.00, income.currency) if t == income else t


def test_tax(income, revision, rate):
    tax = namedtuple("Tax", ["revision", "match_clause", "pay_period", "tax"])

    rev_currency = revision.currency
    income_currency = income.currency.code
    pay_period = revision.pay_period

    if rev_currency != income_currency:
        if not rate:
            raise TypeError(
                f"No ExchaneRate found Tax Currency:{rev_currency} Income Currency:{income_currency}"
            )
        income = rate.exchange(income)

    if pay_period == PayPeriod.ANNUALLY:
        income = income * 12

    elif pay_period == PayPeriod.QUARTER:
        income = income * 6

    elif pay_period == PayPeriod.MONTHLY:
        income = income * 1

    for clause in revision.clause_set.all():
        if clause.end is None:
            if math.floor(income.amount) > clause.start:
                t = calc_tax(
                    income, clause.excess_over, clause.percent, clause.addition
                )
                return tax(revision.version, clause.line_num, pay_period, t)
        else:
            if math.floor(income.amount) in range(int(clause.start), int(clause.end)):
                t = calc_tax(
                    income, clause.excess_over, clause.percent, clause.addition
                )
                return tax(revision.version, clause.line_num, pay_period, t)

    raise ValueError(f"tax revision ID:{revision.id} have no matching tax clause")
