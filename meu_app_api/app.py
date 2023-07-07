from flask_openapi3 import OpenAPI, Info, Tag
from flask import redirect
from urllib.parse import unquote

from sqlalchemy.exc import IntegrityError

from model import Session, Aluno
from logger import logger
from schemas import *
from flask_cors import CORS

info = Info(title="Minha API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

# definindo tags
home_tag = Tag(name="Documentação", description="Seleção de documentação: Swagger, Redoc ou RapiDoc")
aluno_tag = Tag(name="Aluno", description="Adição, visualização e remoção de alunos à base")


@app.get('/', tags=[home_tag])
def home():
    """Redireciona para /openapi, tela que permite a escolha do estilo de documentação.
    """
    return redirect('/openapi')


@app.get('/alunos', tags=[aluno_tag],
         responses={"200": ListagemAlunoSchema, "404": ErrorSchema})
def get_alunos():
    """Faz a busca por todos os Alunos cadastrados

    Retorna uma representação da listagem de alunos.
    """
    logger.debug(f"Coletando alunos ")
    # criando conexão com a base
    session = Session()
    # fazendo a busca
    alunos = session.query(Aluno).all()

    if not alunos:
        # se não há alunos cadastrados
        return {"alunos": []}, 200
    else:
        logger.debug(f"%d alunos econtrados" % len(alunos))
        # retorna a representação de aluno
        print(alunos)
        return apresenta_alunos(alunos), 200
    
@app.post('/aluno', tags=[aluno_tag],
          responses={"200": AlunoViewSchema, "409": ErrorSchema, "400": ErrorSchema})
def add_aluno(form: AlunoSchema):
    """Adiciona um novo Aluno à base de dados

    Retorna uma representação dos alunos.
    """
    aluno = Aluno(
        nome=form.nome,
        documento=form.documento,
        genero=form.genero,
        data_nascimento=form.data_nascimento,
        email=form.email,
        telefone=form.telefone)
    logger.debug(f"Adicionando aluno de nome: '{aluno.nome}'")
    try:
        # criando conexão com a base
        session = Session()
        # adicionando produto
        session.add(aluno)
        # efetivando o camando de adição de novo item na tabela
        session.commit()
        logger.debug(f"Adicionado aluno de nome: '{aluno.nome}'")
        return apresenta_aluno(aluno), 200

    except IntegrityError as e:
        # como a duplicidade do documento é a provável razão do IntegrityError
        error_msg = "Aluno de mesmo documento já salvo na base :/"
        logger.warning(f"Erro ao adicionar aluno '{aluno.nome}', {error_msg}")
        return {"mesage": error_msg}, 409

    except Exception as e:
        # caso um erro fora do previsto
        error_msg = "Não foi possível salvar novo item :/"
        logger.warning(f"Erro ao adicionar aluno '{aluno.nome}', {error_msg}")
        return {"mesage": error_msg}, 400
    

@app.delete('/aluno', tags=[aluno_tag],
            responses={"200": AlunoDelSchema, "404": ErrorSchema})
def del_aluno(query: AlunoBuscaSchema):
    """Deleta um Aluno a partir do documento da aluno informado

    Retorna uma mensagem de confirmação da remoção.
    """
    aluno_documento = unquote(unquote(query.documento))
    print(aluno_documento)
    logger.debug(f"Deletando dados do aluno #{aluno_documento}")
    # criando conexão com a base
    session = Session()
    # fazendo a remoção
    count = session.query(Aluno).filter(Aluno.documento == aluno_documento).delete()
    session.commit()

    if count:
        # retorna a representação da mensagem de confirmação
        logger.debug(f"Deletado aluno #{aluno_documento}")
        return {"mesage": "Aluno removido", "documento": aluno_documento}
    else:
        # se o aluno não foi encontrado
        error_msg = "Aluno não encontrado na base :/"
        logger.warning(f"Erro ao deletar aluno #'{aluno_documento}', {error_msg}")
        return {"mesage": error_msg}, 404