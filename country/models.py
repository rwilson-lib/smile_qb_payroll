from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=25)
    iso3 = models.CharField(max_length=3)
    iso2 = models.CharField(max_length=2)
    phone_code = models.CharField(max_length=25)
    capital = models.CharField(max_length=50)
    native = models.CharField(max_length=50, null=True, blank=True)
    currency = models.CharField(max_length=3)
    currency_symbol = models.CharField(max_length=25)
    region = models.CharField(max_length=25)
    subregion = models.CharField(max_length=25)
    latitude = models.CharField(max_length=25)
    longitude = models.CharField(max_length=25)
    emoji = models.CharField(max_length=100)
    emojiU = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class State(models.Model):
    # Disable all the unused-variable violations in this function
    # pylint: disable=unused-variable
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    state_code = models.CharField(max_length=3)

    def __str__(self):
        return self.name


class TimeZone(models.Model):
    # Disable all the unused-variable violations in this function
    # pylint: disable=unused-variable
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    zoneName = models.CharField(max_length=50)
    gmtOffset = models.IntegerField()
    gmtOffsetName = models.CharField(max_length=25)
    abbreviation = models.CharField(max_length=3)
    tzName = models.CharField(max_length=25)

    def __str__(self):
        return self.zoneName
