import datetime

class PullRequest():
    """Simple object wrapper for a PullRequest data dict, with some simple properties"""
    def __init__(
            self, 
            pull_request: dict) -> None:
        """"""
        self.raw = pull_request

    @property
    def created(self) -> str:
        """Get the creation date
        
        Returns:
            str: ISO formatted datetime string
        """
        return self.raw.get('created_at')
    
    @property
    def updated(self) -> str:
        """Get the updated date
        
        Returns:
            str: ISO formatted datetime string
        """
        return self.raw.get('updated_at')
    
    @property
    def age(self) -> str:
        created = datetime.datetime.fromisoformat(self.created).replace(tzinfo=None)

        if self.isMerged():
            now = datetime.datetime.fromisoformat(self.merged)
        elif self.isClosed():
            now = datetime.datetime.fromisoformat(self.closed)
        else:
            now = datetime.datetime.now()

        now = now.replace(tzinfo=None)
        
        diff = now - created

        days = diff.days
        hours = diff.seconds / 3600.0

        return f'{abs(days):4d}d {hours:4.1f}h'
    
    @property
    def merged(self) -> str | None:
        """Get the merged date
        
        Returns:
            str | None: ISO formatted datetime string, or None if not merged
        """
        return self.raw.get('merged_at')

    @property
    def closed(self) -> str | None:
        """Get the closed date
        
        Returns:
            str | None: ISO formatted datetime string, or None if not closed
        """
        return self.raw.get('merged_at')

    def isClosed(self) -> bool:
        """Check if PullRequest is closed
        
        Returns:
            bool: True if closed, False if open
        """
        return False if self.closed is None else True
    
    def isMerged(self) -> bool:
        """Check if PullRequest is closed
        
        Returns:
            bool: True if closed, False if open
        """
        return False if self.merged is None else True
    
    @property
    def number(self) -> str:
        """Get the PullRequest's number
        
        Returns:
            str: PullRequest ID number
        """
        return str(self.raw.get('number'))
    
    @property
    def state(self) -> str:
        """Get the PullRequet's state
        
        Returns:
            str: State of the Pull Request, open or closed
        """
        return self.raw.get('state')
    
    @property
    def title(self) -> str:
        """Get the title of the Pull Request
        
        Returns:
            str: Title of pull request
        """
        return self.raw.get('title')
    
    @property
    def short_title(self, max_len: int = 40) -> str:
        """Get a shortened title of the Pull Request
        
        Returns:
            str: Sort Title of pull request
        """
        title = self.title
        if len(title) > max_len:
            title = title[:max_len] + '>'

        return title