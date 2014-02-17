import datetime

from django.utils import simplejson as json
from django.contrib.sites.models import Site
from django.conf import settings
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import Http404

from urlparse import urlparse, urlunparse, urljoin
from django.utils.http import urlencode

from freyja.core.localeurl.utils import locale_path, strip_path

import requests

REQUEST_TIMEOUT_SEC = 10

class Post(object):
    """
    Wrapper around a WordPress post JSON object
    """
    data = None
    lang = None
    country = None
    _url_localized = None
    _url_unlocalized = None

    def __init__(self, data=None, lang=None, country=None):
        self.data = data
        self.lang = lang
        self.country = country

    def __repr__(self):
        if self.data:
            return u'<WP mirror post %s: %s>' % (self.data.get('id', '<no id>'), self.data.get('slug', '<no slug>'))
        return u'<WP mirror post without data>'

    def __getitem__(self, key):
        return self.data[key]

    def _parse_date(self, datestr):
        return datetime.datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S")

    @property
    def date(self):
        return self._parse_date(self.data.date)

    @property
    def share_url(self):
        if self.data:
            return self.data.get('custom_fields', {}).get('share_url', [self.url_unlocalized])[0]

    @property
    def url_localized(self):
        if not self._url_localized:
            if self.data:
                url_parsed = list(urlparse(self.data['url']))
                url_parsed[2] = locale_path(url_parsed[2], self.country, self.lang)
                self._url_localized = urlunparse(url_parsed)
        return self._url_localized

    @property
    def url_unlocalized(self):
        if not self._url_unlocalized:
            if self.data:
                url_parsed = list(urlparse(self.data['url']))
                url_parsed[2] = strip_path(url_parsed[2])[2]
                self._url_unlocalized = urlunparse(url_parsed)
        return self._url_unlocalized

def get_posts(wp_path='/', wp_query=None, lang=None, country=None):
    # TODO: Caching
    mapping = settings.WORDPRESS_MAPPING
    site_id = Site.objects.get_current().id

    if not wp_query:
        wp_query = {}
    wp_query['json'] = 1

    parsed_url = list(urlparse(urljoin(mapping[site_id]['host'], wp_path)))
    parsed_url[4] = urlencode(wp_query)

    r = requests.get(urlunparse(parsed_url),
                     timeout=REQUEST_TIMEOUT_SEC)
    json_data = json.loads(r.content)
    if 'post' in json_data:
        json_data['post'] = Post(json_data['post'], lang, country)
    if 'posts' in json_data:
        json_data['posts'] = [Post(pd, lang, country) for pd in json_data['posts']]
    return json_data

def mirror(request, wp_path='/'):
    #namespace = resolve(request.path).namespace
    mapping = settings.WORDPRESS_MAPPING
    site_id = Site.objects.get_current().id

    get_params = dict(request.GET.iteritems())
    api_response = get_posts(wp_path, get_params, lang=getattr(request, 'LANGUAGE_LANG', None), country=getattr(request, 'LANGUAGE_COUNTRY', None))
    context = api_response

    if api_response.get('status') == 'ok':
        template = 'archive.html'
        if 'post' in api_response:
            template = 'single.html'
        if 'pages' in api_response:
            max_pages = api_response['pages']
            cur_page = int(request.GET.get('page', 1))
            cur_params = request.GET.copy()
            if cur_page > 1:
                cur_params['page'] = cur_page - 1
                context['newer_posts_page'] = request.path + '?' + cur_params.urlencode()
            if cur_page < max_pages:
                cur_params['page'] = cur_page + 1
                context['older_posts_page'] = request.path + '?' + cur_params.urlencode()

        return render_to_response(mapping[site_id]['templates'] + template,
                context,
                context_instance=RequestContext(request))
    raise Http404
