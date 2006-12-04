import datetime, random, sha
import os, sys

from django import forms 
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.mail import send_mail
from django.utils.datastructures import MultiValueDict
from django.db.models import Q

from hackzor import settings
from hackzor.server.models import *
from hackzor.server.forms import *
import hackzor.server.utils as utils
import hackzor.evaluator.GPG as GPG

def view_last_n_submissions (request, n, sort_by=None, for_user=None):
    """ View to list the last n submissions sorted by the 'sort by' field """
    print n, sort_by, for_user
    if sort_by == None:
        sort_by = 'time_of_submit'
    if n == None or int(n) < 1:
        raise Http404

    if for_user==None:
        submissions = Attempt.objects.order_by(sort_by)[:int(n)]
        for_user=""
    else:
        try:
            user = User.objects.get(username__iexact=for_user).userprofile
            submissions = Attempt.objects.filter(user__exact=user).order_by(sort_by)[:int(n)]
        except User.DoesNotExist:
            submissions = Attempt.objects.order_by(sort_by)[:int(n)]
    return render_to_response('view_submissions.html',
            {'submissions':submissions, 'user': request.user,
                'n' : n, 'for_user':for_user})



def view_problem (request, id):
    """ Simple view to display view a particular problem 
    id : the primary key(id) of the Problem requested """
    path_to_media_prefix = os.path.join(os.getcwd(), settings.MEDIA_ROOT)
    object = get_object_or_404(Question, id=id)
    inp = open(os.path.join(path_to_media_prefix , object.test_input)).read().split('\n')
    #out = open(os.path.join(path_to_media_prefix , object.test_output)).read().split('\n')
    #testCase = [x for x in zip(inp, out)]
    return render_to_response('view_problem.html',
                              {'object':object, #'testCase':testCase,
                               'user': request.user})

def register(request):
    """ creates an inactive account by using the manipulator for the non-existant user and sends a confirm link to the user"""
    if request.user.is_authenticated():
         # They already have an account; don't let them register again
         return render_to_response('simple_message.html',
                                   {'message' :"You are already registered.",
                                       'user': request.user})

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
            # TODO: Store the message in a seperate file or DB
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
                                       'activate your account',
                                       'user' : request.user})
        else:
            print 'Errors'
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('register.html', 
            {'form': form,'user':request.user})


def confirm (request, activation_key):
    """ Activates an inactivated account 
    activation_key : The key created for the user during registration"""
    if request.user.is_authenticated():
        return render_to_response('simple_message.html',
                {'user':request.user, 'message' : 'You are already registerd!'})
    user_profile = get_object_or_404(UserProfile,
                                     activation_key=activation_key)
    #TODO : Prevent attacks by resetting the key when activated
    if user_profile.key_expires < datetime.datetime.today():
        u = user_profile.user
        user_profile.delete();
        u.delete()
        return render_to_response('simple_message.html',
                {'user': request.user, 'message' : 'Your activation key has ' +
                                   'expired. Please register again'})
    user_account = user_profile.user
    user_account.is_active = True
    user_account.save()
    return render_to_response('simple_message.html',
            {'user': request.user, 'message' : 'Thou arth registered. Begin thy ' +
                               'quest for glory!'})


def logout_view (request):
    logout(request)
    return HttpResponseRedirect('/opc/')

def forgot_password(request):
    ''' Sends mail to user on reset passwords '''
    if request.user.is_authenticated():
        return render_to_response('simple_message.html', 
                {'user':request.user, 'message' : 'You already know your password. Use Change password to change your existing password'})

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
                    {'user':request.user, 'message' : 'A mail has been sent to %s with the new password' %(u.email) })
        else:
            print 'Errors'
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('reset_password.html', {'user':request.user, 'form': form})

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
                #TODO: The Navibar goes crazy after this, find out the reason
                user.save()
                return render_to_response('simple_message.html',
                        {'user':request.user, 'message' : 'Password Changed!'})
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
    """ Handles Submitting problem. Gets User identity from sessions. requires an authenticated user
    problem_no : The primary key(id) of the problem for which the code is being submitted """
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
                        {'user':request.user, 'message' : 'Source Limit Exceeded. Code was NOT saved.'})
            
            user = get_object_or_404(UserProfile, user=request.user)
            language = get_object_or_404(Language, id=new_data['language_id'])

            attempt = Attempt (user = user, question=question, code=content, language=language, file_name=request.FILES['file_path']['filename'])
            attempt.error_status = "Being Evaluated"
            attempt.save()
            pending = ToBeEvaluated (attempt=attempt)
            pending.save()

            return render_to_response('simple_message.html',
                    {'user':request.user, 'message' : 'Code Submitted!'})
        else:
            print errors
    else:
        errors = new_data = {}
        if problem_no:
            new_data = MultiValueDict({'question_id':[problem_no]})

    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('submit_code.html', {'form': form, 'user':request.user})

def search (request):
    """ Search Engine for the Questions"""
    beenthere=False
    result = []
    if request.GET:
        beenthere=True
        data = request.GET.copy()
        keywords = data.getlist ('search_text')[0]
        if keywords:
            keywords = keywords.split()
            #TODO: Exclude Staff accounts in Search
            questions_results = Question.objects.filter( 
                    Q(text__icontains=keywords[0]) | Q(name__icontains=keywords[0]) )
            user_results = User.objects.filter(
                    Q(username__icontains=keywords[0]) | Q(first_name__icontains=keywords[0])| Q(last_name__icontains=keywords[0] ) )

            for k in keywords[1:]:
                questions_results = questions_results.filter( 
                        Q(text__icontains=k) | Q(name__icontains=k) )
                user_results = user_results.filter(
                        Q(username__icontains=keywords) | Q(first_name__icontains=keywords)| Q(last_name__icontains=keywords ) )
                if questions_results.count() == 0 and user_results.count() == 0:
                    break
            result = list(questions_results)
            result.extend(list(user_results))

    return render_to_response('search_result.html', {'user':request.user, 'beenthere':beenthere, 'result':result})



def retrieve_attempt (request, key_id):
    """ Get an attempt to be evaluated as an XML and delete it from ToBeEvaluated"""
    # TODO: Enable RSA/<some-other-pub-key-crypto> based auth here
    from hackzor.settings import ATTEMPT_TIMEOUT
    from datetime import datetime
    for being_eval_attempt in BeingEvaluated.objects.sort_by('time_of_retrieval'):
        #TODO: Handle the condition that the other evaluator returns a result all of a sudden!
        now = datetime.now()
        diff = now - being_eval_attempt.time_of_retrieval
        if (now.seconds > ATTEMPT_TIMEOUT):
            attempt = being_eval_attempt.attempt
            being_eval_attempt.delete()
            to_be_eval_attempt = ToBeEvaluated(attempt=attempt)
            to_be_eval_attempt.save()
        else: break
    attempt_xmlised = utils.get_attempt_as_xml(key_id)
    if not attempt_xmlised:
        raise Http404
    return HttpResponse (content = attempt_xmlised, mimetype = 'application/xml')

def retrieve_question_set (request, key_id):
    """ Get the list of questions  as XML"""
    # TODO: Enable RSA/<some-other-pub-key-crypto> based auth here
    question_set_xmlised = utils.get_question_set_as_xml(key_id)
    return HttpResponse (content = question_set_xmlised, 
            mimetype = 'application/xml')

def submit_attempt (request, key_id):
    """ Get evaluated result and update DB """
    if request.POST:
        xml_data = request.raw_post_data
        global obj
        try:
            xml_data = obj.verify(xml_data).data
        except:
            print 'Error'
            return HttpResponse('Error!')
        aid, result, error_status = utils.get_result(xml_data)
        attempt = get_object_or_404(Attempt, id=aid)
        attempt.error_status = error_status
        if int(result)>0:
            attempt.result = True
            attempt.user.score += attempt.question.score
            attempt.user.save()
        else:
            attempt.result = False
        attempt.save()
        attempt_in_being_evaluated = BeingEvaluated.objects.get(attempt=attempt)
        attempt_in_being_evaluated.delete()
    return HttpResponse('Done!')

def get_pub_key(request):
    """Returns the Public Key of the web server"""
    # TODO: Use this function
    global obj
    return HttpResponse(obj.showpubkey())

obj = GPG.GPG()
# Adding global variable for better performance. TODO: Contemplate moving this
# inside the respective functions
