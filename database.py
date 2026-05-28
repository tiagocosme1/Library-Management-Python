"""
database.py — Camada de persistência SQLite (thread-safe)
Substitui o storage.py baseado em JSON.
"""
import sqlite3
import threading
from contextlib import contextmanager
from datetime import date, timedelta

from models import Livro, Usuario, Emprestimo, PRAZO_EMPRESTIMO_DIAS

DB_FILE = "biblioteca.db"

# Locks por recurso (RN09)
mutex_livros = threading.Lock()
mutex_usuarios = threading.Lock()
mutex_emprestimos = threading.Lock()

# Conexão por thread (sqlite3 não é thread-safe com conexão compartilhada)
_local = threading.local()


def _get_conn():
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")   # permite múltiplos leitores
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


@contextmanager
def _cursor():
    conn = _get_conn()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


# ─────────────────────────────────────────────
# Inicialização
# ─────────────────────────────────────────────

def inicializar_banco():
    """Cria as tabelas se ainda não existirem."""
    with _cursor() as cur:
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS livros (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo  TEXT NOT NULL,
                autor   TEXT DEFAULT '',
                ano     TEXT DEFAULT '',
                status  TEXT DEFAULT 'disponivel'
                         CHECK(status IN ('disponivel','emprestado'))
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                nome           TEXT NOT NULL,
                identificacao  TEXT DEFAULT '',
                status         TEXT DEFAULT 'ativo'
                                CHECK(status IN ('ativo','bloqueado'))
            );

            CREATE TABLE IF NOT EXISTS emprestimos (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id             INTEGER NOT NULL,
                livro_id               INTEGER NOT NULL,
                data_emprestimo        TEXT NOT NULL,
                data_devolucao_prevista TEXT NOT NULL,
                status                 TEXT DEFAULT 'ativo'
                                        CHECK(status IN ('ativo','devolvido','em_atraso')),
                renovacoes             INTEGER DEFAULT 0,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY (livro_id)   REFERENCES livros(id)
            );
        """)


# ─────────────────────────────────────────────
# Livros
# ─────────────────────────────────────────────

def cadastrar_livro(titulo, autor, ano) -> Livro:
    with mutex_livros:
        with _cursor() as cur:
            cur.execute(
                "INSERT INTO livros (titulo, autor, ano) VALUES (?, ?, ?)",
                (titulo, autor, str(ano))
            )
            livro_id = cur.lastrowid
    return Livro(livro_id, titulo, autor, str(ano))


def listar_livros() -> list[Livro]:
    with _cursor() as cur:
        cur.execute("SELECT * FROM livros ORDER BY id")
        return [Livro(r["id"], r["titulo"], r["autor"], r["ano"], r["status"])
                for r in cur.fetchall()]


def buscar_livro(livro_id: int) -> Livro | None:
    with _cursor() as cur:
        cur.execute("SELECT * FROM livros WHERE id = ?", (livro_id,))
        r = cur.fetchone()
    return Livro(r["id"], r["titulo"], r["autor"], r["ano"], r["status"]) if r else None


def buscar_livros_por_titulo(termo: str) -> list[Livro]:
    with _cursor() as cur:
        cur.execute("SELECT * FROM livros WHERE titulo LIKE ? ORDER BY id",
                    (f"%{termo}%",))
        return [Livro(r["id"], r["titulo"], r["autor"], r["ano"], r["status"])
                for r in cur.fetchall()]


def excluir_livro(livro_id: int) -> tuple[bool, str]:
    with mutex_livros:
        livro = buscar_livro(livro_id)
        if not livro:
            return False, "Livro não encontrado."
        if livro.status == "emprestado":
            return False, "Não é possível excluir um livro emprestado."
        with _cursor() as cur:
            cur.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
    return True, "Livro excluído com sucesso."


def _atualizar_status_livro(cur, livro_id: int, status: str):
    cur.execute("UPDATE livros SET status = ? WHERE id = ?", (status, livro_id))


# ─────────────────────────────────────────────
# Usuários
# ─────────────────────────────────────────────

def cadastrar_usuario(nome, identificacao="") -> Usuario:
    with mutex_usuarios:
        with _cursor() as cur:
            cur.execute(
                "INSERT INTO usuarios (nome, identificacao) VALUES (?, ?)",
                (nome, identificacao)
            )
            uid = cur.lastrowid
    return Usuario(uid, nome, identificacao)


def listar_usuarios() -> list[Usuario]:
    with _cursor() as cur:
        cur.execute("SELECT * FROM usuarios ORDER BY id")
        return [Usuario(r["id"], r["nome"], r["identificacao"], r["status"])
                for r in cur.fetchall()]


def buscar_usuario(usuario_id: int) -> Usuario | None:
    with _cursor() as cur:
        cur.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        r = cur.fetchone()
    return Usuario(r["id"], r["nome"], r["identificacao"], r["status"]) if r else None


def excluir_usuario(usuario_id: int) -> tuple[bool, str]:
    with mutex_usuarios:
        usuario = buscar_usuario(usuario_id)
        if not usuario:
            return False, "Usuário não encontrado."
        with _cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as qt FROM emprestimos WHERE usuario_id = ? AND status = 'ativo'",
                (usuario_id,)
            )
            if cur.fetchone()["qt"] > 0:
                return False, "Usuário possui livros emprestados. Devolva antes de excluir."
            cur.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    return True, "Usuário excluído com sucesso."


def _bloquear_usuario(cur, usuario_id: int):
    cur.execute("UPDATE usuarios SET status = 'bloqueado' WHERE id = ?", (usuario_id,))


def _desbloquear_usuario(usuario_id: int):
    with _cursor() as cur:
        cur.execute("UPDATE usuarios SET status = 'ativo' WHERE id = ?", (usuario_id,))


# ─────────────────────────────────────────────
# Empréstimos
# ─────────────────────────────────────────────

def _qtd_emprestimos_ativos(cur, usuario_id: int) -> int:
    cur.execute(
        "SELECT COUNT(*) as qt FROM emprestimos WHERE usuario_id = ? AND status = 'ativo'",
        (usuario_id,)
    )
    return cur.fetchone()["qt"]


def realizar_emprestimo(usuario_id: int, livro_id: int) -> tuple[bool, str]:
    with mutex_emprestimos:
        with _cursor() as cur:
            # Verificações
            cur.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
            u = cur.fetchone()
            if not u:
                return False, "Usuário não encontrado."
            if u["status"] == "bloqueado":
                return False, "Usuário bloqueado por atraso. Regularize a situação."

            cur.execute("SELECT * FROM livros WHERE id = ?", (livro_id,))
            l = cur.fetchone()
            if not l:
                return False, "Livro não encontrado."
            if l["status"] == "emprestado":
                return False, "Livro já está emprestado."

            if _qtd_emprestimos_ativos(cur, usuario_id) >= 3:
                return False, "Usuário já atingiu o limite de 3 empréstimos."

            hoje = date.today().isoformat()
            devolucao = (date.today() + timedelta(days=PRAZO_EMPRESTIMO_DIAS)).isoformat()

            cur.execute(
                """INSERT INTO emprestimos
                   (usuario_id, livro_id, data_emprestimo, data_devolucao_prevista)
                   VALUES (?, ?, ?, ?)""",
                (usuario_id, livro_id, hoje, devolucao)
            )
            _atualizar_status_livro(cur, livro_id, "emprestado")

    return True, f"Empréstimo realizado! Devolução prevista: {devolucao}"


def devolver_livro(livro_id: int) -> tuple[bool, str]:
    with mutex_emprestimos:
        with _cursor() as cur:
            cur.execute(
                "SELECT * FROM emprestimos WHERE livro_id = ? AND status IN ('ativo','em_atraso')",
                (livro_id,)
            )
            emp = cur.fetchone()
            if not emp:
                return False, "Nenhum empréstimo ativo encontrado para este livro."

            cur.execute(
                "UPDATE emprestimos SET status = 'devolvido' WHERE id = ?",
                (emp["id"],)
            )
            _atualizar_status_livro(cur, livro_id, "disponivel")

            # Desbloqueia usuário se não tiver mais atrasos
            cur.execute(
                "SELECT COUNT(*) as qt FROM emprestimos WHERE usuario_id = ? AND status = 'em_atraso'",
                (emp["usuario_id"],)
            )
            if cur.fetchone()["qt"] == 0:
                cur.execute(
                    "UPDATE usuarios SET status = 'ativo' WHERE id = ?",
                    (emp["usuario_id"],)
                )

    return True, "Livro devolvido com sucesso."


def renovar_emprestimo(livro_id: int) -> tuple[bool, str]:
    """Permite uma única renovação por empréstimo (RN03)."""
    with mutex_emprestimos:
        with _cursor() as cur:
            cur.execute(
                "SELECT * FROM emprestimos WHERE livro_id = ? AND status = 'ativo'",
                (livro_id,)
            )
            emp = cur.fetchone()
            if not emp:
                return False, "Nenhum empréstimo ativo para este livro."
            if emp["renovacoes"] >= 1:
                return False, "Este empréstimo já foi renovado uma vez (limite atingido)."

            nova_data = (date.today() + timedelta(days=PRAZO_EMPRESTIMO_DIAS)).isoformat()
            cur.execute(
                "UPDATE emprestimos SET data_devolucao_prevista = ?, renovacoes = renovacoes + 1 WHERE id = ?",
                (nova_data, emp["id"])
            )
    return True, f"Empréstimo renovado! Nova devolução: {nova_data}"


def listar_emprestimos_ativos() -> list[dict]:
    with _cursor() as cur:
        cur.execute("""
            SELECT e.id, u.nome AS usuario, l.titulo AS livro,
                   e.data_emprestimo, e.data_devolucao_prevista, e.status
            FROM emprestimos e
            JOIN usuarios u ON u.id = e.usuario_id
            JOIN livros   l ON l.id = e.livro_id
            WHERE e.status IN ('ativo','em_atraso')
            ORDER BY e.data_devolucao_prevista
        """)
        return [dict(r) for r in cur.fetchall()]


def verificar_atrasos() -> list[dict]:
    """Marca empréstimos vencidos e bloqueia usuários. Retorna lista de atrasados."""
    hoje = date.today().isoformat()
    atrasados = []
    with mutex_emprestimos:
        with _cursor() as cur:
            cur.execute(
                "SELECT * FROM emprestimos WHERE status = 'ativo' AND data_devolucao_prevista < ?",
                (hoje,)
            )
            vencidos = cur.fetchall()
            for emp in vencidos:
                cur.execute(
                    "UPDATE emprestimos SET status = 'em_atraso' WHERE id = ?",
                    (emp["id"],)
                )
                _bloquear_usuario(cur, emp["usuario_id"])
                atrasados.append(dict(emp))
    return atrasados


def gerar_relatorio() -> dict:
    """Retorna contagens para relatório paralelo."""
    with _cursor() as cur:
        cur.execute("SELECT COUNT(*) as qt FROM livros WHERE status = 'disponivel'")
        disponiveis = cur.fetchone()["qt"]
        cur.execute("SELECT COUNT(*) as qt FROM livros WHERE status = 'emprestado'")
        emprestados = cur.fetchone()["qt"]
        cur.execute("SELECT COUNT(*) as qt FROM emprestimos WHERE status = 'em_atraso'")
        em_atraso = cur.fetchone()["qt"]
        cur.execute("SELECT COUNT(*) as qt FROM usuarios WHERE status = 'bloqueado'")
        bloqueados = cur.fetchone()["qt"]
    return {
        "livros_disponiveis": disponiveis,
        "livros_emprestados": emprestados,
        "emprestimos_em_atraso": em_atraso,
        "usuarios_bloqueados": bloqueados,
    }
