# Generated by Django 3.1.4 on 2021-03-15 07:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0013_auto_20210314_1842'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employeeposition',
            name='pay_period',
        ),
    ]
