from django.conf.urls.defaults import *
from hackzor.server.models import Question

problem_dict = {
	'queryset' : Question.objects.all()
}

urlpatterns = patterns('',

        # For now the problem set is the home page
        (r'^$', 'django.views.generic.list_detail.object_list',
            dict(problem_dict, template_name='problem_set.html')),

        # To list the problem set
        # Warning : Displayes a 404 if the Question Model is empty
        (r'^problems/$',
            'django.views.generic.list_detail.object_list',
            dict(problem_dict, template_name='problem_set.html')),

        # To display a particular problem
        #(r'^problems/(?P<object_id>\d+)/$',
        #'django.views.generic.list_detail.object_detail',
        #dict(problem_dict, template_name='view_problem.html')),
        (r'^problems/(?P<id>\d+)/$',
            'hackzor.server.views.viewProblem'),

        # Submit Solution Page
        (r'^problems/(?P<problem_no>\d+)/submit/$',
            'hackzor.server.views.submit_code'),

        )

