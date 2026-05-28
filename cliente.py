"""
cliente.py — Cliente CLI BiblioCore (Sprint 3)

Conecta ao servidor TCP e oferece menu interativo.
Use quando o servidor.py estiver rodando em outro terminal.
"""

import socket
import json

HOST = "127.0.0.1"
PORT = 5000
BUFFER = 65536


def _enviar(req: dict) -> dict:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((HOST, PORT))
            s.sendall(json.dumps(req, ensure_ascii=False).encode("utf-8"))
            data = s.recv(BUFFER)
        return json.loads(data.decode("utf-8"))
    except ConnectionRefusedError:
        return {"status": "erro", "mensagem": "Servidor não encontrado. Inicie o servidor.py primeiro."}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}


def _imprimir(resp: dict):
    if resp["status"] == "ok":
        print(f"\n  ✔ {resp['mensagem']}")
        dados = resp.get("dados")
        if dados:
            # Livros
            if "livros" in dados:
                livros = dados["livros"]
                if not livros:
                    print("  (nenhum livro cadastrado)")
                for l in livros:
                    status = "✓ Disponível" if l["status"] == "disponivel" else "✗ Emprestado"
                    print(f"  [{l['id']}] {l['titulo']} — {l['autor']} ({l['ano']}) | {status}")
            if "livro" in dados:
                l = dados["livro"]
                print(f"  ID: {l['id']} | Título: {l['titulo']} | Autor: {l['autor']} | "
                      f"Ano: {l['ano']} | Status: {l['status']}")

            # Usuários
            if "usuarios" in dados:
                usuarios = dados["usuarios"]
                if not usuarios:
                    print("  (nenhum usuário cadastrado)")
                for u in usuarios:
                    bloq = " [BLOQUEADO]" if u["status"] == "bloqueado" else ""
                    print(f"  [{u['id']}] {u['nome']} | ID: {u['identificacao']}{bloq}")
            if "usuario" in dados:
                u = dados["usuario"]
                print(f"  ID: {u['id']} | Nome: {u['nome']} | Identificação: {u['identificacao']}")

            # Empréstimos
            if "emprestimos" in dados:
                emps = dados["emprestimos"]
                if not emps:
                    print("  (nenhum empréstimo ativo)")
                for e in emps:
                    print(f"  Emp.{e['id']} | {e['usuario']} ← {e['livro']} | "
                          f"Devolução: {e['data_devolucao_prevista']} | {e['status']}")

            # Relatório
            if "relatorio" in dados:
                r = dados["relatorio"]
                print(f"  Livros disponíveis : {r['livros_disponiveis']}")
                print(f"  Livros emprestados : {r['livros_emprestados']}")
                print(f"  Em atraso          : {r['emprestimos_em_atraso']}")
                print(f"  Usuários bloqueados: {r['usuarios_bloqueados']}")

            # Histórico
            if "historico" in dados:
                hist = dados["historico"]
                if not hist:
                    print("  (sem operações registradas)")
                for i, op in enumerate(hist[:20], 1):
                    print(f"  {i}. {op}")

            # Reservas
            if "reservas" in dados:
                for r in dados["reservas"]:
                    print(f"  Usuário {r['usuario_id']} aguarda livro {r['livro_id']}")
    else:
        print(f"\n  ✗ ERRO: {resp['mensagem']}")


# ─────────────────────────────────────────────
# Menu
# ─────────────────────────────────────────────

def _input(prompt: str) -> str:
    return input(f"  {prompt}").strip()


def menu():
    print("\n" + "="*45)
    print("  BiblioCore — Cliente CLI")
    print("="*45)

    while True:
        print("""
  ── Livros ──────────────────────────
  1  Cadastrar livro
  2  Listar livros
  3  Buscar livro por ID
  4  Buscar livro por título
  5  Excluir livro
  ── Usuários ────────────────────────
  6  Cadastrar usuário
  7  Listar usuários
  8  Excluir usuário
  ── Empréstimos ─────────────────────
  9  Emprestar livro
  10 Devolver livro
  11 Renovar empréstimo
  12 Listar empréstimos ativos
  ── Reservas ────────────────────────
  13 Adicionar reserva
  14 Listar reservas
  ── Sistema ─────────────────────────
  15 Relatório do acervo
  16 Histórico de operações
  0  Sair
""")
        op = _input("Escolha: ")

        if op == "0":
            print("\n  Até logo!\n")
            break

        elif op == "1":
            titulo = _input("Título: ")
            autor  = _input("Autor: ")
            ano    = _input("Ano: ")
            _imprimir(_enviar({"acao": "cadastrar_livro", "titulo": titulo, "autor": autor, "ano": ano}))

        elif op == "2":
            _imprimir(_enviar({"acao": "listar_livros"}))

        elif op == "3":
            livro_id = _input("ID do livro: ")
            _imprimir(_enviar({"acao": "buscar_livro", "livro_id": int(livro_id)}))

        elif op == "4":
            termo = _input("Título (parcial): ")
            _imprimir(_enviar({"acao": "buscar_titulo", "termo": termo}))

        elif op == "5":
            livro_id = _input("ID do livro: ")
            _imprimir(_enviar({"acao": "excluir_livro", "livro_id": int(livro_id)}))

        elif op == "6":
            nome = _input("Nome: ")
            ident = _input("CPF ou matrícula: ")
            _imprimir(_enviar({"acao": "cadastrar_usuario", "nome": nome, "identificacao": ident}))

        elif op == "7":
            _imprimir(_enviar({"acao": "listar_usuarios"}))

        elif op == "8":
            usuario_id = _input("ID do usuário: ")
            _imprimir(_enviar({"acao": "excluir_usuario", "usuario_id": int(usuario_id)}))

        elif op == "9":
            usuario_id = _input("ID do usuário: ")
            livro_id   = _input("ID do livro: ")
            _imprimir(_enviar({"acao": "emprestar_livro",
                               "usuario_id": int(usuario_id), "livro_id": int(livro_id)}))

        elif op == "10":
            livro_id = _input("ID do livro: ")
            _imprimir(_enviar({"acao": "devolver_livro", "livro_id": int(livro_id)}))

        elif op == "11":
            livro_id = _input("ID do livro: ")
            _imprimir(_enviar({"acao": "renovar_emprestimo", "livro_id": int(livro_id)}))

        elif op == "12":
            _imprimir(_enviar({"acao": "listar_emprestimos"}))

        elif op == "13":
            usuario_id = _input("ID do usuário: ")
            livro_id   = _input("ID do livro: ")
            _imprimir(_enviar({"acao": "adicionar_reserva",
                               "usuario_id": int(usuario_id), "livro_id": int(livro_id)}))

        elif op == "14":
            _imprimir(_enviar({"acao": "listar_reservas"}))

        elif op == "15":
            _imprimir(_enviar({"acao": "relatorio"}))

        elif op == "16":
            _imprimir(_enviar({"acao": "historico"}))

        else:
            print("  Opção inválida.")


if __name__ == "__main__":
    menu()
