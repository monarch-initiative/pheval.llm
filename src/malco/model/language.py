from enum import Enum


class Language(Enum):
    CS = "Czech"
    DE = "German"
    ES = "Spanish"
    FR = "French"
    IT = "Italian"
    JA = "Japanese"
    NL = "Dutch"
    TR = "Turkish"
    ZH = "Chinese"
    EN = "English"
    ALL = "All"

    @classmethod
    def from_short_name(cls, short_name: str):
        """Create an enumeration instance from the uppercase short name."""
        try:
            return cls[short_name.upper()]
        except KeyError:
            raise ValueError(f"Short name '{short_name}' is not valid.")

    def long_name(self) -> str:
        """Return the long name of the enumeration."""
        return self.value
