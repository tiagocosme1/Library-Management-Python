"""
servidor.py — Servidor TCP BiblioCore (Sprint 3)

Protocolo: TCP/IP, porta 5000, mensagens JSON.

Requisições:
  {"acao": "cadastrar_livro",    "titulo": "...", "autor": "...", "ano": "..."}
  {"acao": "listar_livros"}
  {"acao": "buscar_livro",       "livro_id": 1}
  {"acao": "buscar_titulo",      "termo": "Python"}
  {"acao": "excluir_livro",      "livro_id": 1}
  {"acao": "cadastrar_usuario",  "nome": "...", "identificacao": "..."}
  {"acao": "listar_usuarios"}
  {"acao": "excluir_usuario",    "usuario_id": 1}
  {"acao": "emprestar_livro",    "usuario_id": 1, "livro_id": 2}
  {"acao": "devolver_livro",     "livro_id": 2}
  {"acao": "renovar_emprestimo", "livro_id": 2}
  {"acao": "listar_emprestimos"}
  {"acao": "relatorio"}
  {"acao": "historico"}
  {"acao": "adicionar_reserva",  "usuario_id": 1, "livro_id": 2}
  {"acao": "listar_reservas"}

Resposta padrão:
  {"status": "ok",    "mensagem": "...", "dados": {...}}
  {"status": "erro",  "mensagem": "..."}
"""

import socket
import json
import threading
import sys

import database as db
from threads import iniciar_threads, fila_reservas, historico, simular_multiplos_usuarios

HOST = "0.0.0.0"
PORT = 5000
BUFFER = 4096

_mutex_server = threading.Lock()


# ─────────────────────────────────────────────
# Roteador de ações
# ─────────────────────────────────────────────

def _processar(req: dict) -> dict:
    acao = req.get("acao", "")

    # ── Livros ──────────────────────────────
    if acao == "cadastrar_livro":
        titulo = req.get("titulo", "").strip()
        autor  = req.get("autor", "").strip()
        ano    = req.get("ano", "").strip()
        if not titulo:
            return _erro("Título é obrigatório.")
        livro = db.cadastrar_livro(titulo, autor, ano)
        historico.registrar(f"Livro cadastrado: {titulo} (id={livro.id})")
        return _ok("Livro cadastrado.", {"livro": livro.to_dict()})

    if acao == "listar_livros":
        livros = [l.to_dict() for l in db.listar_livros()]
        return _ok(f"{len(livros)} livro(s) encontrado(s).", {"livros": livros})

    if acao == "buscar_livro":
        livro_id = req.get("livro_id")
        if livro_id is None:
            return _erro("livro_id é obrigatório.")
        livro = db.buscar_livro(int(livro_id))
        if not livro:
            return _erro("Livro não encontrado.")
        return _ok("Livro encontrado.", {"livro": livro.to_dict()})

    if acao == "buscar_titulo":
        termo = req.get("termo", "").strip()
        if not termo:
            return _erro("Informe o termo de busca.")
        livros = [l.to_dict() for l in db.buscar_livros_por_titulo(termo)]
        return _ok(f"{len(livros)} resultado(s).", {"livros": livros})

    if acao == "excluir_livro":
        livro_id = req.get("livro_id")
        if livro_id is None:
            return _erro("livro_id é obrigatório.")
        ok, msg = db.excluir_livro(int(livro_id))
        if ok:
            historico.registrar(f"Livro excluído: id={livro_id}")
        return _ok(msg) if ok else _erro(msg)

    # ── Usuários ────────────────────────────
    if acao == "cadastrar_usuario":
        nome = req.get("nome", "").strip()
        identificacao = req.get("identificacao", "").strip()
        if not nome:
            return _erro("Nome é obrigatório.")
        usuario = db.cadastrar_usuario(nome, identificacao)
        historico.registrar(f"Usuário cadastrado: {nome} (id={usuario.id})")
        return _ok("Usuário cadastrado.", {"usuario": usuario.to_dict()})

    if acao == "listar_usuarios":
        usuarios = [u.to_dict() for u in db.listar_usuarios()]
        return _ok(f"{len(usuarios)} usuário(s).", {"usuarios": usuarios})

    if acao == "excluir_usuario":
        usuario_id = req.get("usuario_id")
        if usuario_id is None:
            return _erro("usuario_id é obrigatório.")
        ok, msg = db.excluir_usuario(int(usuario_id))
        if ok:
            historico.registrar(f"Usuário excluído: id={usuario_id}")
        return _ok(msg) if ok else _erro(msg)

    # ── Empréstimos ─────────────────────────
    if acao == "emprestar_livro":
        usuario_id = req.get("usuario_id")
        livro_id   = req.get("livro_id")
        if usuario_id is None or livro_id is None:
            return _erro("usuario_id e livro_id são obrigatórios.")
        ok, msg = db.realizar_emprestimo(int(usuario_id), int(livro_id))
        if ok:
            historico.registrar(f"Empréstimo: usuário {usuario_id} ← livro {livro_id}")
        return _ok(msg) if ok else _erro(msg)

    if acao == "devolver_livro":
        livro_id = req.get("livro_id")
        if livro_id is None:
            return _erro("livro_id é obrigatório.")
        ok, msg = db.devolver_livro(int(livro_id))
        if ok:
            historico.registrar(f"Devolução: livro {livro_id}")
        return _ok(msg) if ok else _erro(msg)

    if acao == "renovar_emprestimo":
        livro_id = req.get("livro_id")
        if livro_id is None:
            return _erro("livro_id é obrigatório.")
        ok, msg = db.renovar_emprestimo(int(livro_id))
        if ok:
            historico.registrar(f"Renovação: livro {livro_id}")
        return _ok(msg) if ok else _erro(msg)

    if acao == "listar_emprestimos":
        emprestimos = db.listar_emprestimos_ativos()
        return _ok(f"{len(emprestimos)} empréstimo(s) ativo(s).", {"emprestimos": emprestimos})

    # ── Relatório e Histórico ───────────────
    if acao == "relatorio":
        rel = db.gerar_relatorio()
        return _ok("Relatório gerado.", {"relatorio": rel})

    if acao == "historico":
        return _ok("Histórico de operações.", {"historico": historico.listar()})

    # ── Fila de Reservas ────────────────────
    if acao == "adicionar_reserva":
        usuario_id = req.get("usuario_id")
        livro_id   = req.get("livro_id")
        if usuario_id is None or livro_id is None:
            return _erro("usuario_id e livro_id são obrigatórios.")
        fila_reservas.adicionar(int(usuario_id), int(livro_id))
        return _ok(f"Reserva adicionada. Posição na fila: {fila_reservas.tamanho()}")

    if acao == "listar_reservas":
        return _ok(f"{fila_reservas.tamanho()} reserva(s) na fila.",
                   {"reservas": fila_reservas.listar()})

    return _erro(f"Ação desconhecida: '{acao}'")


def _ok(mensagem: str, dados: dict = None) -> dict:
    resp = {"status": "ok", "mensagem": mensagem}
    if dados:
        resp["dados"] = dados
    return resp


def _erro(mensagem: str) -> dict:
    return {"status": "erro", "mensagem": mensagem}


# ─────────────────────────────────────────────
# Handler por cliente
# ─────────────────────────────────────────────

def _handle_cliente(conn: socket.socket, addr):
    print(f"  [+] Conexão de {addr}")
    try:
        while True:
            data = conn.recv(BUFFER)
            if not data:
                break
            try:
                req = json.loads(data.decode("utf-8"))
                resp = _processar(req)
            except json.JSONDecodeError:
                resp = _erro("JSON inválido.")
            conn.sendall(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        conn.close()
        print(f"  [-] Conexão encerrada: {addr}")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    db.inicializar_banco()

    # Inicia threads com intervalos curtos para facilitar testes
    iniciar_threads(intervalo_atrasos=60, intervalo_relatorio=120)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)

    print(f"\n{'='*40}")
    print(f"  BiblioCore — Servidor TCP")
    print(f"  Escutando em {HOST}:{PORT}")
    print(f"{'='*40}\n")

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(
                target=_handle_cliente, args=(conn, addr), daemon=True
            )
            t.start()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
