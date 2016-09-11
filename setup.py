import sys
from setuptools import setup, find_packages

__version__ = '0.0.1a'

if len(set(('test', 'easy_install')).intersection(sys.argv)) > 0:
    import setuptools

tests_require = ['pytest']

extra_setuptools_args = {}

setup(
    name="choroshape",
    version=__version__,
    description="A Python package for easy creation of county choropleth maps.",
    maintainer='Rachel Asquith',
    maintainer_email='rachel.asquith@gmail.com',
    url='http://github.com/rasquith/choroshape',
    packages=find_packages(exclude=['choroshape/tests']),
    install_requires=['six', 'geopandas', 'pandas', 'numpy', 'matplotlib'],
    tests_require=tests_require,
    license='MIT',
    download_url='https://github.com/rasquith/choroshape/archive/%s.tar.gz' % __version__,
    **extra_setuptools_args
)