# Generated by Django 3.2 on 2021-12-09 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0007_auto_20211209_1335'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payrollemployee',
            name='take_home',
        ),
        migrations.RemoveField(
            model_name='payrollemployee',
            name='take_home_currency',
        ),
        migrations.AlterField(
            model_name='payrollemployee',
            name='flag',
            field=models.IntegerField(choices=[(0, 'Ok'), (1, 'Overpaid'), (2, 'Rejected'), (3, 'Reviewed')], default=0),
        ),
    ]
