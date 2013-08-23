#!/usr/bin/env python
from setuptools import (setup, find_packages)

LONG_DESCRIPTION = """

"""

setup(name='django-wordpress-mirror',
      version='0.0.1',
      description='',
      long_description=LONG_DESCRIPTION,
      author='San Gillis, VikingCo nv',
      author_email='san.gillis@mobilevikings.com',
      url='http://github.com/vikingco/django-wordpress-mirror',
      license='LICENSE',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python',
          'Operating System :: OS Independent',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Topic :: Software Development :: Internationalization',
      ],
)
