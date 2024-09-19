from flask import Flask, render_template, request, jsonify
from llm_model import responder_pergunta
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    dados = request.get_json()
    pergunta = dados.get('pergunta')
    try:
        # Tente processar a pergunta
        resposta = responder_pergunta(pergunta)
        return jsonify({'resposta': resposta})

    except Exception as e:
        # Retorna uma mensagem genérica para qualquer tipo de erro
        return jsonify({
            'erro': 'Ocorreu um erro ao processar a solicitação. Tente reformular a sua pergunta.'
        }), 500  # HTTP status code 500 para erros gerais do servidor

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))  # Usa a porta fornecida pelo Render ou 5000 como fallback
    app.run(host="0.0.0.0", port=port)   # Garantir que Flask escute em 0.0.0.0
