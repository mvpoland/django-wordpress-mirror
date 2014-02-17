from django.conf.urls import patterns, url

from wordpress_mirror.views import mirror

urlpatterns = patterns('',
    url(r'^$', mirror, name='wordpress_blog_mirror'),
    url(r'^(?P<wp_path>.*)$', mirror, name='wordpress_blog_mirror_path'),
)
