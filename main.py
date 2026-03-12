from models import Livro, Usuario
from storage import carregar_dados, salvar_dados
from queue_stack import FilaReservas, PilhaHistorico

fila = FilaReservas()
historico = PilhaHistorico()

dados = carregar_dados()

def cadastrar_livro():
    titulo = input("Título: ")
    autor = input("Autor: ")
    ano = input("Ano: ")

    novo_id = len(dados["livros"]) + 1
    livro = Livro(novo_id, titulo, autor, ano)

    dados["livros"].append(livro.to_dict())
    salvar_dados(dados)

    historico.registrar("Livro cadastrado")

def listar_livros():
    for l in dados["livros"]:
        status = "Disponível" if l["disponivel"] else "Emprestado"
        print(f"{l['id']} - {l['titulo']} ({status})")

def cadastrar_usuario():
    nome = input("Nome do usuário: ")

    novo_id = len(dados["usuarios"]) + 1
    usuario = Usuario(novo_id, nome)

    dados["usuarios"].append(usuario.to_dict())
    salvar_dados(dados)

    historico.registrar("Usuário cadastrado")

def listar_usuarios():
    for u in dados["usuarios"]:
        print(f'{u["id"]} - {u["nome"]} | Livros emprestados: {u["livros"]}')

def emprestar_livro():
    livro_id = int(input("ID do livro: "))
    usuario_id = int(input("ID do usuário: "))

    livro = next((l for l in dados["livros"] if l["id"] == livro_id), None)
    usuario = next((u for u in dados["usuarios"] if u["id"] == usuario_id), None)

    if not livro or not usuario:
        print("Usuário ou livro não encontrado")
        return

    if not livro["disponivel"]:
        print("Livro já emprestado")
        return

    if len(usuario["livros"]) >= 3:
        print("Usuário atingiu limite de empréstimos")
        return

    livro["disponivel"] = False
    usuario["livros"].append(livro_id)

    salvar_dados(dados)
    print("Empréstimo realizado!")

def excluir_livro():
    livro_id = int(input("ID do livro para excluir: "))

    livro = next((l for l in dados["livros"] if l["id"] == livro_id), None)

    if not livro:
        print("Livro não encontrado")
        return

    if not livro["disponivel"]:
        print("Não é possível excluir um livro emprestado")
        return

    dados["livros"].remove(livro)

    salvar_dados(dados)

    print("Livro excluído com sucesso!")

def excluir_usuario():
    usuario_id = int(input("ID do usuário para excluir: "))

    usuario = next((u for u in dados["usuarios"] if u["id"] == usuario_id), None)

    if not usuario:
        print("Usuário não encontrado")
        return

    if usuario["livros"]:
        print("Usuário possui livros emprestados")
        return

    dados["usuarios"].remove(usuario)

    salvar_dados(dados)

    print("Usuário excluído com sucesso!")

def devolver_livro():
    livro_id = int(input("ID do livro para devolução: "))

    livro = next((l for l in dados["livros"] if l["id"] == livro_id), None)

    if not livro:
        print("Livro não encontrado")
        return

    if livro["disponivel"]:
        print("Esse livro já está disponível")
        return

    livro["disponivel"] = True

    for u in dados["usuarios"]:
        if livro_id in u["livros"]:
            u["livros"].remove(livro_id)

    salvar_dados(dados)

    print("Livro devolvido com sucesso!")

def menu():
    while True:
        print("\n==================")
        print("SISTEMA BIBLIOTECA")
        print("==================")
        print("1 - Cadastrar livro")
        print("2 - Listar livros")
        print("3 - Cadastrar usuário")
        print("4 - Listar usuários")
        print("5 - Emprestar livro")
        print("6 - Devolver livro")
        print("7 - Excluir livro")
        print("8 - Excluir usuário")
        print("9 - Sair")

        op = input("Escolha: ")

        if op == "1":
            cadastrar_livro()

        elif op == "2":
            listar_livros()

        elif op == "3":
            cadastrar_usuario()

        elif op == "4":
            listar_usuarios()

        elif op == "5":
            emprestar_livro()

        elif op == "6":
            devolver_livro()

        elif op == "7":
            excluir_livro()

        elif op == "8":
            excluir_usuario()

        elif op == "9":
            break

if __name__ == "__main__":
    menu()