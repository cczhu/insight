#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages
from setuptools.extension import Extension
from Cython.Distutils import build_ext
import numpy

requirements = []

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

ext_modules = [
    Extension("snapassist.sklearn_optics._optics_inner",
              ["./snapassist/sklearn_optics/_optics_inner.pyx"],
              include_dirs=[numpy.get_include()]),
]

setup(
    author="Chenchong Zhu",
    author_email='chenchong.zhu@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Insight project.",
    install_requires=requirements,
    license="BSD license",
    long_description=("Photo geolocation clustering project for Insight Data "
                      "Science Toronto"),
    include_package_data=True,
    keywords='snapassist',
    name='snapassist',
    packages=find_packages(include=['snapassist']),
    setup_requires=setup_requirements,
    test_suite='snapassist/tests',
    tests_require=test_requirements,
    url='https://github.com/cczhu/snapassist',
    version='0.1.0',
    zip_safe=False,
    cmdclass={'build_ext': build_ext},
    ext_modules=ext_modules,
)
