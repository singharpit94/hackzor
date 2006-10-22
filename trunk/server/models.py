from django.contrib.auth.models import User 
from django.db import models
import os

class UserProfile(models.Model):
    """ Contains details about the user """
    # TODO: Change this to self.name and have special method for activation key
    def __str__(self):
        return self.user.get_full_name()
    score = models.PositiveIntegerField(default=0)
    activation_key = models.CharField(maxlength=40)
    key_expires = models.DateTimeField() 
    user = models.OneToOneField(User)
    class Admin: pass

class Question(models.Model):
    """ Contains the question content and path to evaluators and test cases """
    def __str__(self):
        return self.name
    name = models.CharField(maxlength=32)
    text = models.TextField()
    test_input = models.FileField(upload_to = 'hidden/evaluators/testCases')
    test_output = models.FileField(upload_to= 'hidden/evaluators/testCases/')
    evaluator_path = models.FileField(upload_to = 'hidden/evaluators/pyCode/')
    score = models.IntegerField()
    class Admin: pass

class Language(models.Model):
    def __str__(self):
        return self.compiler
    compiler = models.CharField(maxlength=32)
    class Admin: pass

class Attempt(models.Model):
    """ Contains Attempt Information """
    def __str__(self):
        return self.user.user.username + ' :' + self.question.name 
    user = models.ForeignKey(UserProfile)
    question = models.ForeignKey(Question)
    result = models.BooleanField()
    code = models.TextField()
    language = models.ForeignKey(Language)
    time_of_submit = models.DateTimeField(auto_now_add=True)
    class Admin: pass

class Pending(models.Model):
    attempt = models.ForeignKey(Attempt)
