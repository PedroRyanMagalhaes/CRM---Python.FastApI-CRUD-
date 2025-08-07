from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional, List
from contextlib import asynccontextmanager


class ClienteBase(SQLModel):
    #Aqui usamso o (SqlModel) para Herança tudo que tiver no sql model a class ClienteBase recebe
    nome : str 
    email : str
    telefone: Optional[str]

class Cliente(ClienteBase, table=True):
    #não é so uma class aqui ele ta falando que Cliente é uma tabela
    id: Optional[int] = Field(default=None, primary_key=True)
    #o Optional é para dizer que o id pode ser None, ou seja, não é obrigatório ser int, pq quando eu registrar o nome nao vai ter id ainda o sql que vai por o int dele dps automatico 
    #Field é para passarmsos exatamente como querermos que o id seja tratado no banco de dados
    # o primary_key=True diz que esse campo é a chave primária da tabela nao pode ser repetido e cria indice otimzado pra fazer consulta 

class ClienteCreate(ClienteBase):
    pass

class ClienteRead(ClienteBase):
    id: int

DATABASE_FILE = "database.db"
engine = create_engine(f"sqlite:///{DATABASE_FILE}", echo=True)

def create_db_and_tables():
    print("Executando SQLModel.metadata.create_all(engine)...")
    SQLModel.metadata.create_all(engine)

'''
O símbolo @ em Python é usado para algo especial chamado Decorador (Decorator).

Pense no decorador como um carimbo mágico que você aplica em uma função para dar a ela um superpoder ou um novo comportamento.

app.on_event(...) sem o @ seria uma chamada de função normal.

@app.on_event(...) com o @ na linha de cima de uma def, significa: "Pegue a função que está logo abaixo (def on_startup():) e
 "enrole" ela com a lógica do on_event. Registre-a no FastAPI para ser executada quando o evento 'startup' acontecer."

Então, o @ não chama a função, ele conecta a função on_startup ao evento startup do objeto app. É o "adesivo" que liga as duas coisas.
'''

@asynccontextmanager
async def lifespan(app:FastAPI):
    print ("API ESTA LIGANDO, CRIANDO TABELAS...")
    create_db_and_tables()
    print ("API ESTA LIGADA")
    yield
    print("API desligando...")

def get_session():
    "Função para obter uma sessão do banco de dados"
    with Session(engine) as session:
        yield session

app = FastAPI(lifespan=lifespan)

'''Cadastrar um novo cliente'''
@app.post("/clientes/", response_model=ClienteRead,  tags=["Clientes"])
def create_cliente(cliente: ClienteCreate, session: Session = Depends(get_session)):
    #cliente aqui é um objetio criado nos moldes da class ClienteCreate
    db_cliente = Cliente.model_validate(cliente)
    #passa o objetio cliente para o model validate validar se ta nos moldes da class Cliente se tiver blz tranforma em db_cliente
    session.add(db_cliente)
    session.commit()
    session.refresh(db_cliente)
    #o banco cria um id automatico porque Field(default=None, primary_key=True) passmaos isso aqui na class cliente
    return db_cliente



@app.get("/clientes/", response_model=List[ClienteRead], tags=["Clientes"])
def read_clientes(session: Session = Depends(get_session)):
    #session: Session siginfica apenas que to criando um objeto chamado session que é no memso molde de Session importado do sqlmodel
    '''Retornar a lista de todos os clientes cadastrados'''
    clientes = session.exec(select(Cliente)).all()
    return clientes

@app.get("/clientes/{cliente_id}", response_model=ClienteRead, tags=["Clientes"])
def read_cliente_by_id(cliente_id: int, session: Session = Depends(get_session)):
    '''Retornar um cliente específico pelo ID'''
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente
'''
como se tivesse o espaço em branco que é equivalente o cliente_id nessa estrutura toda  

 ai vem o numero passa na url fast api vai buscar la com url pronta /clientes/5/

ai a gente falo pra ele cliente id é um numero inteiro ele pega e coloca o numero que ele coloco na url nesse espaço ai pois é o mesmo nome da variavel

 criamos a session com banco de dados ate ai temos ja entao o numero na url o numero no espaço cliente_id e conexao com banco aberta  

 ai vamo la e criamos a variavel cliente que vai usar a sessao do banco "get" que é uma funçao ja pre pronta que pega coluna com chave primeira e fala 

esse cliente é oque vc achar em coluna Clientes com a chave primeira 5  (cupondo que o numero passado la em cima era 5)

 ai ele vai  e pega  

 e no caso ele vai trazer toda a info da linha 5 da coluna clientes nesse caso
'''



