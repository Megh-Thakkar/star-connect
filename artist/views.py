from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import JsonResponse
from models import *
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
import sendgrid
import os
from sendgrid.helpers.mail import *
from django.contrib.auth.decorators import login_required
from instamojo_wrapper import Instamojo
import re
from starconnect.keyconfig import *
from django.contrib.auth.models import User
import string
from random import sample, choice
from django.contrib import messages
chars = string.letters + string.digits
import requests

try:
	from starconnect.config import *
	api = Instamojo(api_key=INSTA_API_KEY, auth_token=AUTH_TOKEN)
except:
	api = Instamojo(api_key=INSTA_API_KEY, auth_token=AUTH_TOKEN, endpoint='https://test.instamojo.com/api/1.1/') #when in development

def home(request):
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				if not user.artist.email_verified:
					context = {'error_heading' : "Email not verified", 'message' :  'It seems you haven\'t verified your email yet. Please verify it as soon as possible to proceed.', 'url':request.build_absolute_uri(reverse('artist:home'))}
					return render(request, 'artist/message.html', context)
				login(request, user)
				return redirect('artist:index')
			else:
				context = {'error_heading' : "Account Inactive", 'message' :  'Your account is currently INACTIVE.', 'url':request.build_absolute_uri(reverse('artist:home'))}
				return render(request, 'artist/message.html', context)
		else:
			messages.warning(request,'Invalid login credentials')
			return redirect(request.META.get('HTTP_REFERER'))
	else:
		return render(request, 'artist/login.html')

def index(request):
	if request.user.is_authenticated():
		user = request.user
		artist = Artist.objects.get(user=user)
		return render(request, 'artist/home.html', {'artist':artist, })

	if request.method == 'POST':
		# data = request.POST
		# recaptcha_response = data['g-recaptcha-response']
		# data_1 = {
		# 	'secret' : recaptcha_key,
		# 	'response' : recaptcha_response
		# }
		# r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data_1)
		# result = r.json()
		# if not result['success']:
		# 	return JsonResponse({'status':0, 'message':'Invalid Recaptcha. Try Again'})
		email = data['email']
		if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email):
			return JsonResponse({'status':0, 'message':'Please enter a valid email address.'})
		try:
			Artist.objects.get(email=data['email'])
			return JsonResponse({'status':0, 'message':'Email already registered.'})
		except:
			pass
		else:
			artist = Artist()
			artist.name = str(data['name'])
			artist.city = str(data['city'])
			artist.state = str(data['state'])
			artist.email = str(data['email'])
			artist.phone_no = int(data['phone'])
			username = data['username']
			password = data['password']
			user = User.objects.create_user(username=username, password=password)
			user.is_active = False
			user.save()
			send_to = str(request.POST["email"])
			name = str(request.POST["name"])
			body = '''
Hello %s!

Thank you for registering!
<a href='%s'>Click Here</a> to verify your email.
</pre>
			'''%(name, str(request.build_absolute_uri(reverse("artist:index"))) + 'email_confirm/' + generate_email_token(artist) + '/')

			# email = EmailMultiAlternatives("Registration for BOSM '17", 'Click '+ str(request.build_absolute_uri(reverse("registrations:email_confirm", kwargs={'token':generate_email_token(GroupLeader.objects.get(email=send_to))})))  + '/' + ' to confirm.', 
			# 								'register@bits-bosm.org', [send_to.strip()]
			# 								)
			# email.attach_alternative(body, "text/html")
			sg = sendgrid.SendGridAPIClient(apikey=API_KEY)
			from_email = Email('register@starconnect.org.in')
			to_email = Email(send_to)
			subject = "Registration for StarConnect"
			content = Content('text/html', body)
			try:
				mail = Mail(from_email, subject, to_email, content)
				response = sg.client.mail.send.post(request_body=mail.get())
			except :
				artist.delete()
				return JsonResponse({'status':0, 'message':'Error sending email. Please try again.'})
			message = "A confirmation link has been sent to %s. Kindly click on it to verify your email address." %(send_to)
			return JsonResponse({'status':1, 'message':message})
				
	else:
		return render(request, 'artist/signup.html',)	

def email_confirm(request, token):
	member = authenticate_email_token(token)
	
	if member:
		context = {
			'error_heading': 'Email verified',
			'message': 'Your email has been verified. Please wait for further correspondence from the Department of PCr, BITS, Pilani',
			'url':'https://starconnect.org.in'
		}
	else:
		context = {
			'error_heading': "Invalid Token",
			'message': "Sorry! This is an invalid token. Email couldn't be verified. Please try again.",
			'url':'https://starconnect.org.in'
		}
	return render(request, 'artist/message.html', context)

@login_required
def update_profile(request):
	user = request.user
	artist = user.artist
	try:
		artist_profile = ArtistProfile.objects.get(artist=artist)
	except:
		artist_profile = ArtistProfile.objects.create(artist=artist)
	if request.method == 'POST':
		data = request.POST
		try:
			facebook_url = data['facebook_url']
			artist_profile.facebook_url = facebook_url
		except:
			pass
		try:
			linkedin_url = data['linkedin_url']
			artist_profile.linkedin_url = linkedin_url
		except:
			pass
		try:
			budget_from = int(data['budget_from'])
			artist_profile.budget_from = budget_from
			budget_to = int(data['budget_to'])
			artist_profile.budget_to = budget_to
		except:
			pass
		from django.core.files import File
		try:
			up_img = request.FILES['image']
			img_file = resize_uploaded_image(up_img, 240, 240)
			new_img = File(img_file)
			caption = data['caption']
			artist_image = ArtistImage.objects.create(artist=artist, caption=caption)
			artist_image.image.save('image' + str(artist_image.id), new_img)
		except:
		 	pass
		artist_profile.save()

	artist_images = artist.artistimage_set.all()
	return render(render, 'artist/update_profile.html', {'artist':artist, 'artist_images':artist_images})

############# Helper functions ##########

def generate_email_token(artist):

	import uuid
	token = uuid.uuid4().hex
	registered_tokens = [profile.email_token for profile in Artist.objects.all()]

	while token in registered_tokens:
		token = uuid.uuid4().hex

	artist.email_token = token
	artist.save()
	
	return token

def authenticate_email_token(token):

	try:
		artist = Artist.objects.get(email_token=token)
		artist.email_verified = True
		user = artist.user
		user.is_active = True
		user.save()
		artist.save()
		return artist

	except :
		return False

def resize_uploaded_image(buf, height, width):
    
	import StringIO
	from PIL import Image
	image = Image.open(buf)
	width = width
	height = height
	resizedImage = image.resize((width, height))

	# Turn back into file-like object
	resizedImageFile = StringIO.StringIO()
	resizedImage.save(resizedImageFile , 'JPEG', optimize = True)
	resizedImageFile.seek(0)    # So that the next read starts at the beginning

	return resizedImageFile


################################# End of helper functions ###############################