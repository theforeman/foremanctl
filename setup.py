"""
Setup file
"""

# To use a consistent encoding
import codecs
import os

# Always prefer setuptools over distutils
from setuptools import setup, find_namespace_packages


def get_long_description():
    """
    Get the long description from the README file
    """
    here = os.path.abspath(os.path.dirname(__file__))

    with codecs.open(os.path.join(here, 'README.md'), encoding='utf-8') as readme:
        return readme.read()


setup(
    name='cli',
    version='0.0.1',
    license='GPL-2.0-only',
    description='packaging wrapper using ansible',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/theforeman/foreman-quadlet',
    author='The Foreman Project',
    author_email='foreman-dev@googlegroups.com',
    zip_safe=False,

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],

    keywords='foreman',

    packages=find_namespace_packages(include=['cli']),
    include_package_data=True,

    install_requires=[
        'cryptography',
        'obsah >= 1.1.0',
        'psycopg2',
    ],

    extras_require={
        'argcomplete': ['argcomplete'],
    },

    entry_points={
        'console_scripts': [
            'rop=cli:main',
        ],
    },
)
