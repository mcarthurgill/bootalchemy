from setuptools import setup, find_packages
import sys, os

version = '0.2'

here = os.path.abspath(os.path.dirname(__file__))
docs = os.path.join(here,'docs', 'source', 'index.rst')
DOCS = open(docs).read()
   
setup(name='bootalchemy',
      version=version,
      description="A package to create database entries from yaml using sqlalchemy.",
      long_description=DOCS,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Christopher Perkins',
      author_email='chris@percious.com',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
          'PyYAML',
          'SQLAlchemy',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
