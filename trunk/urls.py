from django.conf.urls.defaults import *
#from django.views.static import serve

urlpatterns = patterns('',
                       # Everything we do will start with the URL opc/
                       (r'^opc/', include('hackzor.server.urls')),

                       # @Prashanth :Shouldn't this go into the OPC path?
                       (r'^accounts/confirm/(?P<activation_key>\w+)/$',
                        'hackzor.server.views.confirm'),

                       # For serving static files. (like uploaded files etc.)
                       # For development Sever only
                       (r'^(.*)$', 'django.views.static.serve',
                        {'document_root': 'media'}),
                       )
