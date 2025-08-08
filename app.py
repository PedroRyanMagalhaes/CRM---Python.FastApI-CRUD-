from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Field, or_, SQLModel, create_engine, Session, select
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

class ClienteUpdate(SQLModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None

DATABASE_FILE = "database.db"
engine = create_engine(f"sqlite:///{DATABASE_FILE}", echo=True)

def create_db_and_tables():
    print("Executando SQLModel.metadata.create_all(engine)...")
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app:FastAPI):
    print ("API ESTA LIGANDO, CRIANDO TABELAS...")
    create_db_and_tables()
    print ("API ESTA LIGADA")
    yield
    print("API desligando...")

'''
O símbolo @ em Python é usado para algo especial chamado Decorador (Decorator).

Pense no decorador como um carimbo mágico que você aplica em uma função para dar a ela um superpoder ou um novo comportamento.

app.on_event(...) sem o @ seria uma chamada de função normal.

@app.on_event(...) com o @ na linha de cima de uma def, significa: "Pegue a função que está logo abaixo (def on_startup():) e
 "enrole" ela com a lógica do on_event. Registre-a no FastAPI para ser executada quando o evento 'startup' acontecer."

Então, o @ não chama a função, ele conecta a função on_startup ao evento startup do objeto app. É o "adesivo" que liga as duas coisas.
'''

def get_session():
    "Função para obter uma sessão do banco de dados"
    with Session(engine) as session:
        yield session

app = FastAPI(
    lifespan=lifespan,
    title="API CRM Loja de Roupas",
    description="API para gerenciar clientes de uma loja de roupas.",
    version="1.0.0",
)
   
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
def read_clientes(session: Session = Depends(get_session), 
                  termo : Optional[str] = None):
    '''Retornar todos os clientes ou filtrar por termo'''

    query = select(Cliente)

    if termo: 
        expressao_de_busca = f"%{termo}%"
        query = query.where(
            or_(
            Cliente.nome.ilike(expressao_de_busca),
            Cliente.email.ilike(expressao_de_busca),
            Cliente.telefone.ilike(expressao_de_busca)
            )
        )

    clientes = session.exec(query).all()
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

@app.put("/clientes/{cliente_id}", response_model=ClienteRead, tags={"Clientes"})
def update_cliente(cliente_id: int, cliente_dados:ClienteUpdate, session: Session = Depends(get_session)):
    '''Atualiza um cliente existente pelo ID'''
    db_cliente = session.get(Cliente, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    update_dados = cliente_dados.model_dump(exclude_unset=True)

    for key, value in update_dados.items():
        if value:
            setattr(db_cliente, key, value)

    session.add(db_cliente)
    session.commit()
    session.refresh(db_cliente)
    return db_cliente
'''
Eu tinha um objetio criado com idade e nome que eu mandei no get la no banco
pedro 35
ai eu crieo uma nova variavel update_dados que o dicinario das novas informaçoes
ai eu falei for key,value in update_dados.item
vai iterando chave e valor no meu dicionario que agora meu diconaro esta com duplas por conta da funçao item entao agroa meu diconario esta
nome pedro
idade 40
que sao os dados qu eo user colocou
ai o setattr vem e fala pega o objetio que temos que o db cliente pedro 35 e passa key e value entao passa nome pedro e idade 40
e ai chama a sesioon da um add e da um commmit e da um refrech pra atualixar tudo
'''

@app.delete ("/clientes/{cliente_id}", tags=["Clientes"])
def detele_cliente(cliente_id: int, session: Session = Depends(get_session)):
    ''' deleta um cliente pelo ID'''
    cliente_para_apagar= session.get(Cliente, cliente_id)
    if not cliente_para_apagar:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    session.delete(cliente_para_apagar)
    session.commit()
    return{"detalhe": "Cliente deletado com sucesso"}








