# These are local settings that are ignored by git
LOCAL_SETTINGS = True
from tabletracker.settings import *

# SECURITY WARNING: keep the secret key used in production secret!
# from django.utils.crypto import get_random_string as grs
# print(grs(50, 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'))
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db', 'db.sqlite3'),
    }
}
