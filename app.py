import os, uuid
from flask import Flask, render_template, request, redirect, url_for
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mural.db'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB LINHA NOVA <------------

db = SQLAlchemy(app)

@app.errorhandler(413) #LINHA NOVA <------------
def arquivo_grande(e): #LINHA NOVA <------------
    return 'Arquivo maior que 16 MB', 413 #LINHA NOVA <------------

EXTENSOES = {'pdf', 'png', 'jpg', 'txt'}

def extensao_permitida(nome):
    return '.' in nome and nome.rsplit('.', 1)[1].lower() in EXTENSOES


class Arquivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_original = db.Column (db.String(255), nullable= False)
    nome_armazenado = db.Column (db.String(255), nullable= False, unique=True)
    enviado_em = db.Column(db.DateTime, server_default=db.func.now())

@app.route('/')
def index():
    arquivos = Arquivo.query.order_by(Arquivo.enviado_em.desc()).all()
    return render_template('index.html', arquivos=arquivos)

@app.route('/upload', methods=['POST'])
def upload():
    if 'arquivo' not in request.files:
        return 'Nenhum arquivo enviado', 400
    arquivo = request.files['arquivo']
    if arquivo.filename =='' or not extensao_permitida(arquivo.filename):
        return 'Arquivo vazio ou extensão não permitida', 400
    
    nome_seguro = secure_filename(arquivo.filename)
    nome_armazenado = f"{uuid.uuid4().hex}_{nome_seguro}"
    arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_armazenado))
    db.session.add(Arquivo(nome_original=nome_seguro, nome_armazenado=nome_armazenado))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/download/<int:id>')
def download(id):
    registro = db.get_or_404(Arquivo, id)
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        registro.nome_armazenado,
        as_attachment= True, 
        download_name= registro.nome_original
    )

@app.route('/apagar/<int:id>', methods=['POST'])
def apagar(id):
    registro = db.get_or_404(Arquivo, id)
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], registro.nome_armazenado)
    if os.path.exists(caminho):
        os.remove(caminho)
    db.session.delete(registro)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == "__main__":
    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()

    app.run(debug=True)
    
