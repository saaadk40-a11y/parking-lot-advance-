class ParkingSystemException(Exception):
    """Base exception for the parking system."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class DuplicateEntityException(ParkingSystemException):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)

class EntityNotFoundException(ParkingSystemException):
    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class SpotUnavailableException(ParkingSystemException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class IncompatibleSpotException(ParkingSystemException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class InvalidSessionOperationException(ParkingSystemException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class InvalidRateException(ParkingSystemException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class SpotOccupiedException(ParkingSystemException):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)