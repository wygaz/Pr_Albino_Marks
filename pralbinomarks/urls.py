from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from A_Lei_no_NT import views  # importa views diretamente do app

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # Página inicial do site
    path('artigos/', include(('A_Lei_no_NT.urls', 'A_Lei_no_NT'), namespace='A_Lei_no_NT')),
]


# Servir arquivos de mídia apenas no modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
