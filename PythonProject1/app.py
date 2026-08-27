import json
import os
import sqlite3
import urllib.request
from datetime import datetime
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# URL do Google Apps Script (Web App) publicada pelo dono da planilha.
# Configure esta variável na hospedagem (Render) ou em um arquivo .env local.
GOOGLE_SHEETS_WEBAPP_URL = os.environ.get('GOOGLE_SHEETS_WEBAPP_URL', '')

# Endereço e link oficial do Google Maps para a localização do evento
MAPS_LINK = "https://www.google.com/maps/place/15%C2%B037'38.7%22S+47%C2%B050'09.8%22W/@-15.6274167,-47.8386166,17z/data=!3m1!4b1!4m4!3m3!8m2!3d-15.6274167!4d-47.8360417?hl=pt-BR&entry=ttu&g_ep=EgoyMDI2MDgyNC4wIKXMDSoASAFQAw%3D%3D"


def salvar_no_sheets(nome='', presenca='', presente='', acompanhantes='', mensagem=''):
    """Envia um registro para a planilha do Google via Google Apps Script Web App.

    Falha silenciosa (apenas log) para nunca quebrar o fluxo do site
    caso a URL não esteja configurada ou o serviço esteja indisponível.
    """
    if not GOOGLE_SHEETS_WEBAPP_URL:
        print('[Google Sheets] GOOGLE_SHEETS_WEBAPP_URL nao configurada. Registro nao enviado.')
        return

    payload = {
        'data_hora': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'nome': nome,
        'presenca': presenca,
        'presente': presente,
        'acompanhantes': acompanhantes,
        'mensagem': mensagem,
    }
    try:
        req = urllib.request.Request(
            GOOGLE_SHEETS_WEBAPP_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
        print(f'[Google Sheets] Registro enviado: {nome} / {presente or presenca}')
    except Exception as exc:
        print(f'[Google Sheets] Erro ao enviar registro: {exc}')


def get_db_connection():
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'aniversario.db'))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela de Presentes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            reservado INTEGER DEFAULT 0,
            por TEXT
        )
    ''')

    # Tabela de Presenças (RSVP)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presencas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            acompanhantes INTEGER DEFAULT 0,
            mensagem TEXT
        )
    ''')

    # Inserção inicial da lista caso o banco esteja vazio
    cursor.execute('SELECT COUNT(*) FROM presentes')
    if cursor.fetchone()[0] == 0:
        itens_iniciais = [
            ("Acessórios (colares, anéis, pulseiras etc.)",),
            ("Tênis (tamanho 38/39)",),
            ("Perfumes",),
            ("Body Splash",),
            ("Bolsas",),
            ("Roupas (jaquetas, calças, blusas, vestidos, conjuntos)",),
            ("Livro: Heróis do Olimpo Vol. 1 - O Herói Perdido",),
            ("Livro: Heróis do Olimpo Vol. 2 - O Filho de Netuno",),
            ("Livro: Heróis do Olimpo Vol. 3 - A Marca de Atena",),
            ("Livro: Heróis do Olimpo Vol. 4 - A Casa de Hades",),
            ("Livro: Heróis do Olimpo Vol. 5 - O Sangue do Olimpo",),
            ("Contribuição via Pix",)
        ]
        cursor.executemany('INSERT INTO presentes (nome) VALUES (?)', itens_iniciais)
        conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    conn = get_db_connection()
    presentes = conn.execute('SELECT * FROM presentes').fetchall()
    presencas = conn.execute('SELECT * FROM presencas').fetchall()
    conn.close()

    # Gera a imagem do QR Code apontando diretamente para o link atual do site
    site_url = request.url
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={site_url}"

    # QR Code da localização do evento (abre o Google Maps no endereço do convite)
    qr_code_local_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={quote(MAPS_LINK, safe='')}"

    return render_template('index.html', presentes=presentes, presencas=presencas,
                           qr_code_url=qr_code_url, qr_code_local_url=qr_code_local_url, maps_link=MAPS_LINK)


@app.route('/reservar/<int:item_id>', methods=['POST'])
def reservar(item_id):
    nome_convidado = request.form.get('nome_convidado')
    if nome_convidado:
        conn = get_db_connection()
        presente = conn.execute('SELECT nome FROM presentes WHERE id = ?', (item_id,)).fetchone()
        # Insere ou atualiza o registro permitindo que múltiplos convidados escolham a opção
        conn.execute('UPDATE presentes SET reservado = 1, por = COALESCE(por || ", ", "") || ? WHERE id = ?', (nome_convidado, item_id))
        conn.commit()
        conn.close()
        presente_nome = presente['nome'] if presente else f'Presente #{item_id}'
        salvar_no_sheets(nome=nome_convidado, presenca='', presente=presente_nome)
    return redirect(url_for('index'))


@app.route('/confirmar-presenca', methods=['POST'])
def confirmar_presenca():
    nome = request.form.get('nome')
    acompanhantes = request.form.get('acompanhantes', 0)
    mensagem = request.form.get('mensagem', '')

    if nome:
        conn = get_db_connection()
        conn.execute('INSERT INTO presencas (nome, acompanhantes, mensagem) VALUES (?, ?, ?)',
                     (nome, acompanhantes, mensagem))
        conn.commit()
        conn.close()
        salvar_no_sheets(nome=nome, presenca='Confirmado', acompanhantes=acompanhantes, mensagem=mensagem)
    return redirect(url_for('index'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)