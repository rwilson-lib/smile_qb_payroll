# Generated by Django 3.2 on 2021-12-26 11:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0014_payroll_transaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payroll',
            name='transaction',
        ),
    ]
