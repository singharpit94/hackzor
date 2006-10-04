from django.conf.urls.defaults import *
from hackzor.server.models import Question

problem_dict = {
	'queryset' : Question.objects.all()
}

urlpatterns = patterns('',

		# To list the problem set
    (r'^problems/$', 'django.views.generic.list_detail.object_list', dict(problem_dict, template_name='problem_set.html')),
    		
    		# To display a particular problem
    #(r'^problems/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', 
								#dict(problem_dict, template_name='view_problem.html')),
    (r'^problems/(?P<id>\d+)/$', 'hackzor.server.views.viewProblem'), 
	
    		
    		# For now the problem set is the home page
    (r'^$', 'django.views.generic.list_detail.object_list', dict(problem_dict, template_name='problem_set.html')),

		# Auto-generated admin
    (r'^admin/', include('django.contrib.admin.urls')),
)
