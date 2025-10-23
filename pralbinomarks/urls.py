# pralbinomarks/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import RedirectView

# 1) Para montar URL estática (favicon)
from django.templatetags.static import static as static_url
# 2) Para servir MEDIA em dev
from django.conf.urls.static import static as serve_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('A_Lei_no_NT.urls', 'A_Lei_no_NT'), namespace='A_Lei_no_NT')),

    # Opcional: atender /favicon.ico
    path('favicon.ico', RedirectView.as_view(
        url=static_url('favicon.ico'),
        permanent=False,  # evita cache 301 duro
    )),
]

# MEDIA: só em dev
if settings.DEBUG:
    urlpatterns += serve_media(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
