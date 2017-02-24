#!/usr/bin/env python
from setuptools import setup

setup(
    name='mflow_nodes',
    version="0.0.3",
    description="mflow nodes is a library for building processing nodes on top of an mflow stream.",
    author='Paul Scherrer Institute',
    author_email='andrej.babic@psi.ch',
    requires=["bottle", "mflow", "numpy", 'requests'],

    packages=['mflow_nodes',
              'mflow_nodes.processors',
              'mflow_nodes.rest_api',
              'mflow_nodes.stream_tools',
              'mflow_nodes.stream_tools.message_handlers',
              'mflow_nodes.test_tools'],

    scripts=['mflow_nodes/test_tools/mflow_generate_test_stream.py'],

    include_package_data=True
)
