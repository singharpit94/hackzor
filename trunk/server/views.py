import datetime, random, sha
from django import forms 
from django.shortcuts import render_to_response, get_object_or_404
from hackzor.server.models import Question
from django.core.mail import send_mail
from hackzor.server.forms import RegistrationForm, LoginForm
from hackzor.server.models import UserProfile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

def viewProblem (request, id):
	object = Question.objects.get(id=id)
	inp = open(object.testInput).read().split('\n')
	out = open(object.testOutput).read().split('\n')
	testCase = [x for x in zip(inp, out)]
	return render_to_response('view_problem.html',
                              {'object':object, 'testCase':testCase})

def register(request):
#     if request.user.is_authenticated():
#         # They already have an account; don't let them register again
#         return render_to_response('register.html', {'has_account': True})

    manipulator = RegistrationForm()
    
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            # Save the user
            manipulator.do_html2python(new_data)
            new_user = manipulator.save(new_data)
            # Build the activation key for their account
            salt = sha.new(str(random.random())).hexdigest()[:5]
            activation_key = sha.new(salt+new_user.username).hexdigest()
            key_expires = datetime.datetime.today() + datetime.timedelta(2)

            # Create and save their profile
            new_profile = UserProfile(user=new_user,
                                      activation_key=activation_key,
                                      key_expires=key_expires,
                                      )
            new_profile.save()

            # Send an email with the confirmation link
            email_subject = 'Your new Hackzor account confirmation'
            email_body = 'Hello, %s, and thanks for signing up for an Hackzor account!\n\nTo activate your account, click this link within 48 hours:\n\n http://localhost:8000/accounts/confirm/%s' % ('Hello', new_profile.activation_key)
            
            send_mail(email_subject,
                      email_body,
                      'hackzor@googlegroups.com',
                      [new_user.email])
            
            return render_to_response('register.html', {'created': True})
        else:
            print 'Errors'
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('register.html', {'form': form})


def confirm (request, activation_key):
#     if request.user.is_authenticated():
#         return render_to_response('confirm.html', {'has_account': True})
    user_profile = get_object_or_404(UserProfile,
                                     activation_key=activation_key)
    if user_profile.key_expires < datetime.datetime.today():
        return render_to_response('confirm.html', {'expired': True})
    user_account = user_profile.user
    user_account.is_active = True
    user_account.save()
    return render_to_response('confirm.html', {'success': True})


def login (request):
    manipulator = LoginForm()
    
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            user = authenticate(username=new_data['username'],
                                password=new_data['password'])
            if user is None:
                return render_to_response('login.html', {'login_fail':
                                                         True})
            else:
                return render_to_response('login.html', {'login_success':
                                                         True})
        else:
            print 'Errors'
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('login.html', {'form': form})




