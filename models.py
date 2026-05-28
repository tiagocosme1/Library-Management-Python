from datetime import date, timedelta

PRAZO_EMPRESTIMO_DIAS = 7
LIMITE_LIVROS_POR_USUARIO = 3


class Livro:
    def __init__(self, id, titulo, autor, ano, status="disponivel"):
        self.id = id
        self.titulo = titulo
        self.autor = autor
        self.ano = ano
        self.status = status  # "disponivel" | "emprestado"

    @property
    def disponivel(self):
        return self.status == "disponivel"

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "autor": self.autor,
            "ano": self.ano,
            "status": self.status,
        }

    @staticmethod
    def from_dict(d):
        return Livro(d["id"], d["titulo"], d["autor"], d["ano"], d.get("status", "disponivel"))


class Usuario:
    def __init__(self, id, nome, identificacao="", status="ativo"):
        self.id = id
        self.nome = nome
        self.identificacao = identificacao   # CPF ou matrícula
        self.status = status                 # "ativo" | "bloqueado"

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "identificacao": self.identificacao,
            "status": self.status,
        }

    @staticmethod
    def from_dict(d):
        return Usuario(d["id"], d["nome"], d.get("identificacao", ""), d.get("status", "ativo"))


class Emprestimo:
    def __init__(self, id, usuario_id, livro_id,
                 data_emprestimo=None, data_devolucao_prevista=None,
                 status="ativo"):
        self.id = id
        self.usuario_id = usuario_id
        self.livro_id = livro_id
        self.data_emprestimo = data_emprestimo or date.today().isoformat()
        self.data_devolucao_prevista = data_devolucao_prevista or (
            date.today() + timedelta(days=PRAZO_EMPRESTIMO_DIAS)
        ).isoformat()
        self.status = status  # "ativo" | "devolvido" | "em_atraso"
        self.renovacoes = 0

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "livro_id": self.livro_id,
            "data_emprestimo": self.data_emprestimo,
            "data_devolucao_prevista": self.data_devolucao_prevista,
            "status": self.status,
            "renovacoes": self.renovacoes,
        }

    @staticmethod
    def from_dict(d):
        emp = Emprestimo(
            d["id"], d["usuario_id"], d["livro_id"],
            d["data_emprestimo"], d["data_devolucao_prevista"],
            d.get("status", "ativo"),
        )
        emp.renovacoes = d.get("renovacoes", 0)
        return emp
