from flask import Flask,render_template
app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("index.html")


print("=== MONACI MVP ===")

pedidos = [
    {
        "numero": 1,
        "cliente": "Joao",
        "produtos": [
            "2 Cachorros-quentes",
            "1 Hamburguer",
            "2 Sucos"
        ]
    },
    {
        "numero": 2,
        "cliente": "Maria",
        "produtos": [
            "1 Hamburguer",
            "1 Suco"
        ]
    }
]

for pedido in pedidos:
    print("\n========================")
    print("Pedido:", pedido["numero"])
    print("Cliente:", pedido["cliente"])
    print("========================")

    for produto in pedido["produtos"]:

        if "cachorro" in produto.lower():
            print("SETOR CACHORRO-QUENTE:", produto)

        elif "hamburguer" in produto.lower():
            print("SETOR HAMBURGUER:", produto)

        elif "suco" in produto.lower():
            print("SETOR BEBIDAS:", produto)

if __name__ == "__main__":
    app.run(debug=True)