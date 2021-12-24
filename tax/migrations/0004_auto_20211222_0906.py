# Generated by Django 3.2 on 2021-12-22 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tax', '0003_taxcontribution_currency'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxcontribution',
            name='fixed_amount',
        ),
        migrations.RemoveField(
            model_name='taxcontribution',
            name='fixed_amount_currency',
        ),
        migrations.RemoveField(
            model_name='taxcontribution',
            name='percental',
        ),
        migrations.AddField(
            model_name='taxcontribution',
            name='value',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=14),
            preserve_default=False,
        ),
    ]
