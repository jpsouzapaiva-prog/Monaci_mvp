import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# CAMINHOS DO PROJETO
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent


INSTANCE_DIR = BASE_DIR / "instance"


INSTANCE_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# CARREGAR VARIAVEIS LOCAIS
# ============================================================

load_dotenv(
    BASE_DIR / ".env"
)


# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def obter_variavel_ambiente(
    nome,
    padrao=None
):

    return os.getenv(
        nome,
        padrao
    )


# ============================================================
# CONFIGURACAO BASE
# ============================================================

class Config:

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JSON_SORT_KEYS = False

    MAX_CONTENT_LENGTH = (
        2 * 1024 * 1024
    )

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = "Lax"

    TESTING = False

    DEBUG = False


# ============================================================
# DESENVOLVIMENTO
# ============================================================

class DevelopmentConfig(
    Config
):

    DEBUG = True

    SECRET_KEY = obter_variavel_ambiente(
        "SECRET_KEY",
        "chave-local-temporaria-monaci"
    )

    SQLALCHEMY_DATABASE_URI = obter_variavel_ambiente(
        "DATABASE_URL",
        f"sqlite:///{INSTANCE_DIR / 'monaci.db'}"
    )

    SESSION_COOKIE_SECURE = False


# ============================================================
# PRODUCAO
# ============================================================

class ProductionConfig(
    Config
):

    DEBUG = False

    SESSION_COOKIE_SECURE = True


# ============================================================
# TESTES
# ============================================================

class TestingConfig(
    Config
):

    TESTING = True

    DEBUG = False

    SECRET_KEY = "chave-apenas-para-testes"

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///:memory:"
    )

    SESSION_COOKIE_SECURE = False


# ============================================================
# VALIDAR PRODUCAO
# ============================================================

def validar_configuracao_producao():

    secret_key = obter_variavel_ambiente(
        "SECRET_KEY"
    )

    database_url = obter_variavel_ambiente(
        "DATABASE_URL"
    )


    if not secret_key:

        raise RuntimeError(
            "SECRET_KEY obrigatoria em producao."
        )


    if not database_url:

        raise RuntimeError(
            "DATABASE_URL obrigatoria em producao."
        )


    ProductionConfig.SECRET_KEY = (
        secret_key
    )

    ProductionConfig.SQLALCHEMY_DATABASE_URI = (
        database_url
    )


# ============================================================
# ESCOLHER CONFIGURACAO
# ============================================================

def obter_configuracao():

    ambiente = obter_variavel_ambiente(
        "APP_ENV",
        "development"
    ).strip().lower()


    if ambiente == "production":

        validar_configuracao_producao()

        return ProductionConfig


    if ambiente == "testing":

        return TestingConfig


    return DevelopmentConfig