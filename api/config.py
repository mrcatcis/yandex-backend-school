import enum
from os import getenv


class Mode(enum.Enum):
    DEBUG = "DEBUG"
    PRODUCTION = "PRODUCTION"


MODE = Mode(getenv("MODE"))


STRING_SIZE = 256

POSTGRES_USER = getenv("POSTGRES_USER")
POSTGRES_PASSWORD = getenv("POSTGRES_PASSWORD")
DATABASE_HOST = getenv("DATABASE_HOST")
DATABASE_PORT = getenv("DATABASE_PORT")
POSTGRES_DB = getenv("POSTGRES_DB")
