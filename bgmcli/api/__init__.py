"""This is an unofficial API for Bangumi.tv, implemented by sending http
requests and parsing responses. 
This Library is NOT supposed to be thread-safe, but it should be fine to use
multiple threads to retrieve data from Bangumi, as Requests, the underlying
library for sending HTTP requests is thread-safe.
"""

__all__ = ['BangumiSession']
 
from .session import BangumiSession