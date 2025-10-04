from faker import Faker
from sqlalchemy.orm.session import Session

from app.database.session import get_database_session, get_engine
from app.settings import get_app_settings
from tests.helpers import LazyLoader

faker = Faker()

lazy_session = LazyLoader[Session](
    lambda: get_database_session(get_engine(app_settings=get_app_settings()))
)
