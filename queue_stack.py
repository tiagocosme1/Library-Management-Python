"""
queue_stack.py — Fila de Reservas e Pilha de Histórico
"""
import threading


class FilaReservas:
    """
    Fila FIFO thread-safe para reservas de livros (RF11).
    Processada pela thread_fila_reservas em threads.py.
    """

    def __init__(self):
        self._fila: list[dict] = []
        self._lock = threading.Lock()

    def adicionar(self, usuario_id: int, livro_id: int):
        with self._lock:
            self._fila.append({"usuario_id": usuario_id, "livro_id": livro_id})

    def proximo(self) -> dict | None:
        with self._lock:
            if self._fila:
                return self._fila.pop(0)
        return None

    def tamanho(self) -> int:
        with self._lock:
            return len(self._fila)

    def listar(self) -> list[dict]:
        with self._lock:
            return list(self._fila)

    def esta_vazia(self) -> bool:
        with self._lock:
            return len(self._fila) == 0


class PilhaHistorico:
    """
    Pilha LIFO thread-safe para histórico de operações (RF09).
    Suporta desfazer (undo) da última operação.
    """

    def __init__(self, limite: int = 200):
        self._pilha: list[str] = []
        self._lock = threading.Lock()
        self._limite = limite

    def registrar(self, operacao: str):
        with self._lock:
            if len(self._pilha) >= self._limite:
                self._pilha.pop(0)   # descarta o mais antigo
            self._pilha.append(operacao)

    def ultimo(self) -> str | None:
        with self._lock:
            if self._pilha:
                return self._pilha[-1]
        return None

    def desfazer(self) -> str | None:
        """Remove e retorna a última operação (undo)."""
        with self._lock:
            if self._pilha:
                return self._pilha.pop()
        return None

    def listar(self) -> list[str]:
        with self._lock:
            return list(reversed(self._pilha))

    def tamanho(self) -> int:
        with self._lock:
            return len(self._pilha)
