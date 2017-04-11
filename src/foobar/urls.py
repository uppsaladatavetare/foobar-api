from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

import foobar.views
import rest_framework.urls
from rest_framework.documentation import include_docs_urls

from .rest.urls import router

API_TITLE = 'FooBar API'

urlpatterns = [
    url(r'^api/', include(router.urls, namespace='api')),
    url(r'^docs/', include_docs_urls(title=API_TITLE)),
    url(r'^api-auth/', include(rest_framework.urls,
        namespace='rest_framework')),
    url(r'^admin/wallet_management/(?P<obj_id>.+)',
        foobar.views.wallet_management,
        name='wallet_management'),
    url(r'^admin/foobar/account/card/(?P<card_id>\d+)',
        foobar.views.account_for_card, name='account_for_card'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'profile/(?P<token>[^/]+)/$',
        foobar.views.ProfileView.as_view(),
        name='profile-home'),
    url(r'profile/(?P<token>[^/]+)/edit/$',
        foobar.views.EditProfileView.as_view(),
        name='profile-edit'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
