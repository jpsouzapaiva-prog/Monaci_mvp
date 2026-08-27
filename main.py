from flask import Flask, render_template, request, jsonify
from datetime import datetime

from cardapio import cardapio


app = Flask(__name__)


# ============================================================
# PRODUTOS DO CARDAPIO
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
# PEDIDOS
# ============================================================

pedidos = []


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

@app.route("/pedidos", methods=["POST"])
def criar_pedido():

    dados = request.get_json()

    if not dados:

        return jsonify({
            "sucesso": False,
            "mensagem": "Nenhum dado recebido."
        }), 400


    cliente = dados.get(
        "cliente",
        ""
    ).strip()


    itens = dados.get(
        "itens",
        []
    )


    if cliente == "":

        return jsonify({
            "sucesso": False,
            "mensagem": "Nome do cliente nao informado."
        }), 400


    if len(itens) == 0:

        return jsonify({
            "sucesso": False,
            "mensagem": "Pedido sem produtos."
        }), 400


    numero_pedido = (
        len(pedidos) + 1
    )


    tipo_pedido = dados.get(
        "tipo",
        "retirada"
    )


    novo_pedido = {

        "numero": numero_pedido,

        "numero_formatado":
            str(numero_pedido).zfill(4),

        "cliente": cliente,

        "tipo": tipo_pedido,

        "endereco": dados.get(
            "endereco",
            ""
        ),

        "pagamento": dados.get(
            "pagamento",
            ""
        ),

        "total": dados.get(
            "total",
            0
        ),

        "itens": itens,

        "status": "NOVO",

        "data_hora": datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        ),

        "hora_inicio_preparo": "",

        "hora_pronto": "",

        "hora_saida_entrega": "",

        "hora_finalizado": ""
    }


    pedidos.append(
        novo_pedido
    )


    # ========================================================
    # MOSTRAR PEDIDO NO CONSOLE
    # ========================================================

    print("\n")
    print("=" * 50)

    print(
        "PEDIDO #",
        novo_pedido["numero_formatado"]
    )

    print(
        "CLIENTE:",
        novo_pedido["cliente"]
    )

    print(
        "TIPO:",
        novo_pedido["tipo"]
    )


    if novo_pedido["endereco"]:

        print(
            "ENDERECO:",
            novo_pedido["endereco"]
        )


    print(
        "PAGAMENTO:",
        novo_pedido["pagamento"]
    )

    print(
        "TOTAL: R$",
        f'{novo_pedido["total"]:.2f}'
    )

    print("-" * 50)


    for item in novo_pedido["itens"]:

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


        # MOLHO

        molho = item.get(
            "molho",
            ""
        )

        if molho:

            print(
                "  Molho:",
                molho
            )


        # SEM MILHO

        if item.get(
            "semMilho"
        ):

            print(
                "  Sem milho"
            )


        # SEM AZEITONA

        if item.get(
            "semAzeitona"
        ):

            print(
                "  Sem azeitona"
            )


        # RETIRADOS

        retirados = item.get(
            "retirados",
            []
        )

        if retirados:

            print(
                "  Retirar:",
                ", ".join(retirados)
            )


        # ADICIONAIS

        adicionais = item.get(
            "adicionais",
            []
        )

        if adicionais:

            print(
                "  Adicionais:"
            )

            for adicional in adicionais:

                if isinstance(
                    adicional,
                    dict
                ):

                    print(
                        "   +",
                        adicional.get(
                            "nome",
                            ""
                        ),
                        "R$",
                        f'{adicional.get("preco", 0):.2f}'
                    )

                else:

                    print(
                        "   +",
                        adicional
                    )


        # SUCO COM OU SEM LEITE

        leite = item.get(
            "leite"
        )

        if leite is True:

            print(
                "  Com leite"
            )

        elif leite is False:

            print(
                "  Sem leite"
            )


        # ACUCAR

        acucar = item.get(
            "acucar"
        )

        if acucar is True:

            print(
                "  Com acucar"
            )

        elif acucar is False:

            print(
                "  Sem acucar"
            )


        # OBSERVACAO

        observacao = item.get(
            "observacao",
            ""
        )

        if observacao:

            print(
                "  OBS:",
                observacao
            )


    print("-" * 50)

    print(
        "STATUS:",
        novo_pedido["status"]
    )

    print(
        "HORARIO:",
        novo_pedido["data_hora"]
    )

    print("=" * 50)


    return jsonify({

        "sucesso": True,

        "numero":
            numero_pedido,

        "numero_formatado":
            novo_pedido[
                "numero_formatado"
            ],

        "mensagem":
            "Pedido recebido com sucesso."
    })


# ============================================================
# LISTAR PEDIDOS
# ============================================================

@app.route("/pedidos", methods=["GET"])
def listar_pedidos():

    return jsonify(
        pedidos
    )


# ============================================================
# ALTERAR STATUS
# ============================================================

@app.route(
    "/pedidos/<int:numero>/status",
    methods=["PUT"]
)
def alterar_status(numero):

    dados = request.get_json()

    novo_status = dados.get(
        "status",
        ""
    )


    status_permitidos = [
        "NOVO",
        "EM PREPARO",
        "PRONTO",
        "SAIU PARA ENTREGA",
        "FINALIZADO"
    ]


    if novo_status not in status_permitidos:

        return jsonify({
            "sucesso": False,
            "mensagem": "Status invalido."
        }), 400


    for pedido in pedidos:

        if pedido["numero"] == numero:


            # ================================================
            # EM PREPARO
            # ================================================

            if novo_status == "EM PREPARO":

                pedido["status"] = (
                    "EM PREPARO"
                )

                pedido[
                    "hora_inicio_preparo"
                ] = datetime.now().strftime(
                    "%H:%M:%S"
                )


            # ================================================
            # PRONTO
            # ================================================

            elif novo_status == "PRONTO":

                if pedido["tipo"] == "retirada":

                    pedido["status"] = (
                        "PRONTO PARA RETIRADA"
                    )

                else:

                    pedido["status"] = (
                        "PRONTO PARA ENTREGA"
                    )


                pedido[
                    "hora_pronto"
                ] = datetime.now().strftime(
                    "%H:%M:%S"
                )


            # ================================================
            # SAIU PARA ENTREGA
            # ================================================

            elif novo_status == "SAIU PARA ENTREGA":

                if pedido["tipo"] != "entrega":

                    return jsonify({
                        "sucesso": False,
                        "mensagem":
                            "Pedido de retirada nao pode sair para entrega."
                    }), 400


                if pedido["status"] != "PRONTO PARA ENTREGA":

                    return jsonify({
                        "sucesso": False,
                        "mensagem":
                            "O pedido precisa estar pronto antes de sair para entrega."
                    }), 400


                pedido["status"] = (
                    "SAIU PARA ENTREGA"
                )

                pedido[
                    "hora_saida_entrega"
                ] = datetime.now().strftime(
                    "%H:%M:%S"
                )


            # ================================================
            # FINALIZADO
            # ================================================

            elif novo_status == "FINALIZADO":

                pedido["status"] = (
                    "FINALIZADO"
                )

                pedido[
                    "hora_finalizado"
                ] = datetime.now().strftime(
                    "%H:%M:%S"
                )


            # ================================================
            # VOLTAR PARA NOVO
            # ================================================

            elif novo_status == "NOVO":

                pedido["status"] = (
                    "NOVO"
                )


            return jsonify({

                "sucesso": True,

                "mensagem":
                    "Status atualizado.",

                "status":
                    pedido["status"]
            })


    return jsonify({
        "sucesso": False,
        "mensagem": "Pedido nao encontrado."
    }), 404


# ============================================================
# INICIAR SISTEMA
# ============================================================

if __name__ == "__main__":

    print(
        "=== MONACI MVP ==="
    )

    print(
        "Produtos carregados:",
        len(produtos)
    )

    app.run(
        debug=True
    )