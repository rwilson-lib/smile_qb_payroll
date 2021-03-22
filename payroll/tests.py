from django.test import TestCase
from payroll.income import PayPeriod
from payroll.income import convert


class AnnuallyConvertionTestCase(TestCase):
    CONVERT_TO = PayPeriod.ANNUALLY
    VALUE = 12000

    def test_annually_annually(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.ANNUALLY)
        self.assertEqual(value, 12000)

    def test_annually_quartely(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.QUARTERLY)
        self.assertEqual(value, 6000)

    def test_annually_monthly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.MONTHLY)
        self.assertEqual(value, 1000)

    def test_annually_bi_weekly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.BI_WEEKLY)
        self.assertEqual(value, 500)

    def test_annually_weekly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.WEEKLY)
        self.assertEqual(value, 250)

    def test_annually_daily(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.DAILY)
        self.assertEqual(round(value), 36)

    def test_annually_hourly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.HOURLY)
        self.assertEqual(round(value), 1)


class MonthlyConvertionTestCase(TestCase):
    CONVERT_TO = PayPeriod.MONTHLY
    VALUE = 1000

    def test_monthly_monthly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.ANNUALLY)
        self.assertEqual(value, 12000)

    def test_monthly_quartely(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.QUARTERLY)
        self.assertEqual(value, 6000)

    def test_monthly_monthly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.MONTHLY)
        self.assertEqual(value, 1000)

    def test_monthly_weekly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.WEEKLY)
        self.assertEqual(value, 250)

    def test_monthly_bi_weekly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.BI_WEEKLY)
        self.assertEqual(value, 500)

    def test_monthly_daily(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.DAILY)
        self.assertEqual(round(value), 36)

    def test_monthly_hourly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.HOURLY)
        self.assertEqual(round(value), 1)


class WeeklyConvertionTestCase(TestCase):
    CONVERT_TO = PayPeriod.WEEKLY
    VALUE = 250

    def test_weekly_weekly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.ANNUALLY)
        self.assertEqual(value, 12000)

    def test_weekly_quartely(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.QUARTERLY)
        self.assertEqual(value, 6000)

    def test_weekly_weekly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.MONTHLY)
        self.assertEqual(value, 1000)

    def test_weekly_weekly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.WEEKLY)
        self.assertEqual(value, 250)

    def test_weekly_bi_weekly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.BI_WEEKLY)
        self.assertEqual(value, 500)

    def test_weekly_daily(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.DAILY)
        self.assertEqual(round(value), 36)

    def test_weekly_hourly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.HOURLY)
        self.assertEqual(round(value), 1)


class DailyConvertionTestCase(TestCase):
    CONVERT_TO = PayPeriod.DAILY
    VALUE = 35.714285714285715

    def test_daily_daily(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.ANNUALLY)
        self.assertEqual(value, 12000)

    def test_daily_quartely(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.QUARTERLY)
        self.assertEqual(value, 6000)

    def test_daily_daily(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.MONTHLY)
        self.assertEqual(value, 1000)

    def test_daily_daily(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.WEEKLY)
        self.assertEqual(value, 250)

    def test_daily_bi_daily(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.BI_WEEKLY)
        self.assertEqual(value, 500)

    def test_daily_daily(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.DAILY)
        self.assertEqual(round(value), 36)

    def test_daily_hourly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.HOURLY)
        self.assertEqual(round(value), 1)


class HourlyConvertionTestCase(TestCase):
    CONVERT_TO = PayPeriod.HOURLY
    VALUE = 1.488095238095238

    def test_hourly_annually(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.ANNUALLY)
        self.assertEqual(round(value), 12000)

    def test_hourly_quartely(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.QUARTERLY)
        self.assertEqual(round(value), 6000)

    def test_hourly_monthly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.MONTHLY)
        self.assertEqual(round(value), 1000)

    def test_hourly_weekly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.WEEKLY)
        self.assertEqual(round(value), 250)

    def test_hourly_bi_weekly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.BI_WEEKLY)
        self.assertEqual(round(value), 500)

    def test_hourly_daily(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.DAILY)
        self.assertEqual(round(value), 36)

    def test_hourly_hourly(self):
        value = convert(self.CONVERT_TO, self.VALUE, PayPeriod.HOURLY)
        self.assertEqual(value, 1.488095238095238)
