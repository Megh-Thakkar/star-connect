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
from datetime import datetime
import pytz

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
				if not user.cafe.email_verified:
					context = {'error_heading' : "Email not verified", 'message' :  'It seems you haven\'t verified your email yet. Please verify it as soon as possible to proceed.', 'url':request.build_absolute_uri(reverse('cafe:home'))}
					return render(request, 'cafe/message.html', context)
				login(request, user)
				return redirect('cafe:index')
			else:
				context = {'error_heading' : "Account Inactive", 'message' :  'Your account is currently INACTIVE.', 'url':request.build_absolute_uri(reverse('cafe:home'))}
				return render(request, 'cafe/message.html', context)
		else:
			messages.warning(request,'Invalid login credentials')
			return redirect(request.META.get('HTTP_REFERER'))
	else:
		return render(request, 'cafe/login.html')

def index(request):
	if request.user.is_authenticated():
		user = request.user
		cafe = Cafe.objects.get(user=user)
		return render(request, 'cafe/home.html', {'cafe':cafe, })

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
			Cafe.objects.get(email=data['email'])
			return JsonResponse({'status':0, 'message':'Email already registered.'})
		except:
			pass
		else:
			cafe = Cafe()
			cafe.name = str(data['name'])
			cafe.city = str(data['city'])
			cafe.state = str(data['state'])
			cafe.email = str(data['email'])
			cafe.phone_no = int(data['phone'])
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
			'''%(name, str(request.build_absolute_uri(reverse("cafe:index"))) + 'email_confirm/' + generate_email_token(cafe) + '/')

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
				cafe.delete()
				return JsonResponse({'status':0, 'message':'Error sending email. Please try again.'})
			message = "A confirmation link has been sent to %s. Kindly click on it to verify your email address." %(send_to)
			return JsonResponse({'status':1, 'message':message})
				
	else:
		return render(request, 'cafe/signup.html',)	

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
	return render(request, 'cafe/message.html', context)

@login_required
def update_profile(request):
	user = request.user
	cafe = user.cafe
	try:
		cafe_profile = CafeProfile.objects.get(cafe=cafe)
	except:
		cafe_profile = CafeProfile.objects.create(cafe=cafe)
	if request.method == 'POST':
		data = request.POST
		try:
			facebook_url = data['facebook_url']
			cafe_profile.facebook_url = facebook_url
		except:
			pass
		try:
			linkedin_url = data['linkedin_url']
			cafe_profile.linkedin_url = linkedin_url
		except:
			pass
		try:
			gigs_per_week = int(data['gigs_per_week'])
			cafe_profile.gigs_per_week = gigs_per_week
		except:
			pass
		from django.core.files import File
		try:
			up_img = request.FILES['image']
			img_file = resize_uploaded_image(up_img, 240, 240)
			new_img = File(img_file)
			caption = data['caption']
			cafe_image = CafeImage.objects.create(cafe=cafe, caption=caption)
			cafe_image.image.save('image' + str(cafe_image.id), new_img)
		except:
		 	pass
		cafe_profile.save()

	cafe_images = cafe.cafeimage_set.all()
	return render(request, 'cafe/update_profile.html', {'cafe':cafe, 'cafe_images':cafe_images})

@login_required
def create_open_oppurtunity(request):
	user = request.user
	cafe = user.cafe
	if request.method == 'POST':
		data = request.POST
		str_date = data['date']
		req_date = datetime.strptime(str_date, "%Y-%m-%dT%H:%M:%S.%fZ")
		aware_date = pytz.utc.localize(req_date)
		amount = int(data['amount'])
		genre = data['genre']
		opportunity = Opportunity.objects.create(cafe=cafe, is_open=True, genre=genre, date=aware_date, amount=amount)
	oppurtunities = cafe.quotecafetoartist_set.filter(accepted=False)
	return render(request, 'cafe/create_open_oppurtunity.html', {'oppurtunities':oppurtunities, 'cafe':cafe})

@login_required
def respond_to_quote(request, uid, artist_id):
	user = request.user
	cafe = user.cafe
	artist = get_object_or_404(Artist, id=artist_id)
	opportunity = Opportunity.objects.get(uid=uid)
	if opportunity.cafe is not cafe:
		return redirect('cafe:index')
	if request.method == 'POST':
		data = request.POST
		amount = int(data['amount'])
		new_quote_cafe_to_artist = QuoteCafeToArtist.objects.create(q_to=artist, q_amount=amount, opportunity=opportunity)
	oppurtunities = cafe.opportunity_set.filter(accepted=False)
	return render(request, 'cafe/create_open_oppurtunity.html', {'oppurtunities':oppurtunities, 'cafe':cafe})


############# Helper functions ##########

def generate_email_token(cafe):

	import uuid
	token = uuid.uuid4().hex
	registered_tokens = [profile.email_token for profile in Cafe.objects.all()]

	while token in registered_tokens:
		token = uuid.uuid4().hex

	cafe.email_token = token
	cafe.save()
	
	return token

def authenticate_email_token(token):

	try:
		cafe = Cafe.objects.get(email_token=token)
		cafe.email_verified = True
		user = cafe.user
		user.is_active = True
		user.save()
		cafe.save()
		return cafe

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