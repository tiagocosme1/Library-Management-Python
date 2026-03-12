import json
import os

DB_FILE = "database.json"

def carregar_dados():
    if not os.path.exists(DB_FILE):
        return {"livros": [], "usuarios": []}

    with open(DB_FILE, "r") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(DB_FILE, "w") as f:
        json.dump(dados, f, indent=4)