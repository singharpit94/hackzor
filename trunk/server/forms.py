from django import forms 
from django.core import validators 
from django.contrib.auth.models import User
from hackzor.server.models import Question, Language

class RegistrationForm (forms.Manipulator):
    """copied mostly from
    http://www.b-list.org/weblog/2006/09/02/django-tips-user-registration

    Implements a registration form. Fields are
    1. User Name
    2. Password (with password matcher)
    3. Email ID
    4. First Name
    5. Last Name
    """
    
    def __init__(self):
        self.fields = (
            forms.TextField(field_name='username',
                            length=30, maxlength=30,
                            is_required=True,
                            validator_list=[validators.isAlphaNumeric,
                                            self.isValidUsername]),
            forms.EmailField(field_name='email',
                             length=30,
                             maxlength=30,
                             is_required=True,
                             validator_list=[self.isValidUsername]),
            forms.PasswordField(field_name='password1',
                                length=30,
                                maxlength=60,
                                is_required=True),
            forms.PasswordField(field_name='password2',
                                length=30, maxlength=60,
                                is_required=True,
                                validator_list=[validators.AlwaysMatchesOtherField('password1',
                                                                                   'Passwords must match.')]),
             forms.TextField(field_name='first_name',
                             length=20, maxlength=20,
                             is_required=True),                             
             forms.TextField(field_name='last_name',
                             length=20, maxlength=20,
                             is_required=True),
            )
    
    def isValidUsername (self, field_data, all_data):
        try:
            User.objects.get(username=field_data)
        except User.DoesNotExist:
            return
        raise validators.ValidationError('The username "%s" is already taken.' % field_data)

    def isValidEmail (self, field_data, all_data):
        try:
            User.objects.get(email=field_data)
        except User.DoesNotExist:
            return
        raise validators.ValidationError('The email "%s" is already registered.' % field_data)
        
    def save(self, new_data):
        u = User.objects.create_user(new_data['username'],
                                     new_data['email'],
                                     new_data['password1'])
        u.first_name = new_data['first_name']
        u.last_name = new_data['last_name']
        u.score = 0
        u.is_active = False
        u.save()
        return u


class LoginForm (forms.Manipulator):
    """ Designs a Login Form
    Simple matching of user name and password
    """
    def __init__ (self):
        self.fields = (
            forms.TextField(field_name='username',
                            length=30, maxlength=30,
                            is_required=True,
                            validator_list=[validators.isAlphaNumeric]),
            forms.PasswordField(field_name='password',
                                length=30,
                                maxlength=60,
                                is_required=True),
            )

class SubmitSolution (forms.Manipulator):
    """ Submit form that will only have a file upload field to upload the solution. 
    The user identification will be held in the session information."""
    def __init__ (self):
        Qchoices = []
        Lchoices = []
        for i in Question.objects.all():
            Qchoices.append( (i.id, i.name) )
        for i in Language.objects.all():
            Lchoices.append( (i.id, i.compiler) )
        Qchoices = tuple(Qchoices)
        Lchoices = tuple(Lchoices)

        self.fields = (
            forms.FileUploadField(field_name='file_path',
                        is_required=True),
            forms.SelectField(field_name='question_id',
                        choices=Qchoices,
                        is_required=True),
            forms.SelectField(field_name='language_id',
                        choices=Lchoices,
                        is_required=True),
            )


class ForgotPassword (forms.Manipulator):
    ''' Forgot Password Manipulator '''
    def __init__(self):
        self.fields = (
            forms.TextField(field_name='username',
                            length=30, maxlength=30,
                            is_required=True,
                            validator_list=[validators.isAlphaNumeric,
                                            self.isValidUsername]),
                            )
    def userExists(self):
        try:
            User.objects.get(username=field_data)
        except User.DoesNotExist:
            raise validators.ValidationError('The username "%s" is does not exist.' % field_data)
