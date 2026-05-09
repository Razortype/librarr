"""Model registry — importing this package registers all models with SQLAlchemy."""

from app.models import associations  # noqa: F401
from app.models.activity_log import ActivityLog  # noqa: F401
from app.models.author import Author  # noqa: F401
from app.models.book import Book  # noqa: F401
from app.models.download import Download  # noqa: F401
from app.models.edition import Edition  # noqa: F401
from app.models.grab import Grab  # noqa: F401
from app.models.integration_config import IntegrationConfig  # noqa: F401
from app.models.metadata_cache import MetadataCache  # noqa: F401
from app.models.quality_profile import QualityProfile  # noqa: F401
from app.models.series import Series  # noqa: F401
from app.models.setting import Setting  # noqa: F401
