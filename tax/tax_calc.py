import math
from collections import namedtuple

from djmoney.money import Money

from payroll.income import Income, PayPeriod


def calc_tax(income, excess_over, percent, extra):
    t = Money(((income.amount - excess_over) * percent) + extra, income.currency)
    return Money(0.00, income.currency) if t == income else t


def test_tax(income, revision, rate):
    tax = namedtuple("Tax", ["revision", "match_clause", "pay_period", "tax"])

    rev_currency = revision.currency
    pay_period = PayPeriod(revision.pay_period)

    if revision.currency != income.money.currency.code:
        if rate is None:
            raise TypeError(
                f"No ExchaneRate found Tax Currency:{rev_currency} Income Currency:{income.money.currency}"
            )
        income.money = rate.exchange(income.money)

    income = income.convert_to(pay_period)
    for clause in revision.clause_set.all():
        if clause.end is None:
            if math.floor(income.money.amount) > clause.start:
                t = calc_tax(
                    income.money, clause.excess_over, clause.percent, clause.addition
                )
                i = Income(pay_period, t)
                return tax(revision.version, clause.line_num, pay_period, i)
        else:
            if math.floor(income.money.amount) in range(
                int(clause.start), int(clause.end)
            ):
                t = calc_tax(
                    income.money,
                    clause.excess_over,
                    clause.percent,
                    clause.addition,
                )
                i = Income(pay_period, t)
                return tax(revision.version, clause.line_num, pay_period, i)

    raise ValueError(f"tax revision ID:{revision.id} have no matching tax clause")
