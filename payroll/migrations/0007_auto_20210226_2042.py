# Generated by Django 3.1.4 on 2021-02-26 20:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0006_auto_20210226_2041'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payrollemployee',
            old_name='income_tax_income',
            new_name='income_tax',
        ),
        migrations.RenameField(
            model_name='payrollemployee',
            old_name='income_tax_income_currency',
            new_name='income_tax_currency',
        ),
        migrations.RenameField(
            model_name='payrollemployee',
            old_name='total_deductions',
            new_name='total_deduction',
        ),
        migrations.RenameField(
            model_name='payrollemployee',
            old_name='total_deductions_currency',
            new_name='total_deduction_currency',
        ),
    ]
