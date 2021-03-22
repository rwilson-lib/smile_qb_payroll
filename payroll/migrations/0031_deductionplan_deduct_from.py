# Generated by Django 3.1.4 on 2021-03-22 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0030_auto_20210321_1435'),
    ]

    operations = [
        migrations.AddField(
            model_name='deductionplan',
            name='deduct_from',
            field=models.IntegerField(choices=[(0, 'Salary'), (1, 'Net'), (2, 'Gross'), (3, 'Extra')], default=1),
        ),
    ]
