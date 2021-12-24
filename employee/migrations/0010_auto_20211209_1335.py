# Generated by Django 3.2 on 2021-12-09 13:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0009_auto_20211209_1223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employeeaccount',
            name='current',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='employeeposition',
            name='employee',
            field=models.ForeignKey(limit_choices_to={'active': True}, on_delete=django.db.models.deletion.CASCADE, to='employee.employee'),
        ),
    ]
