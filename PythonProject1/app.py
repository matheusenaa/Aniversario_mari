import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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

    return render_template('index.html', presentes=presentes, presencas=presencas, qr_code_url=qr_code_url)


@app.route('/reservar/<int:item_id>', methods=['POST'])
def reservar(item_id):
    nome_convidado = request.form.get('nome_convidado')
    if nome_convidado:
        conn = get_db_connection()
        # Insere ou atualiza o registro permitindo que múltiplos convidados escolham a opção
        conn.execute('UPDATE presentes SET reservado = 1, por = COALESCE(por || ", ", "") || ? WHERE id = ?', (nome_convidado, item_id))
        conn.commit()
        conn.close()
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
    return redirect(url_for('index'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)