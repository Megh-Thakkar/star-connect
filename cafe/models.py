# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from artist.models import *
from django.contrib.auth.models import User
import uuid

def cafe_directory_path(instance, filename):
    return 'cafes/cafe_{0}/{1}'.format(instance.id, filename)

class Cafe(models.Model):
	name = models.CharField(max_length=100)
	email = models.EmailField()
	phone_no = models.IntegerField(default=0)
	city = models.CharField(max_length=60)
	state = models.CharField(max_length=30)
	email_token = models.CharField(max_length=32, null=True, blank=True)
	email_verified = models.BooleanField(default=False)
	user = models.OneToOneField(User, null=True)

class CafeProfile(models.Model):
	rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
	gigs_per_week = models.IntegerField(default=0)
	facebook_url = models.URLField(null=True)
	linkedin_url = models.URLField(null=True)
	cafe = models.OneToOneField(Cafe, null=True)

class CafeImage(models.Model):
	cafe = models.OneToOneField(Cafe, null=True)
	image = models.ImageField(null=True,upload_to=cafe_directory_path)
	caption = models.CharField(max_length=50)

class Opportunity(models.Model):
	is_open = models.BooleanField(default=False)
	genre = models.CharField(max_length=50, null=True)
	date = models.DateTimeField(null=True)
	uid = models.UUIDField(null=True)
	cafe = models.ForeignKey(Cafe)
	artists = models.ManyToManyField('artist.Artist', through='QuoteArtistToCafe')
	artist = models.ForeignKey('artist.Artist', related_name='individual_opportunity')
	amount = models.IntegerField(default=0, null=True)
	accepted = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		if not self.id:
			uid = uuid.uuid4()
			while 1:	
				try:
					quote = Opportunity.objects.get(uid=uid)
					continue
				except:
					break
			self.uid = uid
		return super(Opportunity, self).save(*args, **kwargs)

class QuoteCafeToArtist(models.Model):
	q_to = models.ForeignKey('artist.Artist', null=True)
	q_amount = models.IntegerField(default=0)
	q_time = models.DateTimeField(auto_now=True)
	accepted = models.BooleanField(default=False)
	opportunity = models.ForeignKey(Opportunity, null=True)

class QuoteArtistToCafe(models.Model):
	q_from = models.ForeignKey('artist.Artist', null=True)
	q_to = models.ForeignKey(Opportunity, null=True)
	q_amount = models.IntegerField(default=0)
	q_time = models.DateTimeField(auto_now=True)
	accepted = models.BooleanField(default=False)
	parent = models.ForeignKey('QuoteCafeToArtist', null=True, related_name='parent_for_artist')