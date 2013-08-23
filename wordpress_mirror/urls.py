from django.conf.urls.defaults import *

from wordpress_mirror.views import *

urlpatterns = patterns('',
    url(r'^$', overview, name='wordpress_blog_overview'),
    url(r'^page/(?P<page>\d*)/$', overview, name='wordpress_blog_overview'),
    url(r'^permalink/(?P<post_id>\d*)/$', permalink, name='wordpress_blog_permalink'),
    url(r'^detail/(?P<slug>.*)/$', detail, name='wordpress_blog_detail'),
)
