"""
Script to start the coordinator node.
"""

import sys
import os
import argparse
import logging

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from coordinator.coordinator import *
from config.default_config import DEFAULT_CONFIG 