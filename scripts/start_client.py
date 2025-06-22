"""
Script to start the client.
"""

import sys
import os
import argparse
import logging

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from client.client import *
from config.default_config import DEFAULT_CONFIG 