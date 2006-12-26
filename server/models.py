from django.contrib.auth.models import User 
from django.db import models
import os
import hackzor.evaluator.GPG as GPG

class Question(models.Model):
    """ Contains the question content and path to evaluators and test cases """
    def __str__(self):
        return self.name
    
    name = models.CharField(maxlength=32)
    text = models.TextField()
    # TODO: Input testcases are visible to the user, put them into some safe place 
    test_input = models.FileField(upload_to = 'hidden/evaluators/testCases')
    evaluator_path = models.FileField(upload_to = 'hidden/evaluators/pyCode/')
    score = models.IntegerField()
    time_limit = models.FloatField(max_digits=3, decimal_places = 1)
    memory_limit = models.PositiveIntegerField()
    source_limit = models.PositiveIntegerField()
    class Admin: pass


class UserProfile(models.Model):
    """ Contains details about the user """
    def __str__(self):
        return self.user.get_full_name()
    def solves(self, problem):
        ''' Checks if it has already solved the problem, which is an instance of Question'''
        if problem not in self.solved.all():
            self.solved.add(problem)
            self.score += problem.score
            self.save()
    
    score = models.PositiveIntegerField(default=0)
    activation_key = models.CharField(maxlength=40)
    key_expires = models.DateTimeField() 
    user = models.OneToOneField(User)
    solved = models.ManyToManyField(Question)
    class Admin: pass


class Language(models.Model):
    """ Contains only the language name for now, should contain the compiler name later
    ( helpful incase we need to rejudge all submission on a previous version ) """
    def __str__(self):
        return self.compiler
    
    compiler = models.CharField(maxlength=32)
    class Admin: pass


class Attempt(models.Model):
    """ Contains Attempt Information """
    def __str__(self):
        return self.user.user.username + ' :' + self.question.name
    def verified(self, result, error_status): 
        ''' Updates the DB with the values if result is correct'''
        if result==True:
            self.result = True
            self.user.solves(self.question)
        else:
            self.result = False
        self.error_status = error_status
        self.save()
    
    user = models.ForeignKey(UserProfile)
    question = models.ForeignKey(Question)
    result = models.BooleanField()
    code = models.TextField()
    file_name = models.CharField(maxlength=32)
    language = models.ForeignKey(Language)
    time_of_submit = models.DateTimeField(auto_now_add=True)
    error_status = models.TextField()
    class Admin: pass


class ToBeEvaluated(models.Model):
    """ Contains Attempts which are yet to be Evaluated """
    attempt = models.ForeignKey(Attempt)


class BeingEvaluated(models.Model):
    """ Contains Attempts which have been assigned to an Evaluator but whose
    evaluation process is yet to be completed. In the case that an evaluator
    crashes, these attempt might need to be moved back to ToBeEvaluated """
    attempt = models.ForeignKey (Attempt)
    time_of_retrieval = models.DateTimeField(auto_now_add=True)

class PGP(models.Model):
    """ Contains Key details about Evaluators """
    PGPkey = models.TextField(blank=False)
    keyid = models.CharField(maxlength=8, editable=False)

    def save(self):
        obj = GPG.GPG()
        ret = obj.import_key(self.PGPkey)
        if ret.unchanged + ret.imported <= 0 or not ret.results:
            # TODO: Problem if key is already imported. Correct This
            return
        for keys in obj.list_keys():
            if keys['fingerprint'] == ret.results[0]['fingerprint']:
                # TODO: Support multiple key imports                                        
                self.keyid = keys['keyid']
                # This is to call the 'real' Save function
                super(PGP, self).save()
    class Admin:pass
