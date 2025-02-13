class MongoDBUserNotFound(Exception):
    """
    Exception raised when a user is not found in MongoDB.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
