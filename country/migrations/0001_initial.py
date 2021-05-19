# Generated by Django 3.2 on 2021-04-27 14:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('iso3', models.CharField(max_length=3)),
                ('iso2', models.CharField(max_length=2)),
                ('phone_code', models.CharField(max_length=25)),
                ('capital', models.CharField(max_length=50)),
                ('native', models.CharField(blank=True, max_length=50, null=True)),
                ('currency', models.CharField(max_length=3)),
                ('currency_symbol', models.CharField(max_length=25)),
                ('region', models.CharField(max_length=25)),
                ('subregion', models.CharField(max_length=25)),
                ('latitude', models.CharField(max_length=25)),
                ('longitude', models.CharField(max_length=25)),
                ('emoji', models.CharField(max_length=100)),
                ('emojiU', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='TimeZone',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zoneName', models.CharField(max_length=50)),
                ('gmtOffset', models.IntegerField()),
                ('gmtOffsetName', models.CharField(max_length=25)),
                ('abbreviation', models.CharField(max_length=3)),
                ('tzName', models.CharField(max_length=25)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='country.country')),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('state_code', models.CharField(max_length=3)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='country.country')),
            ],
        ),
    ]
