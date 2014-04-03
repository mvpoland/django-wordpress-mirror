import datetime

from django.utils import simplejson as json
from django.contrib.sites.models import Site
from django.conf import settings
from django.shortcuts import render_to_response
from django.template.context import RequestContext

import requests


def overview(request, page='1', count='4', slug=''):
    """
    Blog overview
    """
    mapping = settings.WORDPRESS_MAPPING
    site_id = Site.objects.get_current().id

    # If it is the first page, we want one extra story, the latest one
    if page == '1':
        count = str(int(count) + 1)

    category = 'get_category_posts' if slug else '1'
    r = requests.get("%s?json=%s&count=%s&page=%s&slug=%s" %
                     (mapping[site_id]['host'], category, count, page, slug))
    json_data = json.loads(r.content)
    # Change the date to a python datetime.datetime object
    for post in json_data['posts']:
        post['date'] = datetime.datetime.strptime(post['date'],
                                                  "%Y-%m-%d %H:%M:%S")

    context = {'posts': json_data['posts'],
               'max_pages': unicode(json_data['pages']),
               'page': page,
               'slug': slug,
               }

    # Get optional category title
    if 'category' in json_data:
        context['title'] = json_data['category']['title']

    return render_to_response(mapping[site_id]['templates'] + 'overview.html',
                              context,
                              context_instance=RequestContext(request))


def category(request, slug):
    """
    View posts from given category
    """
    return overview(request, slug=slug)


def permalink(request, post_id):
    """
    View a single blogpost based on the post id
    """
    mapping = settings.WORDPRESS_MAPPING
    site_id = Site.objects.get_current().id

    r = requests.get("%s?json=get_post&post_id=%s" % (mapping[site_id]['host'],
                                                      post_id))
    json_data = json.loads(r.content)
    # Change the date to a python datetime.datetime object
    json_data['post']['date'] = \
        datetime.datetime.strptime(json_data['post']['date'],
                                   "%Y-%m-%d %H:%M:%S")

    context = {'json_data': json_data, }

    return render_to_response(mapping[site_id]['templates'] + 'detail.html',
                              context,
                              context_instance=RequestContext(request))


def detail(request, slug):
    """
    View a single blogpost based on the post slug
    """
    mapping = settings.WORDPRESS_MAPPING
    site_id = Site.objects.get_current().id

    r = requests.get("%s?json=get_post&slug=%s" % (mapping[site_id]['host'],
                                                   slug))
    json_data = json.loads(r.content)
    # Change the date to a python datetime.datetime object
    json_data['post']['date'] = \
        datetime.datetime.strptime(json_data['post']['date'],
                                   "%Y-%m-%d %H:%M:%S")

    context = {'json_data': json_data, }

    return render_to_response(mapping[site_id]['templates'] + 'detail.html',
                              context,
                              context_instance=RequestContext(request))
