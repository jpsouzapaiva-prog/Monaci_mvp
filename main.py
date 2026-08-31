from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from flask import Flask, render_template, request, jsonify
from datetime import datetime

from cardapio import cardapio


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///monaci.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ============================================================
# CONFIGURACOES DO CARDAPIO
# ============================================================

categorias_produtos = [
    "hot_dog",
    "sanduiches",
    "pizza_brotinho",
    "acai",
    "refrigerantes",
    "sucos",
    "sucos_energeticos"
]


molhos_hot_dog_permitidos = [
    "Todos os molhos",
    "Sem mostarda",
    "Sem maionese",
    "Só queijo",
    "Sem molho"
]


preparos_suco_permitidos = [
    "Sem leite",
    "Com leite"
]


acucar_suco_permitidos = [
    "Com açúcar",
    "Sem açúcar"
]


# ============================================================
# PRODUTOS DO CARDAPIO
# ============================================================

produtos = []


for categoria in categorias_produtos:

    itens_categoria = cardapio.get(
        categoria,
        []
    )

    for produto in itens_categoria:

        produto_copia = produto.copy()

        produto_copia["categoria"] = categoria

        produtos.append(
            produto_copia
        )


# ============================================================
# INDICE SEGURO DE PRODUTOS
# ============================================================

produtos_por_id = {}


for produto in produtos:

    produto_id = produto.get(
        "id"
    )

    if produto_id:

        produtos_por_id[
            produto_id
        ] = produto


# ============================================================
# ADICIONAIS DOS SANDUICHES
# ============================================================

adicionais_sanduiches_por_nome = {}


for adicional in cardapio.get(
    "adicionais_sanduiches",
    []
):

    nome = adicional.get(
        "nome"
    )

    if nome:

        adicionais_sanduiches_por_nome[
            nome
        ] = float(
            adicional.get(
                "preco",
                0
            )
        )


# ============================================================
# MODELOS DO BANCO DE DADOS
# ============================================================

class Pedido(db.Model):

    __tablename__ = "pedidos"

    id = db.Column(
        db.Integer,
        primary_key=True
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
        default="NOVO"
    )

    data_hora = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    hora_inicio_preparo = db.Column(
        db.DateTime,
        nullable=True
    )

    hora_pronto = db.Column(
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

    itens = db.relationship(
        "ItemPedido",
        backref="pedido",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="ItemPedido.id"
    )


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
        nullable=False
    )

    produto_id = db.Column(
        db.String(100),
        nullable=False
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


# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def texto_seguro(
    valor,
    limite=300
):

    if valor is None:

        return ""

    texto = str(
        valor
    ).strip()

    return texto[
        :limite
    ]


def buscar_produto(
    produto_id
):

    return produtos_por_id.get(
        produto_id
    )


def validar_quantidade(
    valor
):

    try:

        quantidade = int(
            valor
        )

    except (
        TypeError,
        ValueError
    ):

        return None


    if quantidade < 1:

        return None


    if quantidade > 50:

        return None


    return quantidade


def normalizar_texto(
    texto
):

    substituicoes = {

        "á": "a",
        "à": "a",
        "ã": "a",
        "â": "a",
        "ä": "a",

        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",

        "í": "i",
        "ì": "i",
        "î": "i",
        "ï": "i",

        "ó": "o",
        "ò": "o",
        "õ": "o",
        "ô": "o",
        "ö": "o",

        "ú": "u",
        "ù": "u",
        "û": "u",
        "ü": "u",

        "ç": "c"
    }


    resultado = str(
        texto or ""
    ).lower().strip()


    for origem, destino in substituicoes.items():

        resultado = resultado.replace(
            origem,
            destino
        )


    return resultado


def formatar_hora(
    valor
):

    if valor is None:

        return ""

    return valor.strftime(
        "%H:%M:%S"
    )


def pedido_para_dict(
    pedido
):

    return {

        "numero":
            pedido.id,

        "numero_formatado":
            str(
                pedido.id
            ).zfill(
                4
            ),

        "cliente":
            pedido.cliente,

        "tipo":
            pedido.tipo,

        "endereco":
            pedido.endereco or "",

        "pagamento":
            pedido.pagamento or "",

        "total":
            float(
                pedido.total
            ),

        "itens": [
            item_para_dict(
                item
            )
            for item in pedido.itens
        ],

        "status":
            pedido.status,

        "data_hora":
            pedido.data_hora.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),

        "hora_inicio_preparo":
            formatar_hora(
                pedido.hora_inicio_preparo
            ),

        "hora_pronto":
            formatar_hora(
                pedido.hora_pronto
            ),

        "hora_saida_entrega":
            formatar_hora(
                pedido.hora_saida_entrega
            ),

        "hora_finalizado":
            formatar_hora(
                pedido.hora_finalizado
            )
    }


def item_para_dict(
    item
):

    return {

        "id":
            item.produto_id,

        "nome":
            item.nome,

        "categoria":
            item.categoria,

        "setor":
            item.setor,

        "preco":
            float(
                item.preco
            ),

        "quantidade":
            item.quantidade,

        "retirados":
            item.retirados or [],

        "adicionais":
            item.adicionais or [],

        "valorAdicionais":
            float(
                item.valor_adicionais
            ),

        "molho":
            item.molho or "",

        "preparoSuco":
            item.preparo_suco or "",

        "acucarSuco":
            item.acucar_suco or "",

        "observacao":
            item.observacao or "",

        "subtotal":
            float(
                item.subtotal
            )
    }


# ============================================================
# INGREDIENTES QUE PODEM SER RETIRADOS
# ============================================================

def ingredientes_retiraveis(
    produto
):

    ingredientes = produto.get(
        "ingredientes",
        []
    )


    categoria = produto.get(
        "categoria"
    )


    if not isinstance(
        ingredientes,
        list
    ):

        return []


    if categoria == "hot_dog":

        permitidos = [
            "milho",
            "milho verde",
            "azeitona"
        ]


        return [

            ingrediente

            for ingrediente
            in ingredientes

            if normalizar_texto(
                ingrediente
            )
            in permitidos
        ]


    if categoria == "sanduiches":

        ingredientes_estruturais = [

            "pao bola",
            "pao de caixa",
            "pao de forma",

            "carne de hamburguer",
            "1 carne de hamburguer",
            "2 carnes de hamburguer",

            "carne",
            "2 carnes"
        ]


        return [

            ingrediente

            for ingrediente
            in ingredientes

            if normalizar_texto(
                ingrediente
            )
            not in ingredientes_estruturais
        ]


    if categoria == "pizza_brotinho":

        return [

            ingrediente

            for ingrediente
            in ingredientes

            if normalizar_texto(
                ingrediente
            )
            == "ovo de codorna"
        ]


    if categoria == "acai":

        return [

            ingrediente

            for ingrediente
            in ingredientes

            if normalizar_texto(
                ingrediente
            )
            != "acai"
        ]


    return []


# ============================================================
# VALIDAR INGREDIENTES RETIRADOS
# ============================================================

def validar_retirados(
    produto,
    retirados_recebidos
):

    if not isinstance(
        retirados_recebidos,
        list
    ):

        return []


    permitidos = ingredientes_retiraveis(
        produto
    )


    permitidos_normalizados = {

        normalizar_texto(
            ingrediente
        ): ingrediente

        for ingrediente
        in permitidos
    }


    retirados_validos = []


    for ingrediente in retirados_recebidos:

        nome_normalizado = normalizar_texto(
            ingrediente
        )


        if (
            nome_normalizado
            in permitidos_normalizados
        ):

            ingrediente_oficial = (
                permitidos_normalizados[
                    nome_normalizado
                ]
            )


            if (
                ingrediente_oficial
                not in retirados_validos
            ):

                retirados_validos.append(
                    ingrediente_oficial
                )


    return retirados_validos


# ============================================================
# VALIDAR ADICIONAIS
# ============================================================

def validar_adicionais(
    produto,
    adicionais_recebidos
):

    adicionais_validos = []

    valor_adicionais = 0.0


    if not isinstance(
        adicionais_recebidos,
        list
    ):

        return (
            None,
            0.0,
            "Formato dos adicionais invalido."
        )


    categoria = produto.get(
        "categoria"
    )


    nomes_processados = set()


    for adicional_recebido in adicionais_recebidos:


        if isinstance(
            adicional_recebido,
            dict
        ):

            nome = texto_seguro(
                adicional_recebido.get(
                    "nome"
                ),
                100
            )

        else:

            nome = texto_seguro(
                adicional_recebido,
                100
            )


        if not nome:

            return (
                None,
                0.0,
                "Adicional invalido."
            )


        if nome in nomes_processados:

            continue


        preco_oficial = None


        if categoria == "hot_dog":

            adicionais_produto = produto.get(
                "adicionais",
                {}
            )


            if (
                isinstance(
                    adicionais_produto,
                    dict
                )
                and nome
                in adicionais_produto
            ):

                preco_oficial = float(
                    adicionais_produto[
                        nome
                    ]
                )


        elif categoria == "sanduiches":

            if (
                nome
                in adicionais_sanduiches_por_nome
            ):

                preco_oficial = float(
                    adicionais_sanduiches_por_nome[
                        nome
                    ]
                )


        if preco_oficial is None:

            return (
                None,
                0.0,
                "Adicional invalido."
            )


        adicionais_validos.append({

            "nome":
                nome,

            "preco":
                round(
                    preco_oficial,
                    2
                )
        })


        valor_adicionais += (
            preco_oficial
        )


        nomes_processados.add(
            nome
        )


    return (

        adicionais_validos,

        round(
            valor_adicionais,
            2
        ),

        None
    )


# ============================================================
# MONTAR ITEM SEGURO
# ============================================================

def montar_item_seguro(
    item_recebido
):

    if not isinstance(
        item_recebido,
        dict
    ):

        return (
            None,
            "Item invalido."
        )


    produto_id = texto_seguro(
        item_recebido.get(
            "id"
        ),
        100
    )


    produto = buscar_produto(
        produto_id
    )


    if not produto:

        return (
            None,
            "Produto nao encontrado."
        )


    quantidade = validar_quantidade(
        item_recebido.get(
            "quantidade"
        )
    )


    if quantidade is None:

        return (
            None,
            "Quantidade invalida."
        )


    retirados = validar_retirados(
        produto,
        item_recebido.get(
            "retirados",
            []
        )
    )


    (
        adicionais,
        valor_adicionais,
        erro_adicional
    ) = validar_adicionais(

        produto,

        item_recebido.get(
            "adicionais",
            []
        )
    )


    if erro_adicional:

        return (
            None,
            erro_adicional
        )


    categoria = produto.get(
        "categoria",
        ""
    )


    molho = ""


    if categoria == "hot_dog":

        molho_recebido = texto_seguro(
            item_recebido.get(
                "molho"
            ),
            50
        )


        if (
            molho_recebido
            in molhos_hot_dog_permitidos
        ):

            molho = molho_recebido

        else:

            molho = (
                "Todos os molhos"
            )


    preparo_suco = ""


    if categoria == "sucos":

        preparo_recebido = texto_seguro(
            item_recebido.get(
                "preparoSuco"
            ),
            30
        )


        if (
            preparo_recebido
            in preparos_suco_permitidos
        ):

            preparo_suco = (
                preparo_recebido
            )

        else:

            preparo_suco = (
                "Sem leite"
            )


    acucar_suco = ""


    if categoria == "sucos":

        acucar_recebido = texto_seguro(
            item_recebido.get(
                "acucarSuco"
            ),
            30
        )


        if (
            acucar_recebido
            in acucar_suco_permitidos
        ):

            acucar_suco = (
                acucar_recebido
            )

        else:

            acucar_suco = (
                "Com açúcar"
            )


    observacao = texto_seguro(
        item_recebido.get(
            "observacao"
        ),
        300
    )


    preco_produto = float(
        produto.get(
            "preco",
            0
        )
    )


    preco_unitario = (
        preco_produto
        + valor_adicionais
    )


    subtotal = (
        preco_unitario
        * quantidade
    )


    item_seguro = {

        "id":
            produto.get(
                "id"
            ),

        "nome":
            produto.get(
                "nome",
                ""
            ),

        "categoria":
            produto.get(
                "categoria",
                ""
            ),

        "setor":
            produto.get(
                "setor",
                ""
            ),

        "preco":
            round(
                preco_produto,
                2
            ),

        "quantidade":
            quantidade,

        "retirados":
            retirados,

        "adicionais":
            adicionais,

        "valorAdicionais":
            valor_adicionais,

        "molho":
            molho,

        "preparoSuco":
            preparo_suco,

        "acucarSuco":
            acucar_suco,

        "observacao":
            observacao,

        "subtotal":
            round(
                subtotal,
                2
            )
    }


    return (
        item_seguro,
        None
    )


# ============================================================
# PAGINA INICIAL
# ============================================================

@app.route("/")
def inicio():

    return render_template(
        "index.html",
        produtos=produtos
    )


# ============================================================
# PAINEL DE PRODUCAO
# ============================================================

@app.route("/painel")
def painel():

    return render_template(
        "painel.html"
    )


# ============================================================
# CRIAR PEDIDO
# ============================================================

@app.route(
    "/pedidos",
    methods=["POST"]
)
def criar_pedido():

    dados = request.get_json(
        silent=True
    )


    if not isinstance(
        dados,
        dict
    ):

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Nenhum dado recebido."
        }), 400


    cliente = texto_seguro(
        dados.get(
            "cliente"
        ),
        100
    )


    if cliente == "":

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Nome do cliente nao informado."
        }), 400


    tipo_pedido = texto_seguro(
        dados.get(
            "tipo",
            "retirada"
        ),
        20
    )


    if tipo_pedido not in [
        "retirada",
        "entrega"
    ]:

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Tipo de pedido invalido."
        }), 400


    endereco = texto_seguro(
        dados.get(
            "endereco"
        ),
        500
    )


    if (
        tipo_pedido == "entrega"
        and endereco == ""
    ):

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Endereco de entrega nao informado."
        }), 400


    pagamento = texto_seguro(
        dados.get(
            "pagamento"
        ),
        200
    )


    itens_recebidos = dados.get(
        "itens",
        []
    )


    if not isinstance(
        itens_recebidos,
        list
    ):

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Formato dos itens invalido."
        }), 400


    if len(
        itens_recebidos
    ) == 0:

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Pedido sem produtos."
        }), 400


    if len(
        itens_recebidos
    ) > 100:

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Quantidade de itens acima do permitido."
        }), 400


    itens_seguros = []

    total_calculado = 0.0


    for item_recebido in itens_recebidos:

        (
            item_seguro,
            erro
        ) = montar_item_seguro(
            item_recebido
        )


        if erro:

            return jsonify({
                "sucesso": False,
                "mensagem":
                    erro
            }), 400


        itens_seguros.append(
            item_seguro
        )


        total_calculado += (
            item_seguro[
                "subtotal"
            ]
        )


    total_calculado = round(
        total_calculado,
        2
    )


    try:

        novo_pedido = Pedido(

            cliente=
                cliente,

            tipo=
                tipo_pedido,

            endereco=
                endereco,

            pagamento=
                pagamento,

            total=
                total_calculado,

            status=
                "NOVO",

            data_hora=
                datetime.now()
        )


        db.session.add(
            novo_pedido
        )


        db.session.flush()


        for item in itens_seguros:

            novo_item = ItemPedido(

                pedido_id=
                    novo_pedido.id,

                produto_id=
                    item["id"],

                nome=
                    item["nome"],

                categoria=
                    item["categoria"],

                setor=
                    item["setor"],

                preco=
                    item["preco"],

                quantidade=
                    item["quantidade"],

                retirados=
                    item["retirados"],

                adicionais=
                    item["adicionais"],

                valor_adicionais=
                    item[
                        "valorAdicionais"
                    ],

                molho=
                    item["molho"],

                preparo_suco=
                    item[
                        "preparoSuco"
                    ],

                acucar_suco=
                    item[
                        "acucarSuco"
                    ],

                observacao=
                    item["observacao"],

                subtotal=
                    item["subtotal"]
            )


            db.session.add(
                novo_item
            )


        db.session.commit()


    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Erro ao salvar pedido no banco."
        )

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Nao foi possivel salvar o pedido."
        }), 500


    pedido_dict = pedido_para_dict(
        novo_pedido
    )


    print(
        "\n"
    )


    print(
        "=" * 55
    )


    print(
        "PEDIDO #",
        pedido_dict[
            "numero_formatado"
        ]
    )


    print(
        "CLIENTE:",
        pedido_dict[
            "cliente"
        ]
    )


    print(
        "TIPO:",
        pedido_dict[
            "tipo"
        ]
    )


    if pedido_dict[
        "endereco"
    ]:

        print(
            "ENDERECO:",
            pedido_dict[
                "endereco"
            ]
        )


    print(
        "PAGAMENTO:",
        pedido_dict[
            "pagamento"
        ]
    )


    print(
        "TOTAL CALCULADO PELO SERVIDOR: R$",
        f'{pedido_dict["total"]:.2f}'
    )


    print(
        "-" * 55
    )


    for item in pedido_dict[
        "itens"
    ]:

        print(
            item.get(
                "quantidade",
                1
            ),
            "x",
            item.get(
                "nome",
                ""
            )
        )


        molho = item.get(
            "molho",
            ""
        )


        if molho:

            print(
                "  Molho:",
                molho
            )


        retirados = item.get(
            "retirados",
            []
        )


        if retirados:

            print(
                "  Retirar:",
                ", ".join(
                    retirados
                )
            )


        adicionais = item.get(
            "adicionais",
            []
        )


        if adicionais:

            print(
                "  Adicionais:"
            )


            for adicional in adicionais:

                print(
                    "   +",
                    adicional.get(
                        "nome",
                        ""
                    ),
                    "R$",
                    f'{adicional.get("preco", 0):.2f}'
                )


        preparo_suco = item.get(
            "preparoSuco",
            ""
        )


        if preparo_suco:

            print(
                " ",
                preparo_suco
            )


        acucar_suco = item.get(
            "acucarSuco",
            ""
        )


        if acucar_suco:

            print(
                " ",
                acucar_suco
            )


        observacao = item.get(
            "observacao",
            ""
        )


        if observacao:

            print(
                "  OBS:",
                observacao
            )


        print(
            "  Subtotal: R$",
            f'{item.get("subtotal", 0):.2f}'
        )


    print(
        "-" * 55
    )


    print(
        "STATUS:",
        pedido_dict[
            "status"
        ]
    )


    print(
        "HORARIO:",
        pedido_dict[
            "data_hora"
        ]
    )


    print(
        "=" * 55
    )


    return jsonify({

        "sucesso":
            True,

        "numero":
            novo_pedido.id,

        "numero_formatado":
            str(
                novo_pedido.id
            ).zfill(
                4
            ),

        "total":
            total_calculado,

        "mensagem":
            "Pedido recebido com sucesso."
    })


# ============================================================
# LISTAR PEDIDOS
# ============================================================

@app.route(
    "/pedidos",
    methods=["GET"]
)
def listar_pedidos():

    pedidos_banco = Pedido.query.order_by(
        Pedido.id.asc()
    ).all()


    return jsonify([

        pedido_para_dict(
            pedido
        )

        for pedido in pedidos_banco
    ])


# ============================================================
# ALTERAR STATUS
# ============================================================

@app.route(
    "/pedidos/<int:numero>/status",
    methods=["PUT"]
)
def alterar_status(
    numero
):

    dados = request.get_json(
        silent=True
    )


    if not isinstance(
        dados,
        dict
    ):

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Dados invalidos."
        }), 400


    novo_status = texto_seguro(
        dados.get(
            "status"
        ),
        50
    )


    status_permitidos = [
        "NOVO",
        "EM PREPARO",
        "PRONTO",
        "SAIU PARA ENTREGA",
        "FINALIZADO"
    ]


    if (
        novo_status
        not in status_permitidos
    ):

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Status invalido."
        }), 400


    pedido = db.session.get(
        Pedido,
        numero
    )


    if pedido is None:

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Pedido nao encontrado."
        }), 404


    agora = datetime.now()


    if (
        novo_status
        == "EM PREPARO"
    ):

        pedido.status = (
            "EM PREPARO"
        )

        pedido.hora_inicio_preparo = (
            agora
        )


    elif (
        novo_status
        == "PRONTO"
    ):

        if (
            pedido.tipo
            == "retirada"
        ):

            pedido.status = (
                "PRONTO PARA RETIRADA"
            )

        else:

            pedido.status = (
                "PRONTO PARA ENTREGA"
            )


        pedido.hora_pronto = (
            agora
        )


    elif (
        novo_status
        == "SAIU PARA ENTREGA"
    ):

        if (
            pedido.tipo
            != "entrega"
        ):

            return jsonify({
                "sucesso": False,
                "mensagem":
                    "Pedido de retirada nao pode sair para entrega."
            }), 400


        if (
            pedido.status
            != "PRONTO PARA ENTREGA"
        ):

            return jsonify({
                "sucesso": False,
                "mensagem":
                    "O pedido precisa estar pronto antes de sair para entrega."
            }), 400


        pedido.status = (
            "SAIU PARA ENTREGA"
        )

        pedido.hora_saida_entrega = (
            agora
        )


    elif (
        novo_status
        == "FINALIZADO"
    ):

        pedido.status = (
            "FINALIZADO"
        )

        pedido.hora_finalizado = (
            agora
        )


    elif (
        novo_status
        == "NOVO"
    ):

        pedido.status = (
            "NOVO"
        )


    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Erro ao atualizar status do pedido."
        )

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Nao foi possivel atualizar o status."
        }), 500


    return jsonify({

        "sucesso":
            True,

        "mensagem":
            "Status atualizado.",

        "status":
            pedido.status
    })


# ============================================================
# INICIAR SISTEMA
# ============================================================

if __name__ == "__main__":

    print(
        "=== MONACI 1.0 ==="
    )


    print(
        "Produtos carregados:",
        len(
            produtos
        )
    )


    app.run(
        debug=True
    )
