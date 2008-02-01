import datetime, random, sha
import os, sys

from django import forms 
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.mail import send_mail
from django.utils.datastructures import MultiValueDict
from django.views.generic.list_detail import object_list
from django.db.models import Q
from django.template import RequestContext 

from hackzor import settings
from hackzor.server.models import *
from hackzor.server.forms import *
import hackzor.server.utils as utils

import datetime

#TODO: Fix Models to rank properly
#TODO: Make a decorator to change permissions for veiws based on Contest timings

#TODO: Not tested yet. Need to make changes
def get_contest_times(request):
    contest_done = False
    anytime_now = ''
    if settings.CONTEST_START_TIME > datetime.datetime.now():
        display_time = settings.CONTEST_START_TIME
        display_tense = 'start'
        if display_time-datetime.datetime.now() < datetime.timedelta(0,  60):
            anytime_now = '< 1 minute'
    elif settings.CONTEST_END_TIME > datetime.datetime.now():
        display_time = settings.CONTEST_END_TIME
        display_tense = 'end'
        if display_time-datetime.datetime.now() < datetime.timedelta(0,  60):
            anytime_now = '< 1 minute'
    else:
        display_time = ''
        display_tense = ''
        contest_done = True
    return {'CONTEST_START_TIME':settings.CONTEST_START_TIME, 'CONTEST_END_TIME':settings.CONTEST_END_TIME, 
            'DISPLAY_TIME':display_time, 'DISPLAY_TENSE':display_tense, 'CONTEST_DONE':contest_done, 
            'ANYTIME_NOW':anytime_now}

def view_last_n_submissions (request, n, sort_by=None, for_user=None):
    ''' View to list the last n submissions sorted by the 'sort by' field '''
    #TODO: Breaks if sort_by is intentionally passed None(which happens) 
    # remove default parameter value and check if sort_by has allowed values
    # A Better way would be to handle exceptions
    n = int(n)
    fields = tuple([field.name for field in Attempt._meta.fields])
    if (sort_by == None): sort_by='-time_of_submit'
    elif sort_by[0]=='-':
        if sort_by[1:] not in fields: raise Http404
    else:
        if sort_by not in fields: raise Http404

    if for_user==None:
        submissions = Attempt.objects.order_by(sort_by)
        for_user=''
    else:
        try:
            user = User.objects.get(username__iexact=for_user).userprofile
            submissions = Attempt.objects.filter(user__exact=user).order_by(sort_by)
        except User.DoesNotExist:
            submissions = Attempt.objects.order_by(sort_by)

    return object_list(request, 
                paginate_by=n, 
                template_name='view_submissions.html', 
                extra_context = {'n' : n, 'for_user':for_user},
                allow_empty=True,
                template_object_name = 'submissions',
                queryset = submissions)

def view_problem (request, id):
    ''' Simple view to display view a particular problem 
    id : the primary key(id) of the Problem requested '''
    object = get_object_or_404(Question, id=id)
    return render_to_response('view_problem.html',
                              {'object':object }, RequestContext(request))

def register(request):
    ''' creates an inactive account by using the manipulator for the non-existant user and sends a confirm link to the user'''
    if request.user.is_authenticated():
         # They already have an account; don't let them register again
         return render_to_response('simple_message.html',
                                   {'message' :'You are already registered.',}, RequestContext(request))

    manipulator = RegistrationForm()
    
    if request.POST:
        new_data = request.POST.copy()
        #TODO: Clean up the user objects (at some point of time) to  release accounts which were never activated
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
            # TODO: Store this message in a template
            email_subject = 'Your new Hackzor account confirmation'
            email_body = ('Hello, %s, and thanks for signing up for an %s ' %(request.user.username, settings.CONTEST_NAME) +
                          'account!\n\nTo activate your account, click this' +
                          'link within 48 hours:\n\n ' +
                          'http://%s/accounts/confirm/%s' %
                          ( settings.CONTEST_URL, new_profile.activation_key))
            
            send_mail(email_subject,
                      email_body,
                      settings.CONTEST_EMAIL,
                      [new_user.email])
            
            return render_to_response('simple_message.html', 
                                      {'message' : 'A mail has been sent to ' +
                                       '%s. Follow the link in the mail to ' %(new_user.email)+
                                       'activate your account',}, RequestContext(request))
                                       #'user' : request.user})
        else:
            print 'Errors'
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('register.html', 
            {'form': form}, RequestContext(request))
    #,'user':request.user})


# TODO: Untested/Unchecked Code. May meed rewrite
def activate_account(request):
    ''' creates an inactive account by using the manipulator for the non-existant user and sends a confirm link to the user'''
    if request.user.is_authenticated():
         # They already have an account; don't let them register again
         return render_to_response('simple_message.html',
                                   {'message' :'You are already logged in.',}, RequestContext(request))

    manipulator = ActivateAccount()
    
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            # Save the user
            user = manipulator.get_user(new_data)
            # Build the activation key for their account
            salt = sha.new(str(random.random())).hexdigest()[:5]
            activation_key = sha.new(salt+user.username).hexdigest()
            key_expires = datetime.datetime.today() + datetime.timedelta(2)
            userprofile = user.userprofile
            userprofile.activation_key = activation_key
            userprofile.key_expires = key_expires
            userprofile.save()

            # Send an email with the confirmation link
            # TODO: Store the message in a seperate file or DB
            email_subject = 'Your new %s account confirmation' %(settings.CONTEST_NAME)
            email_body = ('Hello %s,\n ' %(user.username ) +
                          'You have requested for an activation mail at %s. You can activate your account by following the ' %(settings.CONTEST_NAME)+
                          'link below within 48 hours.\n\n ' +
                          'http://%s/accounts/confirm/%s \n' %( settings.CONTEST_URL, user.userprofile.activation_key) +
                           '\n Best of luck for %s!\n\nRegards,\n%s Team' %(settings.CONTEST_NAME, settings.CONTEST_NAME))
            
            send_mail(email_subject,
                      email_body,
                      settings.CONTEST_EMAIL,
                      [user.email])
            
            return render_to_response('simple_message.html', 
                                      {'message' : 'A mail has been sent to ' +
                                       '%s. Follow the link in the mail to ' %(user.email)+
                                       'activate your account<br />'+
                                       '<span class="bold">Note :</span>If you think your confirmation mail has not arrived, please check your Spam/Bulk'+
                                       ' before contacting us.',
                                       }, RequestContext(request))
                                       #'user' : request.user})
        else:
            print 'Errors'
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('activate.html', 
            {'form': form}, RequestContext(request))
    #,'user':request.user})

@login_required
def change_details(request):
    ''' Change details of existing users '''

    manipulator = ChangeDetails(request.user.id)

    if request.method == 'POST':
        new_data = request.POST.copy()
        print 'By post', new_data
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            new_user = manipulator.save(new_data)
            return render_to_response('simple_message.html',
                {'message' : 'Your Details have been updated'}, RequestContext(request))
        else:
            print 'Errors at change_details :', errors
    else:
        errors = {}
        new_data = manipulator.flatten_data()
        print new_data
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('change_profile.html',
            {'form': form}, RequestContext(request))


    return render_to_response('register.html', {'form':form}, RequestContext(request))


def confirm (request, activation_key):
    ''' Activates an inactivated account 
    activation_key : The key created for the user during registration'''
    if request.user.is_authenticated():
        return render_to_response('simple_message.html',
                {'message' : 'You are already registerd!'}, RequestContext(request))
    user_profile = get_object_or_404(UserProfile,
                                     activation_key=activation_key)
    #TODO : Prevent attacks by resetting the key when activated
    if user_profile.key_expires < datetime.datetime.today():
        # TODO: Dangerous Thing to do! If a user submits through an
        # expired account, account gets deleted!
        # u = user_profile.user
        # user_profile.delete();
        # u.delete()
        return render_to_response('simple_message.html',
                    {'message' : 'Your activation key has ' +
                                   'expired. Please register again'}, RequestContext(request))
    user_account = user_profile.user
    user_account.is_active = True
    user_account.save()
    return render_to_response('simple_message.html',
                {'message' : 'Thou arth registered. Begin thy ' +
                               'quest for glory!'}, RequestContext(request))


def logout_view (request):
    ''' Logs out user and redirects to home page '''
    logout(request)
    return HttpResponseRedirect('/opc/')

def forgot_password(request):
    ''' Sends mail to user on reset passwords '''
    if request.user.is_authenticated():
        return render_to_response('simple_message.html', 
                    {'message' : 'You already know your password. Use Change password to change your existing password'}, RequestContext(request))

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
                        {'message' : 'A mail has been sent to %s with the new password' %(u.email) }, RequestContext(request))
        else:
            print 'Errors'
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('reset_password.html', {'form': form}, RequestContext(request))

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
                return render_to_response('simple_message.html',
                        {'message' : 'Password Changed!'}, RequestContext(request))
            else:
                    errors['old_password'].append('Old Password is incorrect')
        else: 
            print errors
    else:
        errors = new_data = {}

    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('change_password.html', {'form': form}, RequestContext(request))


@login_required
def submit_code (request, problem_no=None):
    ''' Handles Submitting problem. Gets User identity from sessions. requires an authenticated user
    problem_no : The primary key(id) of the problem for which the code is being submitted '''
    manipulator = SubmitSolution()

    if request.POST:
        new_data = request.POST.copy()
        new_data.update(request.FILES)
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            content  = request.FILES['file_path']['content']
            question = get_object_or_404(Question, id=new_data['question_id'])
            if len(content) > question.source_limit:
                return render_to_response('simple_message.html',
                            {'message' : 'Source Limit Exceeded. Code was NOT saved.'}, RequestContext(request))
            
            user = get_object_or_404(UserProfile, user=request.user)
            language = get_object_or_404(Language, id=new_data['language_id'])

            #TODO: Make all this a decorator and apply it only if defined in settings
            if question in [a.question for a in user.solved.all()]: #If the user has already solved this problem
                return render_to_response('simple_message.html',
                        {'message' : 'You have already solved this problem. The current submission is ignored'}, RequestContext(request))
            if user.attempt_set.filter(question=question).count()>question.submission_limit:
                return render_to_response('simple_message.html',
                        {'message' : 'You have exceeded your submission limit for this problem. The current submission is ignored'},
                        RequestContext(request))

            attempt = Attempt (user = user, question=question, code=content, language=language, file_name=request.FILES['file_path']['filename'])
            attempt.error_status = 'Being Evaluated'
            attempt.result = False
            attempt.save()
            pending = ToBeEvaluated (attempt=attempt)
            pending.save()

            return render_to_response('simple_message.html',
                        {'message' : 'Code Submitted!'}, RequestContext(request))
        else:
            print 'Errors at submit_code: ',errors
    else:
        errors = new_data = {}
        if problem_no:
            new_data = MultiValueDict({'question_id':[problem_no]})

    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('submit_code.html', {'form': form}, RequestContext(request))

###################
## Evaluator API ##
###################

def retrieve_attempt (request, key_id):
    ''' Get an attempt to be evaluated as an XML and delete it from ToBeEvaluated'''

    get_object_or_404(EvalKey, key=key_id)
    # TODO: Enable RSA/<some-other-pub-key-crypto> based auth here
    from hackzor.settings import ATTEMPT_TIMEOUT
    from datetime import datetime
    for being_eval_attempt in BeingEvaluated.objects.order_by('time_of_retrieval'):
        #TODO: Handle the condition that the other evaluator returns a result all of a sudden!
        now = datetime.now()
        diff = now - being_eval_attempt.time_of_retrieval
        if (diff.seconds > ATTEMPT_TIMEOUT):
            attempt = being_eval_attempt.attempt
            being_eval_attempt.delete()
            to_be_eval_attempt = ToBeEvaluated(attempt=attempt)
            to_be_eval_attempt.save()
        else: break
    attempt_xmlised = utils.get_attempt_as_xml()
    if not attempt_xmlised: raise Http404
    return HttpResponse (content = attempt_xmlised, mimetype = 'application/xml')

def retrieve_question_set (request, key_id):
    ''' Get the list of questions  as XML'''

    get_object_or_404(EvalKey, key=key_id)
    # TODO: Enable RSA/<some-other-pub-key-crypto> based auth here
    question_set_xmlised = utils.get_question_set_as_xml()
    return HttpResponse (content = question_set_xmlised, 
            mimetype = 'application/xml')

def submit_attempt (request, key_id):
    ''' Get evaluated result and update DB '''

    get_object_or_404(EvalKey, key=key_id)
    if request.POST:
        xml_data = request.raw_post_data
        aid, result, error_status = utils.get_result(xml_data)
        print aid, result, error_status
        attempt = get_object_or_404(Attempt, id=aid)
        attempt.verified(int(result) == 0, error_status)
        attempt_in_being_evaluated = BeingEvaluated.objects.get(attempt=attempt)
        attempt_in_being_evaluated.delete()
    return HttpResponse('Done!')
