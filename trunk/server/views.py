from django.shortcuts import render_to_response, get_object_or_404
from hackzor.server.models import Question

def viewProblem (request, id):
	object = Question.objects.get(id=id)
	inp = open(object.testInput).read().split('\n')
	out = open(object.testOutput).read().split('\n')
	testCase = [x for x in zip(inp, out)]
	return render_to_response('view_problem.html', {'object':object, 'testCase':testCase})
