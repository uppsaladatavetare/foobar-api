from django.conf.urls import patterns, include, url
from django.contrib import admin

from .rest.urls import router

urlpatterns = patterns(
    '',
    url(r'^api/', include(router.urls, namespace='api')),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^api-auth/', include('rest_framework.urls',
        namespace='rest_framework')),

    url(r'^admin/foobar/account/card/(?P<card_id>\d+)',
        'foobar.views.account_for_card', name='account_for_card'),
    url(r'^admin/', include(admin.site.urls)),
)
