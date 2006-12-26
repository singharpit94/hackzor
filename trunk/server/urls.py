from django.contrib.auth.models import User 
from django.conf.urls.defaults import *
from hackzor.server.models import Question, UserProfile

problem_dict = {
	'queryset' : Question.objects.all()
}

urlpatterns = patterns('',

        # For now the problem set is the home page
        ('^$', 
            'django.views.generic.simple.redirect_to', 
            {'url': 'problems'}
        ),

        # To list the problem set
        (r'^problems/$',
            'django.views.generic.list_detail.object_list',
            dict(problem_dict, template_name='problem_set.html', allow_empty=True)),

        # To display a particular problem
        #(r'^problems/(?P<object_id>\d+)/$',
        #'django.views.generic.list_detail.object_detail',
        #dict(problem_dict, template_name='view_problem.html')),
        (r'^problems/(?P<id>\d+)/$',
            'hackzor.server.views.view_problem'),

        # Submit Solution Page
        (r'^problems/(?P<problem_no>\d+)/submit/$',
            'hackzor.server.views.submit_code'),

        (r'^problems/submit/$',
            'hackzor.server.views.submit_code',),

        # Search page
        (r'^search/',
         'hackzor.server.views.search',),

        # TOP 10 list
        (r'^top10/$',
            'django.views.generic.list_detail.object_list',
            { 'queryset' : UserProfile.objects.filter(user__is_active=True).order_by('-score')[:10], 'template_name' : 'view_toppers.html' }),

        # Last n submits 
        (r'^submits/last(?P<n>\d+)(/orderby/(?P<sort_by>(-)?\w+))?(/(?P<for_user>\w+))?/',
            'hackzor.server.views.view_last_n_submissions',),

        # To display a particular user's Stats
        #Not Finished!
        # TODO: Use a shared dict called User_dict along with TOP 10
        (r'^users/(?P<object_id>\d+)/$',
        'django.views.generic.list_detail.object_detail',
        { 'queryset' : User.objects.all(), 'template_name' : 'view_user.html'}),

        # To get an Attempt
        (r'^evaluator/(?P<key_id>\w+)/getattempt/',
         'hackzor.server.views.retrieve_attempt',),

        # To submit result of an Attempt
        (r'^evaluator/(?P<key_id>\w+)/submitattempt/',
         'hackzor.server.views.submit_attempt',),

        # To get Question set
        (r'^evaluator/(?P<key_id>\w+)/getquestionset/',
         'hackzor.server.views.retrieve_question_set',),

        (r'^evaluator/getpubkey/','hackzor.server.views.get_pub_key'),
        )

