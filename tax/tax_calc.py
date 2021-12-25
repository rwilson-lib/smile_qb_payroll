import math
from collections import namedtuple

from djmoney.money import Money

from payroll.income import Income, PayPeriod
from tax.models import TaxContribution


def apply_tax_rules(income, excess_over, percent, extra):
    t = Money(((income.amount - excess_over) * percent) + extra, income.currency)
    return Money(0.00, income.currency) if t == income else t

def calculate_tax(tax_contrib, income):

    if tax_contrib.calc_mode == TaxContribution.CalcMode.Fixed:
        return Income(
            PayPeriod(tax_contrib.tax_period),
            Money(tax_contrib.value, tax_contrib.currency)
        )

    elif tax_contrib.calc_mode == TaxContribution.CalcMode.Percentage:
        return Income(
            PayPeriod(tax_contrib.tax_period),
            income.money * tax_contrib.value
        )

    elif tax_contrib.calc_mode == TaxContribution.CalcMode.RuleBase:
        tax = determine_tax_value(tax_contrib, income) 
        return tax.tax

def determine_tax_value(tax_contrib, income):
    if tax_contrib.currency != income.money.currency.code:
        raise TypeError(f"income currency must be of the type {tax_contrib.currency} but got {income.money.currency}")

    tax = namedtuple("Tax", ["revision", "match_clause", "tax"])

    currency = tax_contrib.currency
    tax_period = PayPeriod(tax_contrib.tax_period)

    income = income.convert_to(tax_period)

    for clause in tax_contrib.clause_set.all():
        if clause.end is None:
            if math.floor(income.money.amount) > clause.start:
                t = apply_tax_rules(
                    income.money, clause.excess_over, clause.percent, clause.addition
                )
                i = Income(tax_period, t)
                return tax(tax_contrib.revision.version, clause.line_num, i)
        else:
            if math.floor(income.money.amount) in range(
                int(clause.start), int(clause.end)
            ):
                t = apply_tax_rules(
                    income.money,
                    clause.excess_over,
                    clause.percent,
                    clause.addition,
                )
                i = Income(tax_period, t)
                return tax(tax_contrib.revision.version, clause.line_num, i)

    raise ValueError(f"tax revision ID:{tax_contrib.id} have no matching tax clause")
