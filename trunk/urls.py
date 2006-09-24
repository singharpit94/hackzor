from django.conf.urls.defaults import *
from django.views.static import serve

urlpatterns = patterns('',
		# Everything we do will start with the URL opc/
	(r'^opc/', include('hackzor.server.urls')),
	# For serving static files. (like uploaded files etc.) For development Sever only
	#(r'^(.*)$', 'django.views.static.serve', {'document_root': '/home/rave/Django/hackzor/'}),
)
