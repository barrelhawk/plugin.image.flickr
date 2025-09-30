#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flickr Add-on Initialization Script
This is run once during installation to ensure compatibility
"""

import os
import sys
import shutil

# Get addon directory
addon_dir = os.path.dirname(os.path.abspath(__file__))

# Create required directories
required_dirs = [
    os.path.join(addon_dir, 'resources', 'lib'),
    os.path.join(addon_dir, 'resources', 'lib', 'api'),
    os.path.join(addon_dir, 'resources', 'lib', 'ui'),
    os.path.join(addon_dir, 'resources', 'lib', 'utils'),
]

# Create directories if they don't exist
for directory in required_dirs:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Create __init__.py files in each directory
for directory in required_dirs:
    init_file = os.path.join(directory, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Auto-generated __init__.py file for Flickr addon\n')

print("Flickr addon initialization complete.")