from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views
from rest_framework import urls, schemas


admin.site.site_url = settings.ADMIN_SITE_URL
admin.site.index_title = settings.ADMIN_SITE_TITLE
admin.site.site_header = settings.ADMIN_SITE_HEADER

urlpatterns = [
    path('sead/', RedirectView.as_view(url=settings.URL_PATH_PREFIX)),
    path(settings.URL_PATH_PREFIX[1:],include('suapintegration.urls')),
    path(
        settings.URL_PATH_PREFIX[1:],
        include(
            [
                path('admin/', admin.site.urls),
                path('markdownx/', include('markdownx.urls')),
                # path('', RedirectView.as_view(pattern_name='admin:index')),
                path('', include('agendamento.urls')),
            ]
        )
    ),
    path('', RedirectView.as_view(url=settings.URL_PATH_PREFIX)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path(settings.URL_PATH_PREFIX + '__debug__/', include(debug_toolbar.urls))]