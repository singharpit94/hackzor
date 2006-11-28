from django.contrib.auth.models import User 
from django.conf.urls.defaults import *
from hackzor.server.models import Question, UserProfile

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

        (r'^problems/submit/$',
            'hackzor.server.views.submit_code',),

        # Search Questions page
        (r'^search/',
         'hackzor.server.views.search_questions',),

        # TOP 10 list
        (r'^top10/$',
            'django.views.generic.list_detail.object_list',
            { 'queryset' : UserProfile.objects.order_by('score')[:10], 'template_name' : 'view_toppers.html' }),

        # To display a particular user's Stats
        #Not Finished!
        # TODO: Use a shared dict called User_dict along with TOP 10
        (r'^users/(?P<object_id>\d+)/$',
        'django.views.generic.list_detail.object_detail',
        { 'queryset' : User.objects.all(), 'template_name' : 'view_user.html'}),

        # To get an Attempt
        # TODO: To be used by Evaluator only!! Add encryption!
        (r'^evaluator/getattempt/',
         'hackzor.server.views.retreive_attempt',),

        # To get Question set
        # TODO: To be used by Evaluator only!! Add encryption!
        (r'^evaluator/getquestionset/',
         'hackzor.server.views.retreive_question_set',),

        )

