"""
threads.py — Módulo de Concorrência (Sprint 2)

Implementa:
  - thread_fila_reservas      : processa reservas da fila quando livro fica disponível
  - thread_verificar_atrasos  : verifica prazos vencidos a cada hora
  - thread_relatorios         : gera relatório do acervo periodicamente
  - thread_validar_livros     : validação em lote de livros (simulação)
  - thread_validar_usuarios   : validação em lote de usuários (simulação)
  - simular_multiplos_usuarios: teste de carga com N threads concorrentes
"""

import threading
import time
import random
from datetime import datetime

import database as db
from queue_stack import FilaReservas, PilhaHistorico

# ─────────────────────────────────────────────
# Objetos globais compartilhados
# ─────────────────────────────────────────────
fila_reservas = FilaReservas()
historico = PilhaHistorico()

_stop_event = threading.Event()   # sinaliza parada de todas as threads daemon


def parar_threads():
    """Sinaliza todas as threads daemon para encerrarem."""
    _stop_event.set()


def _log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [THREAD {ts}] {msg}")


# ─────────────────────────────────────────────
# Thread 1 — Fila de Reservas
# ─────────────────────────────────────────────

def _worker_fila_reservas():
    """
    Fica em loop verificando a fila de reservas.
    Quando um livro fica disponível e há reserva na fila, realiza o empréstimo.
    """
    _log("thread_fila_reservas iniciada.")
    while not _stop_event.is_set():
        if not fila_reservas.esta_vazia():
            reserva = fila_reservas.proximo()
            if reserva:
                livro = db.buscar_livro(reserva["livro_id"])
                if livro and livro.disponivel:
                    ok, msg = db.realizar_emprestimo(
                        reserva["usuario_id"], reserva["livro_id"]
                    )
                    if ok:
                        historico.registrar(
                            f"Reserva processada: usuário {reserva['usuario_id']} "
                            f"← livro {reserva['livro_id']}"
                        )
                        _log(f"Reserva atendida: {msg}")
                    else:
                        # Devolve à fila se falhou por motivo transitório
                        fila_reservas.adicionar(reserva["usuario_id"], reserva["livro_id"])
        time.sleep(5)
    _log("thread_fila_reservas encerrada.")


# ─────────────────────────────────────────────
# Thread 2 — Verificação de Atrasos
# ─────────────────────────────────────────────

def _worker_verificar_atrasos(intervalo_segundos: int = 3600):
    """
    Verifica periodicamente empréstimos vencidos.
    Marca como 'em_atraso' e bloqueia o usuário.
    Intervalo padrão: 1 hora (3600s). Em testes use 30s.
    """
    _log("thread_verificar_atrasos iniciada.")
    while not _stop_event.is_set():
        atrasados = db.verificar_atrasos()
        if atrasados:
            _log(f"{len(atrasados)} empréstimo(s) marcado(s) em atraso.")
            for emp in atrasados:
                historico.registrar(
                    f"Atraso detectado: empréstimo {emp['id']} "
                    f"(usuário {emp['usuario_id']}, livro {emp['livro_id']})"
                )
        _stop_event.wait(intervalo_segundos)
    _log("thread_verificar_atrasos encerrada.")


# ─────────────────────────────────────────────
# Thread 3 — Relatórios Paralelos
# ─────────────────────────────────────────────

def _worker_relatorios(intervalo_segundos: int = 1800):
    """
    Gera relatório do acervo periodicamente.
    Intervalo padrão: 30 min. Em testes use 60s.
    """
    _log("thread_relatorios iniciada.")
    while not _stop_event.is_set():
        rel = db.gerar_relatorio()
        _log(
            f"Relatório | Disponíveis: {rel['livros_disponiveis']} | "
            f"Emprestados: {rel['livros_emprestados']} | "
            f"Em atraso: {rel['emprestimos_em_atraso']} | "
            f"Usuários bloqueados: {rel['usuarios_bloqueados']}"
        )
        historico.registrar(f"Relatório gerado: {rel}")
        _stop_event.wait(intervalo_segundos)
    _log("thread_relatorios encerrada.")


# ─────────────────────────────────────────────
# Thread 4 — Validação de Livros em Lote
# ─────────────────────────────────────────────

def _worker_validar_livros():
    """
    Valida integridade dos livros no banco (campos obrigatórios, status coerente).
    Roda uma vez na inicialização e depois fica em standby.
    """
    _log("thread_validar_livros iniciada.")
    livros = db.listar_livros()
    problemas = 0
    for l in livros:
        if not l.titulo.strip():
            _log(f"  AVISO: Livro id={l.id} sem título!")
            problemas += 1
        if l.status not in ("disponivel", "emprestado"):
            _log(f"  AVISO: Livro id={l.id} com status inválido '{l.status}'!")
            problemas += 1
    _log(f"thread_validar_livros concluída. {len(livros)} livros verificados, {problemas} problema(s).")


# ─────────────────────────────────────────────
# Thread 5 — Validação de Usuários em Lote
# ─────────────────────────────────────────────

def _worker_validar_usuarios():
    """
    Valida integridade dos usuários no banco.
    """
    _log("thread_validar_usuarios iniciada.")
    usuarios = db.listar_usuarios()
    problemas = 0
    for u in usuarios:
        if not u.nome.strip():
            _log(f"  AVISO: Usuário id={u.id} sem nome!")
            problemas += 1
        if u.status not in ("ativo", "bloqueado"):
            _log(f"  AVISO: Usuário id={u.id} com status inválido '{u.status}'!")
            problemas += 1
    _log(f"thread_validar_usuarios concluída. {len(usuarios)} usuários verificados, {problemas} problema(s).")


# ─────────────────────────────────────────────
# Inicialização de todas as threads daemon
# ─────────────────────────────────────────────

def iniciar_threads(intervalo_atrasos: int = 3600, intervalo_relatorio: int = 1800):
    """
    Inicia todas as threads daemon do sistema.
    Chame uma vez na inicialização do servidor.
    """
    _stop_event.clear()

    threads = [
        threading.Thread(target=_worker_fila_reservas,    daemon=True, name="fila_reservas"),
        threading.Thread(target=_worker_verificar_atrasos, daemon=True, name="verif_atrasos",
                         args=(intervalo_atrasos,)),
        threading.Thread(target=_worker_relatorios,        daemon=True, name="relatorios",
                         args=(intervalo_relatorio,)),
        threading.Thread(target=_worker_validar_livros,    daemon=True, name="valid_livros"),
        threading.Thread(target=_worker_validar_usuarios,  daemon=True, name="valid_usuarios"),
    ]

    for t in threads:
        t.start()

    return threads


# ─────────────────────────────────────────────
# Simulação de Múltiplos Usuários (Sprint 2 §6.4)
# ─────────────────────────────────────────────

_resultados_simulacao: list[str] = []
_lock_resultados = threading.Lock()


def _usuario_simulado(usuario_id: int, livros_ids: list[int], n_operacoes: int):
    """Simula um usuário realizando empréstimos e devoluções aleatoriamente."""
    for _ in range(n_operacoes):
        livro_id = random.choice(livros_ids)
        acao = random.choice(["emprestar", "devolver"])

        if acao == "emprestar":
            ok, msg = db.realizar_emprestimo(usuario_id, livro_id)
        else:
            ok, msg = db.devolver_livro(livro_id)

        with _lock_resultados:
            _resultados_simulacao.append(
                f"  Usuário {usuario_id} | {acao} livro {livro_id} → {msg}"
            )
        time.sleep(random.uniform(0.05, 0.2))


def simular_multiplos_usuarios(n_usuarios: int = 5, n_operacoes: int = 4) -> list[str]:
    """
    Cria N threads simulando N usuários acessando o sistema ao mesmo tempo.
    Retorna log das operações realizadas.
    """
    _resultados_simulacao.clear()

    livros = db.listar_livros()
    usuarios = db.listar_usuarios()

    if not livros or not usuarios:
        return ["Simulação cancelada: cadastre ao menos 1 livro e 1 usuário antes."]

    livros_ids = [l.id for l in livros]
    usuarios_ids = [u.id for u in usuarios]

    print(f"\n[SIMULAÇÃO] Iniciando {n_usuarios} usuários simultâneos, {n_operacoes} ops cada...")

    threads = []
    for i in range(n_usuarios):
        uid = usuarios_ids[i % len(usuarios_ids)]
        t = threading.Thread(
            target=_usuario_simulado,
            args=(uid, livros_ids, n_operacoes),
            name=f"sim_user_{i}"
        )
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verificação de consistência final
    relatorio = db.gerar_relatorio()
    _resultados_simulacao.append(
        f"\n[CONSISTÊNCIA] Disponíveis={relatorio['livros_disponiveis']} | "
        f"Emprestados={relatorio['livros_emprestados']}"
    )

    return list(_resultados_simulacao)
