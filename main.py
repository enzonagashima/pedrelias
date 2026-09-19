from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrumento TEXT NOT NULL,
            volume TEXT NOT NULL,
            status TEXT DEFAULT 'pendente'
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        instrumento = request.form['instrumento']
        volume = request.form['volume']
        
        conn = sqlite3.connect('mesa.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO pedidos (instrumento, volume, status) VALUES (?, ?, ?)', 
                       (instrumento, volume, 'pendente'))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))
        
    return render_template('index.html')

@app.route('/operador')
def operador():
    return render_template('operador.html')

@app.route('/api/pedidos')
def listar_pedidos():
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, instrumento, volume FROM pedidos WHERE status = 'pendente'")
    pedidos = cursor.fetchall()
    conn.close()
    
    lista = [{'id': p[0], 'instrumento': p[1], 'volume': p[2]} for p in pedidos]
    return jsonify(lista)

@app.route('/api/pedido/<int:id>/<acao>', methods=['POST'])
def atualizar_pedido(id, acao):
    novo_status = 'aceito' if acao == 'aceitar' else 'recusado'
    
    conn = sqlite3.connect('mesa.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, id))
    conn.commit()
    conn.close()
    
    return jsonify({'sucesso': True, 'status': novo_status})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)