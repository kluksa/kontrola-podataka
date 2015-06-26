# -*- coding: utf-8 -*-
"""
Created on Wed May 27 10:28:43 2015

@author: DHMZ-Milic
"""
from setuptools import setup, find_packages


setup(
    name="kontrolapodataka",
    version="0.2.0",
    author="DHMZ",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests >= 2.5.3",
		"numpy >= 1.9.2rc1",
		"pandas >= 0.15.2",
		"matplotlib >= 1.4.3",
		"PyQt4 >= 4.11.3"
    ],
)