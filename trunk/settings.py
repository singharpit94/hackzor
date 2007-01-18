# Django settings for hackzor project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'           # 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'hackzor'       # Or path to database file if using sqlite3.
DATABASE_USER = 'opc'             # Not used with sqlite3.
DATABASE_PASSWORD = 'opcadmin'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'Asia/Calcutta'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = 'media'

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = '/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'g7e34o)u-^sl(vq#p(be=o5$-1toh+2ki^8j*oae*e%$z(@ryn'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.cache.CacheMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'hackzor.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    'hackzor/server/templates',
)

TEMPLATE_CONTEXT_PROCESSORS = (
        "django.core.context_processors.auth",
        "django.core.context_processors.debug",
        "django.core.context_processors.i18n",
        "django.core.context_processors.request",
        "hackzor.server.views.get_contest_times"
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'hackzor.server',
)

AUTH_PROFILE_MODULE = 'server.UserProfile' 

# Replace with the name of your own contest
CONTEST_NAME = 'Hackzor' 
# replace with the email of your own contest
CONTEST_EMAIL = 'hackzor@googlegroups.com' 

# replace with the url of your own contest
                               # evaluator/settings.py
CONTEST_URL = 'localhost:8000' # should typically be the same as in

SESSION_COOKIE_AGE =1800

# This is that time that will be given before the attempt it retrieved will be
# moved back to TobeEvaluated
ATTEMPT_TIMEOUT = 60 # In Seconds

#For Cache
# Caching might create problems with individual pages. Make the site per-view cached
#CACHE_BACKEND = 'simple:///'
#CACHE_MIDDLEWARE_SECONDS = 10
#CACHE_MIDDLEWARE_KEY_PREFIX = ''
