from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('A_Lei_no_NT.urls', 'A_Lei_no_NT'), namespace='A_Lei_no_NT')),
'''
    path("favicon.ico", RedirectView.as_view(
        url=static("favicon.ico"),
        permanent=False,  # evita cache duro de 301
    )),
'''
    ]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)