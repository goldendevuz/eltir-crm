"""
WSGI config for tgbot_shop project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tgbot_shop.settings')

application = get_wsgi_application()

# Mahsulot rasmlari MEDIA_ROOT da turadi. WhiteNoise middleware faqat
# statikani beradi, django.conf.urls.static.static() esa DEBUG=False da
# bo'sh ro'yxat qaytaradi — shuning uchun prodda panelda rasmlar o'rniga
# singan belgi chiqardi. Nginx qo'shmaslik uchun media'ni ham shu yerda
# WhiteNoise'ga beramiz.
from django.conf import settings  # noqa: E402  (Django sozlangandan keyin)
from whitenoise import WhiteNoise  # noqa: E402

application = WhiteNoise(application)
application.add_files(str(settings.MEDIA_ROOT), prefix=settings.MEDIA_URL)
