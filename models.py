class Livro:
    def __init__(self, id, titulo, autor, ano):
        self.id = id
        self.titulo = titulo
        self.autor = autor
        self.ano = ano
        self.disponivel = True

    def to_dict(self):
        return self.__dict__

class Usuario:
    def __init__(self, id, nome):
        self.id = id
        self.nome = nome
        self.livros = []
        self.bloqueado = False

    def to_dict(self):
        return self.__dict__

class Emprestimo:
    def __init__(self, usuario_id, livro_id):
        self.usuario_id = usuario_id
        self.livro_id = livro_id