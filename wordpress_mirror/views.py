import datetime
import re
import json

from django.core.cache import cache
from django.contrib.sites.models import Site
from django.conf import settings
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import Http404

from urlparse import urlparse, urlunparse, urljoin
from django.utils.http import urlencode

from freyja.core.localeurl.languages import sitelanguage

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
    def postdate(self):
        return self._parse_date(self.data.get('date'))

    @property
    def share_url(self):
        if self.data:
            return self.data.get('custom_fields', {}).get('share_url', [self.url_unlocalized])[0]

    @property
    def url_localized(self):
        if not self._url_localized:
            if self.data:
                url_parsed = list(urlparse(self.data['url']))
                url_parsed[2] = sitelanguage().locale_url(url_parsed[2], self.lang)
                self._url_localized = urlunparse(url_parsed)
        return self._url_localized

    @property
    def url_unlocalized(self):
        if not self._url_unlocalized:
            if self.data:
                url_parsed = list(urlparse(self.data['url']))
                url_parsed[2] = sitelanguage().path_without_locale(url_parsed[2])
                self._url_unlocalized = urlunparse(url_parsed)
        return self._url_unlocalized

    def custom_images(self):
        if self.data:
            attachments = dict([(att.get('id'), att) for att in self.data.get('attachments', [])])
            custom_images = {}
            for cfname, cfdata in self.data.get('custom_fields', {}).iteritems():
                if 0 < len(cfdata):
                    try:
                        if int(cfdata[0]) in attachments:
                            custom_images[cfname] = attachments[int(cfdata[0])]
                    except ValueError:
                        pass
            return custom_images


def allowed_path(path):
    """
    Check whether a path is allowed by the WORDPRESS_ALLOWED_PATHS setting.
    """
    allowed_paths = getattr(settings, 'WORDPRESS_ALLOWED_PATHS', None)

    # If the setting is not defined, all paths are allowable
    if not allowed_paths:
        return True

    return any(re.match(p, path) for p in allowed_paths)


def get_posts(wp_path='/', wp_query=None, lang=None, country=None, authenticate=False):
    # TODO: Caching
    mapping = settings.WORDPRESS_MAPPING
    site_id = Site.objects.get_current().id

    if not allowed_path(wp_path):
        return {}

    if not wp_query:
        wp_query = {}
    wp_query['json'] = 1

    # when we want to preview posts from WP we need to do a bit of magic
    if wp_path == '/' and authenticate and wp_query.get('p', None):
        wp_query['json'] = 'get_post'
        wp_query['id'] = wp_query.pop('p')

    parsed_url = list(urlparse(urljoin(mapping[site_id]['host'], wp_path)))
    parsed_url[4] = urlencode(wp_query)
    cookies = None
    s = requests.Session()
    if authenticate:
        cookies = cache.get(settings.WORDPRESS_COOKIES_KEY)
        if not cookies:
            mapping = settings.WORDPRESS_MAPPING
            site_id = Site.objects.get_current().id
            url = urljoin(mapping[site_id]['host'], "wp-login.php")
            post_data = {
                'log': settings.WORDPRESS_USERNAME,
                'pwd': settings.WORDPRESS_PASSWORD,
                'rememberme': 'forever'
            }
            s.get(urljoin(mapping[site_id]['host'], "wp-admin"))
            s.post(url,
                   timeout=REQUEST_TIMEOUT_SEC,
                   cookies=cookies,
                   data=post_data)
            cookies = s.cookies.get_dict()
            cache.set(settings.WORDPRESS_COOKIES_KEY, cookies, 60*60*24) # 24 hours
    r = s.get(urlunparse(parsed_url),
                     timeout=REQUEST_TIMEOUT_SEC,
                     cookies=cookies)
    if r.status_code != 200:
        return {}
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
    authenticate = request.user.is_authenticated() and request.user.is_staff
    api_response = get_posts(wp_path, get_params, lang=getattr(request, 'LANGUAGE_LANG', None),
            country=getattr(request, 'LANGUAGE_COUNTRY', None), authenticate=authenticate)
    context = api_response

    if api_response.get('status') == 'ok':
        template = 'archive.html'
        if 'post' in api_response:
            template = 'single.html'
        if 'pages' in api_response:
            max_pages = api_response['pages']

            # If no valid numeric page ID is set, raise a 404.
            try:
                cur_page = int(request.GET.get('page', 1))
            except ValueError:
                raise Http404

            cur_params = request.GET.copy()
            if cur_page > 1:
                cur_params['page'] = cur_page - 1
                context['newer_posts_page'] = request.path + '?' + cur_params.urlencode()
            if cur_page < max_pages:
                cur_params['page'] = cur_page + 1
                context['older_posts_page'] = request.path + '?' + cur_params.urlencode()
        if 's' in get_params:
            context['search_string'] = get_params['s']
        if 'count_total' in api_response:
            context['nr_posts'] = api_response['count_total']

        return render_to_response(
            mapping[site_id]['templates'] + template,
            context,
            context_instance=RequestContext(request))
    raise Http404
