"""This is an unofficial API for Bangumi.tv, implemented by sending http
requests and parsing responses. This Library is NOT supposed to be
thread-safe
"""

__all__ = ['BangumiSession']
 
from .session import BangumiSession