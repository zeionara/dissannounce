from enum import Enum


class Status(Enum):
    SUCCESSFUL = 'успешная'
    UNSUCCESSFUL = 'отрицательное решение'
    UNKNOWN = None

    @property
    def bool(self):
        match self:
            case Status.SUCCESSFUL:
                return True
            case Status.UNSUCCESSFUL:
                return False
            case _:
                return None
