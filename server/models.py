from django.db import models

class User(models.Model):
	""" Contains details about the user """
	def __str__(self):
		return self.alias
	fullName = models.CharField(maxlength=32)
	alias = models.CharField(maxlength=32)
	password = models.CharField(maxlength=32)
	email = models.EmailField()
	score = models.PositiveIntegerField(default=0)
	class Admin: pass

class Question(models.Model):
	""" Contains the question content and path to evaluators and test cases """
	def __str__(self):
		return self.name
	name = models.CharField(maxlength=32)
	text = models.TextField()
	testInput = models.FileField(upload_to = 'server/evaluators/testCases')
	testOutput = models.FileField(upload_to= 'server/evaluators/testCases/')
	evaluatorPath   = models.FileField(upload_to = 'server/evaluators/pyCode/')
	class Admin: pass

class Attempt(models.Model):
	""" Contains Attempt Information """
	def __str__(self):
		return self.user.alias + ' :' + self.question.name 
	user = models.ForeignKey(User)
	question = models.ForeignKey(Question)
	attemptNumber = models.PositiveIntegerField()
	result = models.BooleanField()
	class Admin: pass
