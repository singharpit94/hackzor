from django.db import models

class User(models.Model):
	def __str__(self):
		return self.alias
	fullName = models.CharField(maxlength=32)
	alias	 = models.CharField(maxlength=32)
	password = models.CharField(maxlength=32)
	email	 = models.EmailField()
	score	 = models.PositiveIntegerField(default=0)
	class Admin: pass

class Question(models.Model):
	def __str__(self):
		return self.name
	name 		= models.CharField(maxlength=32)
	text	   	= models.TextField()
	testInput  	= models.FilePathField(path='/home/rave/Django/hackzor/judge/evaluators/testCases', recursive=True)
	testOutput 	= models.FilePathField(path='/home/rave/Django/hackzor/judge/evaluators/testCases', recursive=True)
	evaluatorPath   = models.FilePathField(path='/home/rave/Django/hackzor/judge/evaluators/pyCode', recursive=True)
	class Admin: pass

class Attempt(models.Model):
	def __str__(self):
		return self.user.alias
	user		= models.ForeignKey(User)
	question	= models.ForeignKey(Question)
	attemptNumber	= models.PositiveIntegerField()
	result		= models.BooleanField()
	class Admin: pass
