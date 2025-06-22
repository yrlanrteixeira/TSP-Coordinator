"""
Script to start a worker node.
"""

import sys
import os
import argparse
import logging

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from worker.worker import *
from config.default_config import DEFAULT_CONFIG 