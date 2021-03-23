from requests.exceptions import ConnectionError
#unrecoverable server error
class UnrecoverableError(Exception):
    pass

# recoverable -> get token ->repeat
# codes 1,2,3
class CredentialsError(Exception):
    pass

class ExpiredTokenError(Exception):
    pass

# recoverable -> close shift -> repeat
class ShiftExceededTime(Exception):
    pass

# unrecoverable until next payment
class ShiftAlreadyClosed(Exception):
    pass

# unrecoverable until next payment
class OpenedShiftNotFound(Exception):
    pass

# recoverable -> change UID -> repeat
class ReceiptUniqueNumDuplication(Exception):
    pass


class UnresolvedCommand(Exception):
    pass
