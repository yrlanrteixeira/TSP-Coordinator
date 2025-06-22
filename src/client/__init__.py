"""
Client package for interacting with the distributed TSP system.
"""

from .client import TSPClient
from .problem_generator import TSPProblemGenerator

__all__ = ['TSPClient', 'TSPProblemGenerator'] 