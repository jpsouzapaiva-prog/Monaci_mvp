from flask import Flask, render_template, request, jsonify, session, redirect, url_for, render_template_string
from flask_migrate import Migrate
from datetime import datetime
import os
import hmac
from functools import wraps

from cardapio import cardapio
from config import obter_configuracao
from models import db, Empresa, Pedido, ItemPedido


# ============================================================
# APLICACAO
# ============================================================

app = Flask(__name__)

app.config.from_object(
    obter_configuracao()
)

db.init_app(
    app
)

migrate = Migrate(
    app,
    db
)


# ============================================================
# SEGURANCA DE SESSAO
# ============================================================

app.config.setdefault(
    "SESSION_COOKIE_HTTPONLY",
    True
)

app.config.setdefault(
    "SESSION_COOKIE_SAMESITE",
    "Lax"
)

app.config.setdefault(
    "PERMANENT_SESSION_LIFETIME",
    60 * 60 * 8
)


# ============================================================
# AUTENTICACAO DO PAINEL
# ============================================================

LOGIN_HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Monaci - Acesso ao painel</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .box {
            width: 100%;
            max-width: 390px;
            background: white;
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 12px 35px rgba(0,0,0,.10);
        }
        h1 { margin: 0 0 8px; font-size: 26px; }
        p { margin: 0 0 22px; color: #666; }
        label { display: block; margin-bottom: 8px; font-weight: 700; }
        input {
            width: 100%;
            padding: 13px 14px;
            border: 1px solid #ccc;
            border-radius: 10px;
            font-size: 16px;
        }
        button {
            width: 100%;
            margin-top: 16px;
            padding: 13px;
            border: 0;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
        }
        .erro {
            background: #fff0f0;
            border: 1px solid #efb4b4;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 14px;
        }
    </style>
</head>
<body>
    <div class="box">
        <h1>Painel Monaci</h1>
        <p>Acesso restrito à operação.</p>

        {% if erro %}
        <div class="erro">{{ erro }}</div>
        {% endif %}

        <form method="post">
            <label for="senha">Senha</label>
            <input
                id="senha"
                name="senha"
                type="password"
                autocomplete="current-password"
                required
                autofocus
            >
            <button type="submit">Entrar</button>
        </form>
    </div>
</body>
</html>
"""


def senha_painel_configurada():
    return os.getenv(
        "PAINEL_PASSWORD",
        ""
    ).strip()


def painel_autenticado():
    return session.get(
        "painel_autenticado"
    ) is True


def login_painel_obrigatorio(
    funcao
):

    @wraps(
        funcao
    )
    def wrapper(
        *args,
        **kwargs
    ):

        if not painel_autenticado():

            if request.path.startswith(
                "/pedidos"
            ):

                return jsonify({
                    "sucesso": False,
                    "mensagem":
                        "Autenticacao necessaria."
                }), 401

            return redirect(
                url_for(
                    "login"
                )
            )

        return funcao(
            *args,
            **kwargs
        )

    return wrapper


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
# EMPRESA PADRAO DO MVP
# ============================================================

EMPRESA_PADRAO_SLUG = "familia-monaci"


def buscar_empresa_padrao():
    """
    No MVP existe uma empresa operacional ativa.
    O navegador nao escolhe empresa_id: o backend resolve a empresa
    pelo slug configurado no servidor.
    """
    return Empresa.query.filter_by(
        slug=EMPRESA_PADRAO_SLUG,
        ativa=True
    ).first()


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

        "empresa_id":
            pedido.empresa_id,

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
# REGRAS DE TRANSICAO DE STATUS
# ============================================================

def validar_transicao_status(
    pedido,
    novo_status
):
    """
    Controla o fluxo operacional pelo backend.
    O frontend pode solicitar a mudanca, mas o servidor decide
    se a transicao e permitida.
    """

    status_atual = pedido.status

    transicoes_permitidas = {
        "NOVO": {
            "EM PREPARO"
        },
        "EM PREPARO": {
            "PRONTO"
        },
        "PRONTO PARA RETIRADA": {
            "FINALIZADO"
        },
        "PRONTO PARA ENTREGA": {
            "SAIU PARA ENTREGA"
        },
        "SAIU PARA ENTREGA": {
            "FINALIZADO"
        },
        "FINALIZADO": set()
    }

    if novo_status == status_atual:
        return True, None

    permitidos = transicoes_permitidas.get(
        status_atual,
        set()
    )

    if novo_status not in permitidos:
        return (
            False,
            f"Transicao invalida: {status_atual} -> {novo_status}."
        )

    if (
        novo_status == "SAIU PARA ENTREGA"
        and pedido.tipo != "entrega"
    ):
        return (
            False,
            "Pedido de retirada nao pode sair para entrega."
        )

    return True, None


# ============================================================
# LOGIN E LOGOUT DO PAINEL
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if painel_autenticado():
        return redirect(
            url_for(
                "painel"
            )
        )

    senha_configurada = senha_painel_configurada()

    if not senha_configurada:

        return render_template_string(
            LOGIN_HTML,
            erro=(
                "Senha do painel ainda nao foi configurada "
                "no arquivo .env."
            )
        ), 503

    erro = None

    if request.method == "POST":

        senha_recebida = str(
            request.form.get(
                "senha",
                ""
            )
        )

        if hmac.compare_digest(
            senha_recebida,
            senha_configurada
        ):

            session.clear()

            session[
                "painel_autenticado"
            ] = True

            session.permanent = True

            return redirect(
                url_for(
                    "painel"
                )
            )

        erro = (
            "Senha incorreta."
        )

    return render_template_string(
        LOGIN_HTML,
        erro=erro
    )


@app.route(
    "/logout",
    methods=["POST"]
)
@login_painel_obrigatorio
def logout():

    session.clear()

    return jsonify({
        "sucesso": True,
        "mensagem":
            "Sessao encerrada."
    })


# ============================================================
# PAGINA INICIAL
# ============================================================

@app.route("/")
def inicio():

    empresa = buscar_empresa_padrao()

    if empresa is None:
        return (
            "Empresa padrao nao configurada.",
            503
        )

    return render_template(
        "index.html",
        produtos=produtos,
        empresa=empresa
    )


# ============================================================
# PAINEL DE PRODUCAO
# ============================================================

@app.route("/painel")
@login_painel_obrigatorio
def painel():

    empresa = buscar_empresa_padrao()

    if empresa is None:
        return (
            "Empresa padrao nao configurada.",
            503
        )

    return render_template(
        "painel.html",
        empresa=empresa
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


    empresa = buscar_empresa_padrao()

    if empresa is None:

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Empresa nao configurada."
        }), 503


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

            empresa_id=
                empresa.id,

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


    app.logger.info(
        "Pedido criado com sucesso. pedido_id=%s empresa_id=%s total=%.2f",
        novo_pedido.id,
        novo_pedido.empresa_id,
        total_calculado
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
@login_painel_obrigatorio
def listar_pedidos():

    empresa = buscar_empresa_padrao()

    if empresa is None:

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Empresa nao configurada."
        }), 503


    pedidos_banco = Pedido.query.filter_by(
        empresa_id=empresa.id
    ).order_by(
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
@login_painel_obrigatorio
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


    empresa = buscar_empresa_padrao()

    if empresa is None:

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Empresa nao configurada."
        }), 503


    pedido = Pedido.query.filter_by(
        id=numero,
        empresa_id=empresa.id
    ).first()


    if pedido is None:

        return jsonify({
            "sucesso": False,
            "mensagem":
                "Pedido nao encontrado."
        }), 404


    transicao_valida, erro_transicao = validar_transicao_status(
        pedido,
        novo_status
    )


    if not transicao_valida:

        return jsonify({
            "sucesso": False,
            "mensagem":
                erro_transicao
        }), 400


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


    if not senha_painel_configurada():
        print(
            "ATENCAO: PAINEL_PASSWORD nao configurada no .env."
        )


    app.run(
        debug=app.config.get(
            "DEBUG",
            False
        )
    )
