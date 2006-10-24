import datetime, random, sha
import os

from django import forms 
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.core.mail import send_mail
from django.utils.datastructures import MultiValueDict
from django.db.models import Q

from hackzor import settings
from hackzor.server.models import Question, Attempt, UserProfile, Language, ToBeEvaluated
from hackzor.server.forms import RegistrationForm, LoginForm, SubmitSolution, ForgotPassword, ChangePassword
from hackzor.evaluator.main import Client

@login_required
def viewProblem (request, id):
    path_to_media_prefix = os.path.join(os.getcwd(), settings.MEDIA_ROOT)
    object = Question.objects.get(id=id)
    inp = open(os.path.join(path_to_media_prefix , object.test_input)).read().split('\n')
    out = open(os.path.join(path_to_media_prefix , object.test_output)).read().split('\n')
    testCase = [x for x in zip(inp, out)]
    return render_to_response('view_problem.html',
                              {'object':object, 'testCase':testCase,
                               'user': request.user})

def register(request):
    # TODO: Make this a decorator after cleaning up the template
    if request.user.is_authenticated():
         # They already have an account; don't let them register again
         return render_to_response('simple_message.html', {'message' :"You are already registered."} )

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
            # TODO: Store the message in a seperate file or DB
            email_subject = 'Your new Hackzor account confirmation'
            email_body = 'Hello, %s, and thanks for signing up for an %s account!\n\nTo activate your account, click this link within 48 hours:\n\n \
                    http://%s/accounts/confirm/%s' % (request.user.username, settings.CONTEST_NAME, settings.CONTEST_URL, new_profile.activation_key)
            
            send_mail(email_subject,
                      email_body,
                      settings.CONTEST_EMAIL,
                      [new_user.email])
            
            return render_to_response('simple_message.html', 
            {'message' : 'A mail has been sent to %s. Follow the link in the mail to activate your account' %(new_user.email) })
        else:
            print 'Errors'
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('register.html', {'form': form})


def confirm (request, activation_key):
    if request.user.is_authenticated():
        return render_to_response('simple_message.html', {'message' : 'You are already registerd!'})
    user_profile = get_object_or_404(UserProfile,
                                     activation_key=activation_key)
    #TODO : Prevent attacks by resetting the key when activated
    if user_profile.key_expires < datetime.datetime.today():
        u = user_profile.user
        user_profile.delete();
        u.delete()
        return render_to_response('simple_message.html', {'message' : 'Your activation key has expired. Please register again'})
    user_account = user_profile.user
    user_account.is_active = True
    user_account.save()
    return render_to_response('simple_message.html', {'message' : 'Thou arth registered. Begin thy quest for glory!'})


def logout_view (request):
    logout(request)
    return HttpResponseRedirect('/opc/')

def forgot_password(request):
    ''' Sends mail to user on reset passwords '''

    manipulator = ForgotPassword()

    if request.POST:
        import md5
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            # Build the activation key, for the reset password
            salt = sha.new(str(random.random())).hexdigest()[:5]
            new_password = md5.md5 (str(random.random())).hexdigest()[:8]
            username = new_data['username']

            # Create and save their profile
            u = User.objects.get(username=username)
            u.set_password(new_password)
            u.save()

            # Send an email with the password
            email_subject = 'Your new Hackzor account password reset'
            email_body = 'Hello, %s. A password reset was requested at %s. Your new_password is %s.' % (request.user.username, 
                    settings.CONTEST_URL, new_password)
            
            send_mail(email_subject,
                      email_body,
                      settings.CONTEST_EMAIL,
                      [u.email])
            
            return render_to_response('simple_message.html', 
            {'message' : 'A mail has been sent to %s with the new password' %(u.email) })
        else:
            print 'Errors'
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('reset_password.html', {'form': form})

@login_required
def change_password(request):
    ''' Change Pasword View. Need I say more? '''
    manipulator = ChangePassword()

    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            user = request.user
            if user.check_password(new_data['old_password']):
                user.set_password(new_data['password1'])
                user.save()
                return render_to_response('simple_message.html', {'message' : 'Password Changed!'})
            else:
                    errors['old_password'].append('Old Password is incorrect')
        else: 
            print errors
    else:
        errors = new_data = {}

    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('change_password.html', {'form': form, 'user':request.user})


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

            content  = request.FILES['file_path']['content']
            user     = get_object_or_404(UserProfile, user=request.user)
            print 'user'
            question = get_object_or_404(Question, id=new_data['question_id'])
            print 'question'
            language = get_object_or_404(Language, id=new_data['language_id'])
            print 'language'
            attempt  = Attempt (user = user, question=question, code=content, language=language, file_name=request.FILES['file_path']['filename'])
            attempt.save()
            pending  = ToBeEvaluated (attempt=attempt)
            pending.save()
            Client().start()
            return render_to_response('simple_message.html', {'message' : 'Code Submitted!'})
        else:
            print errors
    else:
        errors = new_data = {}
        if problem_no:
            new_data = MultiValueDict({'question_id':[problem_no]})

    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('submit_code.html', {'form': form, 'user':request.user})

def search_questions (request):
    """ Search Engine for the Questions"""
    result = []
    beenthere=False
    if request.GET:
        beenthere=True
        data = request.GET.copy()
        keywords = data.getlist ('search_text')[0]
        if keywords:
            keywords = keywords.split()
            result = Question.objects.filter( Q(text__icontains=keywords[0]) | Q(name__icontains=keywords[0]) )
            for k in keywords[1:]:
                result = result.filter( Q(text__icontains=k) | Q(name__icontains=k) )
                if result.count() == 0:
                    break

    return render_to_response('search_result.html', {'beenthere':beenthere, 'result':result})
