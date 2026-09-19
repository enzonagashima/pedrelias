from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    
    # Tabela de Músicos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS musicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            instrumento TEXT NOT NULL,
            volume_atual TEXT DEFAULT '0'
        )
    ''')
    
    # Tabela de Pedidos de Mudança
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musico_id INTEGER,
            instrumento TEXT NOT NULL,
            volume TEXT NOT NULL,
            status TEXT DEFAULT 'pendente',
            FOREIGN KEY (musico_id) REFERENCES musicos (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Rota de Cadastro de Músicos
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nome = request.form['nome']
        instrumento = request.form['instrumento']
        cursor.execute('INSERT INTO musicos (nome, instrumento, volume_atual) VALUES (?, ?, ?)', 
                       (nome, instrumento, '0'))
        conn.commit()
        conn.close()
        return redirect(url_for('cadastro'))
        
    cursor.execute('SELECT id, nome, instrumento, volume_atual FROM musicos')
    musicos = cursor.fetchall()
    conn.close()
    
    return render_template('cadastro.html', musicos=musicos)

# Rota da Tela do Músico (Slider Individual)
@app.route('/musico/<int:id>')
def musico(id):
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, instrumento, volume_atual FROM musicos WHERE id = ?', (id,))
    musico_info = cursor.fetchone()
    conn.close()
    
    if not musico_info:
        return "Músico não encontrado!", 404
        
    return render_template('musico.html', musico=musico_info)

# Rota da Tela do Operador
@app.route('/operador')
def operador():
    return render_template('operador.html')

# API para o músico enviar o pedido direto pelo slider (sem recarregar a página)
@app.route('/api/musico/pedir', methods=['POST'])
def api_musico_pedir():
    musico_id = request.form['musico_id']
    volume = request.form['volume']
    
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT instrumento FROM musicos WHERE id = ?', (musico_id,))
    res = cursor.fetchone()
    instrumento = res[0] if res else "Instrumento"
    
    cursor.execute('INSERT INTO pedidos (musico_id, instrumento, volume, status) VALUES (?, ?, ?, ?)', 
                   (musico_id, instrumento, volume, 'pendente'))
    conn.commit()
    conn.close()
    
    return jsonify({'sucesso': True})

# API para o músico verificar o status atual do seu pedido e o volume oficial
@app.route('/api/musico/status/<int:id>')
def api_musico_status(id):
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT volume_atual FROM musicos WHERE id = ?', (id,))
    musico = cursor.fetchone()
    volume_atual = musico[0] if musico else '0'
    
    cursor.execute('SELECT status FROM pedidos WHERE musico_id = ? ORDER BY id DESC LIMIT 1', (id,))
    pedido = cursor.fetchone()
    status = pedido[0] if pedido else 'aceito'
    
    conn.close()
    return jsonify({'status': status, 'volume_atual': volume_atual})

# API para buscar pedidos pendentes para o operador
@app.route('/api/pedidos')
def listar_pedidos():
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, musico_id, instrumento, volume FROM pedidos WHERE status = 'pendente'")
    pedidos = cursor.fetchall()
    conn.close()
    
    lista = [{'id': p[0], 'musico_id': p[1], 'instrumento': p[2], 'volume': p[3]} for p in pedidos]
    return jsonify(lista)

# API para Operador Aceitar ou Recusar
@app.route('/api/pedido/<int:id>/<acao>', methods=['POST'])
def atualizar_pedido(id, acao):
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    
    if acao == 'aceitar':
        cursor.execute("SELECT musico_id, volume FROM pedidos WHERE id = ?", (id,))
        pedido = cursor.fetchone()
        if pedido:
            musico_id, novo_volume = pedido
            cursor.execute("UPDATE musicos SET volume_atual = ? WHERE id = ?", (novo_volume, musico_id))
        
        novo_status = 'aceito'
    else:
        novo_status = 'recusado'
    
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, id))
    conn.commit()
    conn.close()
    
    return jsonify({'sucesso': True, 'status': novo_status})

# API para o operador ver a lista completa de todos os instrumentos
@app.route('/api/instrumentos')
def listar_instrumentos():
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, instrumento, volume_atual FROM musicos")
    dados = cursor.fetchall()
    conn.close()
    
    lista = [{'id': d[0], 'nome': d[1], 'instrumento': d[2], 'volume_atual': d[3]} for d in dados]
    return jsonify(lista)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)