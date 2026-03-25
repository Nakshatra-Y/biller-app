import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = db_url or f"sqlite:///{os.path.join(BASE_DIR, 'biller.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        logger.warning("Using SQLite database. Data will be lost on restart. Please configure DATABASE_URL for PostgreSQL.")
    else:
        logger.info("Using PostgreSQL database.")


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevConfig,
    "production": ProdConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(env, DevConfig)

