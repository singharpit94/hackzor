from django.conf.urls.defaults import *
#from django.views.static import serve

urlpatterns = patterns('',


        # For now, The home page will be the OPC
        ('^$', 
            'django.views.generic.simple.redirect_to', 
            {'url': '/opc'}
        ),

        # Everything we do will start with the URL opc/
        (r'^opc/', include('hackzor.server.urls')),

        (r'^accounts/confirm/(?P<activation_key>\w+)/$',
            'hackzor.server.views.confirm'),

        #For django login, authenticated login 
        # gets redirected to /accounts/profile
        ('^accounts/profile/$', 
            'django.views.generic.simple.redirect_to', 
            {'url': '/opc'}
        ),

        #Login
        (r'^accounts/login/$', 
            'django.contrib.auth.views.login',
            {'template_name' : 'login.html'}),

        #Logout
        (r'^accounts/logout/$', 
            'hackzor.server.views.logout_view'),
        
        # Registration Page
        (r'^accounts/register/$',
            'hackzor.server.views.register'),

        # Admin Interface 
        (r'^admin/', 
            include('django.contrib.admin.urls')),

        # For serving static files. (like uploaded files etc.)
        # For development Sever only
        (r'^(.*)$', 'django.views.static.serve',
            {'document_root': 'media'}),

        )
