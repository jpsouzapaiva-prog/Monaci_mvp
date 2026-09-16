from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


# ============================================================
# INSTANCIA DO BANCO
# ============================================================

db = SQLAlchemy()


# ============================================================
# EMPRESA
# ============================================================

class Empresa(db.Model):

    __tablename__ = "empresas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(120),
        nullable=False
    )

    slug = db.Column(
        db.String(80),
        nullable=False,
        unique=True,
        index=True
    )

    ativa = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # --------------------------------------------------------
    # LOCALIZACAO DA EMPRESA / PONTO DE SAIDA DAS ENTREGAS
    # --------------------------------------------------------

    endereco = db.Column(
        db.String(500),
        nullable=False,
        default="",
        server_default=""
    )

    cep = db.Column(
        db.String(20),
        nullable=False,
        default="",
        server_default=""
    )

    cidade = db.Column(
        db.String(120),
        nullable=False,
        default="",
        server_default=""
    )

    uf = db.Column(
        db.String(2),
        nullable=False,
        default="",
        server_default=""
    )

    latitude = db.Column(
        db.Numeric(10, 7),
        nullable=True
    )

    longitude = db.Column(
        db.Numeric(10, 7),
        nullable=True
    )

    criada_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )


# ============================================================
# BAIRRO DE ENTREGA
# ============================================================

class BairroEntrega(db.Model):

    __tablename__ = "bairros_entrega"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "empresas.id"
        ),
        nullable=False,
        index=True
    )

    nome = db.Column(
        db.String(120),
        nullable=False
    )

    taxa = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    ativo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    empresa = db.relationship(
        "Empresa",
        backref=db.backref(
            "bairros_entrega",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    __table_args__ = (
        db.UniqueConstraint(
            "empresa_id",
            "nome",
            name="uq_bairro_entrega_empresa_nome"
        ),
    )


# ============================================================
# MOTOBOY
# ============================================================

class Motoboy(db.Model):

    __tablename__ = "motoboys"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "empresas.id"
        ),
        nullable=False,
        index=True
    )

    nome = db.Column(
        db.String(120),
        nullable=False
    )

    telefone = db.Column(
        db.String(30),
        nullable=False,
        default=""
    )

    login = db.Column(
        db.String(80),
        nullable=False
    )

    senha_hash = db.Column(
        db.String(255),
        nullable=False
    )

    ativo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # --------------------------------------------------------
    # LOCALIZACAO ATUAL DO MOTOBOY
    # --------------------------------------------------------

    latitude_atual = db.Column(
        db.Numeric(10, 7),
        nullable=True
    )

    longitude_atual = db.Column(
        db.Numeric(10, 7),
        nullable=True
    )

    localizacao_atualizada_em = db.Column(
        db.DateTime,
        nullable=True
    )

    criado_em = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    empresa = db.relationship(
        "Empresa",
        backref=db.backref(
            "motoboys",
            lazy=True
        )
    )

    __table_args__ = (
        db.UniqueConstraint(
            "empresa_id",
            "login",
            name="uq_motoboy_empresa_login"
        ),
    )


# ============================================================
# PEDIDO
# ============================================================

class Pedido(db.Model):

    __tablename__ = "pedidos"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    empresa_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "empresas.id"
        ),
        nullable=True,
        index=True
    )

    motoboy_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "motoboys.id"
        ),
        nullable=True,
        index=True
    )

    cliente = db.Column(
        db.String(100),
        nullable=False
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )

    endereco = db.Column(
        db.String(500),
        nullable=False,
        default=""
    )

    bairro_entrega = db.Column(
        db.String(120),
        nullable=False,
        default="",
        server_default=""
    )

    cep_entrega = db.Column(
        db.String(20),
        nullable=False,
        default="",
        server_default=""
    )

    cidade_entrega = db.Column(
        db.String(120),
        nullable=False,
        default="",
        server_default=""
    )

    uf_entrega = db.Column(
        db.String(2),
        nullable=False,
        default="",
        server_default=""
    )

    latitude_entrega = db.Column(
        db.Numeric(10, 7),
        nullable=True
    )

    longitude_entrega = db.Column(
        db.Numeric(10, 7),
        nullable=True
    )

    taxa_entrega = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0,
        server_default="0"
    )

    pagamento = db.Column(
        db.String(200),
        nullable=False,
        default=""
    )

    total = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="NOVO",
        index=True
    )

    data_hora = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        index=True
    )

    hora_inicio_preparo = db.Column(
        db.DateTime,
        nullable=True
    )

    hora_pronto = db.Column(
        db.DateTime,
        nullable=True
    )

    hora_aceite_entrega = db.Column(
        db.DateTime,
        nullable=True
    )

    hora_saida_entrega = db.Column(
        db.DateTime,
        nullable=True
    )

    hora_finalizado = db.Column(
        db.DateTime,
        nullable=True
    )

    empresa = db.relationship(
        "Empresa",
        backref=db.backref(
            "pedidos",
            lazy=True
        )
    )

    motoboy = db.relationship(
        "Motoboy",
        backref=db.backref(
            "pedidos",
            lazy=True
        )
    )

    itens = db.relationship(
        "ItemPedido",
        backref="pedido",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="ItemPedido.id"
    )


# ============================================================
# ITEM DO PEDIDO
# ============================================================

class ItemPedido(db.Model):

    __tablename__ = "itens_pedido"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "pedidos.id"
        ),
        nullable=False,
        index=True
    )

    produto_id = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    nome = db.Column(
        db.String(200),
        nullable=False
    )

    categoria = db.Column(
        db.String(100),
        nullable=False,
        default=""
    )

    setor = db.Column(
        db.String(100),
        nullable=False,
        default=""
    )

    preco = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    quantidade = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    retirados = db.Column(
        db.JSON,
        nullable=False,
        default=list
    )

    adicionais = db.Column(
        db.JSON,
        nullable=False,
        default=list
    )

    valor_adicionais = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )

    molho = db.Column(
        db.String(100),
        nullable=False,
        default=""
    )

    sabor_suco = db.Column(
        db.String(80),
        nullable=False,
        default="",
        server_default=""
    )

    preparo_suco = db.Column(
        db.String(50),
        nullable=False,
        default=""
    )

    acucar_suco = db.Column(
        db.String(50),
        nullable=False,
        default=""
    )

    observacao = db.Column(
        db.String(300),
        nullable=False,
        default=""
    )

    subtotal = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0
    )
