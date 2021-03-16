# Generated by Django 3.1.4 on 2021-03-08 15:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0011_auto_20210308_1317'),
        ('payroll', '0023_auto_20210308_1425'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeContribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contribution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payroll.contribution')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employee.employeeposition')),
            ],
        ),
    ]
