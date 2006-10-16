import datetime, random, sha
import os
from hackzor import settings
from django import forms 
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.mail import send_mail

from hackzor.server.models import Question, Attempt
from hackzor.server.forms import RegistrationForm, LoginForm, SubmitSolution
from hackzor.server.models import UserProfile

@login_required
def viewProblem (request, id):
    path_to_media_prefix = os.path.join(os.getcwd(), settings.MEDIA_ROOT)
    object = Question.objects.get(id=id)
    inp = open(os.path.join(path_to_media_prefix , object.test_input)).read().split('\n')
    out = open(os.path.join(path_to_media_prefix , object.test_output)).read().split('\n')
    testCase = [x for x in zip(inp, out)]
    print request.user.is_authenticated()
    return render_to_response('view_problem.html',
            {'object':object, 'testCase':testCase, 'user': request.user})

def register(request):
    #TODO: Make this a decorator after cleaning up the template
    if request.user.is_authenticated():
         # They already have an account; don't let them register again
         return render_to_response('register.html', {'has_account': True})

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


def logout_view (request):
    logout(request)
    return HttpResponseRedirect('/opc/')

@login_required
def submit_code (request, problem_no=None):
    """ Handles Submitting problem. Gets User identity from sessions. requires an authenticated user"""
    manipulator = SubmitSolution()

    if request.POST:
        new_data = request.POST.copy()
        new_data.update(request.FILES)
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            #FIXME: Stores only last submited Code for problem for each user
            new_file = open('submits/%s_%s' %(request.user.username, problem_no), 'w')
            new_file.write(request.FILES['file_path']['content'])

            # TODO: Catch For Objects that do not exist
            attempt = Attempt (user = UserProfile.objects.get(user=User.objects.get(username=request.user.username)), 
                                    question = Question(id=new_data['question_name']),
                                                            code_path = new_file.name)
            new_file.close()
            attempt.save()
            errors = {'file_path':['Code Uploaded']}
        else:
            print errors
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('submit_code.html', {'form': form, 'id_question_name' : problem_no, 'user':request.user})

