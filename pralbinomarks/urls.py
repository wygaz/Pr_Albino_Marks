# pralbinomarks/urls.py
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.views.generic import RedirectView
from django.http import HttpResponse

# Para servir MEDIA em dev
from django.conf.urls.static import static as serve_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz/', lambda request: HttpResponse('ok', content_type='text/plain'), name='healthz'),
    path(
        'conta/entrar/',
        auth_views.LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True),
        name='login',
    ),
    path('conta/sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('sermoes/', include('sermoes.urls')),
    path('', include(('A_Lei_no_NT.urls', 'A_Lei_no_NT'), namespace='A_Lei_no_NT')),


    # Evita depender do manifest de staticfiles durante o import das URLs.
    path('favicon.ico', RedirectView.as_view(
        url='/static/favicon.ico',
        permanent=False,  # evita cache 301 duro
    )),
]

# MEDIA: só em dev
if settings.DEBUG:
    urlpatterns += serve_media(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
