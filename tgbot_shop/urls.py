from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('admin/', admin.site.urls),
]

# DEBUG rejimida media'ni Django beradi. Prodda static() bo'sh ro'yxat
# qaytaradi, shuning uchun u yerda media WhiteNoise orqali uzatiladi —
# tgbot_shop/wsgi.py ga qarang.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
