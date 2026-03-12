class FilaReservas:
    def __init__(self):
        self.fila = []

    def adicionar(self, usuario_id, livro_id):
        self.fila.append((usuario_id, livro_id))

    def proximo(self):
        if self.fila:
            return self.fila.pop(0)
        return None

class PilhaHistorico:
    def __init__(self):
        self.pilha = []

    def registrar(self, operacao):
        self.pilha.append(operacao)

    def ultimo(self):
        if self.pilha:
            return self.pilha.pop()
        return None