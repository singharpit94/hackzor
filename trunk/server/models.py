from django.contrib.auth.models import User 
from django.db import models


class UserProfile(models.Model):
    """ Contains details about the user """
    def __str__(self):
        return self.activation_key
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
    test_input = models.FileField(upload_to = 'server/evaluators/testCases')
    test_output = models.FileField(upload_to= 'server/evaluators/testCases/')
    evaluator_path = models.FileField(upload_to = 'server/evaluators/pyCode/')
    class Admin: pass

class Attempt(models.Model):
    """ Contains Attempt Information """
    def __str__(self):
        return self.user.alias + ' :' + self.question.name 
    user = models.ForeignKey(UserProfile)
    question = models.ForeignKey(Question)
    attempt_number = models.PositiveIntegerField()
    result = models.BooleanField()
    class Admin: pass

