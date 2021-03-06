Django-wordpress-mirror
=======================

Django-wordpress-mirror gets blog post content from a wordpress server, and
returns this content via Django. This allows you to pour the blogs into the
templates you want, while using wordpress as the blog editor.

Installation
------------

To install wordpress_mirror:

- Add wordpress_mirror to INSTALLED_APPS
- Add the WORDPRESS_MAPPING variable to the settings. This is a dictionary
  with different site id's as the key (every site that has a 
  wordpress_mirror instance). The values are dictionaries containing the
  host name and the templates directory. For example:

```python
WORDPRESS_MAPPING = {2: {'host': 'http://localhost/mvb_be',
                         'templates': 'community/blog/',
                         },
                     7: {'host': 'http://localhost/mvb_nl',
                         'templates': 'nl_community/blog/',
                         },
                     }
```

- Add the wordpress_mirror urls.py. If there are multiple instances of 
  the wordpress_mirror app, you can use url namespaces:

```python
url(r'^blog/', include('wordpress_mirror.urls', namespace='my_blog', app_name='wordpress_mirror')),
```

- There need to be two templates in the template directory, *overview.html*
  and *detail.html*. Examples of these files can be found in 
  wordpress_mirror/templates/wordpress_mirror

- The wordpress server needs to have the JSON API plugin installed
  (http://wordpress.org/plugins/json-api/)

Author
------
San Gillis (<san.gillis@mobilevikings.com>)
