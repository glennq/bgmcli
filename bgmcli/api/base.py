class BangumiBase(object):
    """Interface for all element and collection classes"""

    @classmethod
    def from_html(cls, *args, **kwargs):
        """Parse HTML of certain page to create element object"""
        raise NotImplementedError

    @classmethod
    def from_soup(cls, *args, **kwargs):
        """Process parsed HTML of certain page to create element object"""
        raise NotImplementedError

    @classmethod
    def deserialize(cls, text):
        """Create element object from serialized form"""
        raise NotImplementedError

    def serialize(self):
        """Transform to a serializable from"""
        raise NotImplementedError