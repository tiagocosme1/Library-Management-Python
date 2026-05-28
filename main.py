"""
main.py — Modo Standalone BiblioCore
Executa o sistema localmente sem servidor TCP.
Para arquitetura cliente-servidor, use servidor.py + cliente.py.
"""

import database as db
from threads import (
    iniciar_threads, fila_reservas, historico,
    simular_multiplos_usuarios, parar_threads
)


def _sep():
    print("\n" + "="*40)
    print("  SISTEMA BIBLIOTECA — BiblioCore")
    print("="*40)


# ─────────────────────────────────────────────
# Livros
# ─────────────────────────────────────────────

def cadastrar_livro():
    titulo = input("  Título: ").strip()
    autor  = input("  Autor: ").strip()
    ano    = input("  Ano: ").strip()
    if not titulo:
        print("  Título é obrigatório!")
        return
    livro = db.cadastrar_livro(titulo, autor, ano)
    historico.registrar(f"Livro cadastrado: {titulo} (id={livro.id})")
    print(f"  ✔ Livro cadastrado com ID {livro.id}.")


def listar_livros():
    livros = db.listar_livros()
    if not livros:
        print("  (nenhum livro cadastrado)")
        return
    for l in livros:
        status = "✓ Disponível" if l.disponivel else "✗ Emprestado"
        print(f"  [{l.id}] {l.titulo} — {l.autor} ({l.ano}) | {status}")


def buscar_livro():
    print("  1 - Buscar por ID")
    print("  2 - Buscar por título")
    op = input("  Opção: ").strip()
    if op == "1":
        livro_id = int(input("  ID: "))
        livro = db.buscar_livro(livro_id)
        if livro:
            print(f"  {livro.titulo} | {livro.autor} | {livro.ano} | {livro.status}")
        else:
            print("  Livro não encontrado.")
    elif op == "2":
        termo = input("  Título (parcial): ").strip()
        resultados = db.buscar_livros_por_titulo(termo)
        if not resultados:
            print("  Nenhum resultado.")
        for l in resultados:
            print(f"  [{l.id}] {l.titulo} — {l.autor}")


def excluir_livro():
    livro_id = int(input("  ID do livro: "))
    ok, msg = db.excluir_livro(livro_id)
    print(f"  {'✔' if ok else '✗'} {msg}")
    if ok:
        historico.registrar(f"Livro excluído: id={livro_id}")


# ─────────────────────────────────────────────
# Usuários
# ─────────────────────────────────────────────

def cadastrar_usuario():
    nome  = input("  Nome: ").strip()
    ident = input("  CPF ou matrícula: ").strip()
    if not nome:
        print("  Nome é obrigatório!")
        return
    usuario = db.cadastrar_usuario(nome, ident)
    historico.registrar(f"Usuário cadastrado: {nome} (id={usuario.id})")
    print(f"  ✔ Usuário cadastrado com ID {usuario.id}.")


def listar_usuarios():
    usuarios = db.listar_usuarios()
    if not usuarios:
        print("  (nenhum usuário cadastrado)")
        return
    for u in usuarios:
        bloq = " [BLOQUEADO]" if u.status == "bloqueado" else ""
        print(f"  [{u.id}] {u.nome} | {u.identificacao}{bloq}")


def excluir_usuario():
    usuario_id = int(input("  ID do usuário: "))
    ok, msg = db.excluir_usuario(usuario_id)
    print(f"  {'✔' if ok else '✗'} {msg}")
    if ok:
        historico.registrar(f"Usuário excluído: id={usuario_id}")


# ─────────────────────────────────────────────
# Empréstimos
# ─────────────────────────────────────────────

def emprestar_livro():
    usuario_id = int(input("  ID do usuário: "))
    livro_id   = int(input("  ID do livro: "))
    ok, msg = db.realizar_emprestimo(usuario_id, livro_id)
    print(f"  {'✔' if ok else '✗'} {msg}")
    if ok:
        historico.registrar(f"Empréstimo: usuário {usuario_id} ← livro {livro_id}")


def devolver_livro():
    livro_id = int(input("  ID do livro: "))
    ok, msg = db.devolver_livro(livro_id)
    print(f"  {'✔' if ok else '✗'} {msg}")
    if ok:
        historico.registrar(f"Devolução: livro {livro_id}")


def renovar_emprestimo():
    livro_id = int(input("  ID do livro: "))
    ok, msg = db.renovar_emprestimo(livro_id)
    print(f"  {'✔' if ok else '✗'} {msg}")
    if ok:
        historico.registrar(f"Renovação: livro {livro_id}")


def listar_emprestimos():
    emps = db.listar_emprestimos_ativos()
    if not emps:
        print("  (nenhum empréstimo ativo)")
        return
    for e in emps:
        print(f"  Emp.{e['id']} | {e['usuario']} ← {e['livro']} | "
              f"Devolução: {e['data_devolucao_prevista']} | {e['status']}")


# ─────────────────────────────────────────────
# Reservas
# ─────────────────────────────────────────────

def adicionar_reserva():
    usuario_id = int(input("  ID do usuário: "))
    livro_id   = int(input("  ID do livro: "))
    fila_reservas.adicionar(usuario_id, livro_id)
    print(f"  ✔ Reserva adicionada. Posição na fila: {fila_reservas.tamanho()}")


def listar_reservas():
    reservas = fila_reservas.listar()
    if not reservas:
        print("  (nenhuma reserva na fila)")
        return
    for i, r in enumerate(reservas, 1):
        print(f"  {i}. Usuário {r['usuario_id']} aguarda livro {r['livro_id']}")


# ─────────────────────────────────────────────
# Sistema
# ─────────────────────────────────────────────

def exibir_relatorio():
    rel = db.gerar_relatorio()
    print(f"  Livros disponíveis : {rel['livros_disponiveis']}")
    print(f"  Livros emprestados : {rel['livros_emprestados']}")
    print(f"  Em atraso          : {rel['emprestimos_em_atraso']}")
    print(f"  Usuários bloqueados: {rel['usuarios_bloqueados']}")


def exibir_historico():
    ops = historico.listar()
    if not ops:
        print("  (sem operações registradas)")
        return
    for i, op in enumerate(ops[:20], 1):
        print(f"  {i}. {op}")


def rodar_simulacao():
    n_usuarios = int(input("  Número de usuários simultâneos [5]: ") or "5")
    n_ops      = int(input("  Operações por usuário [4]: ") or "4")
    logs = simular_multiplos_usuarios(n_usuarios, n_ops)
    for linha in logs:
        print(linha)


# ─────────────────────────────────────────────
# Menu Principal
# ─────────────────────────────────────────────

def menu():
    db.inicializar_banco()
    iniciar_threads(intervalo_atrasos=60, intervalo_relatorio=120)

    while True:
        _sep()
        print("""
  ── Livros ───────────────────────
  1  Cadastrar livro
  2  Listar livros
  3  Buscar livro
  4  Excluir livro
  ── Usuários ─────────────────────
  5  Cadastrar usuário
  6  Listar usuários
  7  Excluir usuário
  ── Empréstimos ───────────────────
  8  Emprestar livro
  9  Devolver livro
  10 Renovar empréstimo
  11 Listar empréstimos ativos
  ── Reservas ─────────────────────
  12 Adicionar reserva
  13 Listar reservas
  ── Sistema ──────────────────────
  14 Relatório do acervo
  15 Histórico de operações
  16 Simular múltiplos usuários
  0  Sair
""")
        op = input("  Escolha: ").strip()

        try:
            if   op == "0":  parar_threads(); print("\n  Até logo!\n"); break
            elif op == "1":  cadastrar_livro()
            elif op == "2":  listar_livros()
            elif op == "3":  buscar_livro()
            elif op == "4":  excluir_livro()
            elif op == "5":  cadastrar_usuario()
            elif op == "6":  listar_usuarios()
            elif op == "7":  excluir_usuario()
            elif op == "8":  emprestar_livro()
            elif op == "9":  devolver_livro()
            elif op == "10": renovar_emprestimo()
            elif op == "11": listar_emprestimos()
            elif op == "12": adicionar_reserva()
            elif op == "13": listar_reservas()
            elif op == "14": exibir_relatorio()
            elif op == "15": exibir_historico()
            elif op == "16": rodar_simulacao()
            else:            print("  Opção inválida.")
        except ValueError:
            print("  Entrada inválida. Use apenas números onde solicitado.")
        except KeyboardInterrupt:
            parar_threads()
            print("\n  Saindo...\n")
            break


if __name__ == "__main__":
    menu()
