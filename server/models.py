import os, datetime
from django.contrib.auth.models import User 
from django.db import models
from hackzor.server.country_choices import country_choices 

class Question(models.Model):
    ''' Contains problem statement and paths to judge code and test cases '''

    name = models.CharField(verbose_name='Problem Name', maxlength=32)
    text = models.TextField(verbose_name='Problem Statement')
    # TODO: Input testcases are visible to the user, put them into some safe place 
    # TODO: Make the test_input and evaluator_path a part of the database, rather than as files
    test_input = models.FileField(
            verbose_name='Input Test Cases', upload_to = 'hidden/evaluators/testCases')
    expected_output = models.FileField(
            verbose_name='Expected Output', upload_to = 'hidden/evaluators/testCases')
    # TODO: Change name from evaluator_path to judge_path in other files
    judge_path = models.FileField(
            verbose_name='Path to Judge Code', upload_to = 'hidden/evaluators/pyCode/')
    score = models.IntegerField()
    time_limit = models.FloatField(max_digits=3, decimal_places = 1)
    memory_limit = models.PositiveIntegerField()
    source_limit = models.PositiveIntegerField()
    submission_limit = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    class Admin: pass


class UserProfile(models.Model):
    ''' Contains additional details about the user '''

    score = models.PositiveIntegerField(default=0)
    activation_key = models.CharField(maxlength=40)
    key_expires = models.DateTimeField(verbose_name='Expiry date-time for Key') 
    user = models.OneToOneField(User)
    solved = models.ManyToManyField('Attempt', verbose_name='Succesful Attempts', blank=True)
    country = models.CharField(maxlength=30, choices=country_choices)
    organization = models.CharField(verbose_name='Organization/Institution', maxlength=30)
    contact_address = models.TextField()

    def __str__(self):
        return self.user.get_full_name()

    def solves(self, evaluated_attempt):
        ''' Adds evaluated_attempt to solved if it is a successful attempt '''

        if not evaluated_attempt.result: return
        if evaluated_attempt.question not in [ i.question for i in self.solved.all() ]:
            # Not solved already
            self.solved.add(evaluated_attempt)
            self.score += evaluated_attempt.question.score
            self.save()

    def get_total_submission_time(self):
        ''' Returns sum of time taken to solve all correct problems with respect to 
            the start of the contest'''

        #TODO: See if we can cache this
        from hackzor.settings import CONTEST_START_TIME
        sum_time = datetime.timedelta(0)
        for successful_attempt in self.solved.iterator():
            # Find the first successful attempt for this problem by this user
            attempt = Attempt.objects.filter(user = self).filter(question = 
                    successful_attempt.question).filter(result = 
                            True).order_by('-time_of_submit')[0]
            sum_time += (attempt.time_of_submit - CONTEST_START_TIME)
        self.total_submission_time = sum_time
        return sum_time
    
    class Admin: pass


class Language(models.Model):
    ''' Contains only the language name for now, should contain the compiler name later
    ( helpful incase we need to rejudge all submission on a previous version ) '''

    compiler = models.CharField(maxlength=32)

    def __str__(self):
        return self.compiler
    
    class Admin: pass


class Attempt(models.Model):
    ''' Contains information on a user's attempt on solving a problem '''

    user = models.ForeignKey(UserProfile)
    question = models.ForeignKey(Question)
    result = models.BooleanField(verbose_name='Is a successful attempt?')
    code = models.TextField()
    file_name = models.CharField(maxlength=32)
    language = models.ForeignKey(Language)
    time_of_submit = models.DateTimeField(auto_now_add=True)
    error_status = models.TextField(verbose_name='Verbose Error Status')

    def __str__(self):
        return self.user.user.username + ' :' + self.question.name

    def verified(self, result, error_status): 
        ''' Updates the DB with the values if result is correct'''
        if result==True:
            self.result = True
            self.user.solves(self)
        else:
            self.result = False
        self.error_status = error_status
        self.save()
    
    class Admin: pass


class ToBeEvaluated(models.Model):
    ''' Contains Attempts which are yet to be Evaluated '''

    attempt = models.ForeignKey(Attempt)


class BeingEvaluated(models.Model):
    ''' Contains Attempts which have been assigned to an Evaluator but whose
    evaluation process is yet to be completed. In the case that an evaluator
    crashes, these attempt might need to be moved back to ToBeEvaluated '''

    attempt = models.ForeignKey (Attempt)
    time_of_retrieval = models.DateTimeField(auto_now_add=True)

class EvalKey(models.Model):
    ''' Contains Key details about Evaluators '''

    class Admin:pass
    key = models.CharField(maxlength=8, verbose_name="Pass Key for the evaluator")
