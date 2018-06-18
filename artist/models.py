# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

def artist_directory_path(instance, filename):
    return 'artists/artist_{0}/{1}'.format(instance.id, filename)

class Artist(models.Model):
	name = models.CharField(max_length=100)
	email = models.EmailField()
	age = models.CharField(max_length=10)
	phone_no = models.IntegerField(default=0)
	city = models.CharField(max_length=60)
	state = models.CharField(max_length=30)
	email_token = models.CharField(max_length=32, null=True, blank=True)
	email_verified = models.BooleanField(default=False)
	genre = models.CharField(max_length=100)
	user = models.OneToOneField(User, null=True)

class ArtistProfile(models.Model):
	rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
	facebook_url = models.URLField(null=True)
	linkedin_url = models.URLField(null=True)
	artist = models.OneToOneField(Artist, null=True)
	budget_from = models.IntegerField(default=0)
	budget_to = models.IntegerField(default=0)

class ArtistImage(models.Model):
	artist = models.OneToOneField(Artist, null=True)
	image = models.ImageField(null=True,upload_to=artist_directory_path)
	caption = models.CharField(max_length=50)