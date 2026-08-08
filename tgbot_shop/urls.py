from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('admin/', admin.site.urls),
]

# Product photos are user-uploaded, so WhiteNoise (static only) won't serve
# them. In DEBUG Django does it; in production put them behind the web server.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
