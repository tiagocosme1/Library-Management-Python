# BiblioCore — Library Management System (Python)

Sistema de gerenciamento de biblioteca desenvolvido em **Python** para controle de livros, usuários e empréstimos, com suporte a **concorrência**, **banco de dados SQLite** e **arquitetura cliente-servidor TCP**.

Projeto desenvolvido para a disciplina **Projeto Integrador de Computação Paralela** do curso de **Sistemas de Informação**.

---

## 📚 Funcionalidades

- Cadastro, listagem e remoção de livros
- Busca de livros por ID ou título
- Cadastro, listagem e remoção de usuários
- Empréstimo e devolução de livros
- Renovação de empréstimo (1 renovação por empréstimo)
- Fila de reservas automática
- Verificação automática de atrasos e bloqueio de usuários
- Histórico de operações com suporte a desfazer (undo)
- Relatório do acervo em tempo real
- Simulação de múltiplos usuários simultâneos
- Arquitetura cliente-servidor via TCP/IP

---

## 🧠 Estruturas de Dados Utilizadas

**Fila (Queue)**
Utilizada para organizar reservas de livros. Segue o princípio FIFO — quem reservou primeiro é atendido primeiro. Quando um livro é devolvido, a fila é processada automaticamente em background.

**Pilha (Stack)**
Utilizada para registrar o histórico de operações do sistema. Segue o princípio LIFO e suporta desfazer (undo) da última operação realizada.

Ambas as estruturas são **thread-safe**, protegidas por `threading.Lock()`.

---

## ⚙️ Concorrência e Paralelismo

O sistema utiliza **5 threads rodando em background** simultaneamente:

| Thread | Função |
|---|---|
| `fila_reservas` | Processa reservas automaticamente quando um livro fica disponível |
| `verif_atrasos` | Verifica empréstimos vencidos e bloqueia usuários em atraso |
| `relatorios` | Gera relatório periódico do acervo |
| `valid_livros` | Valida integridade dos livros no banco na inicialização |
| `valid_usuarios` | Valida integridade dos usuários no banco na inicialização |

O acesso concorrente ao banco é protegido por **mutexes por recurso** (`mutex_livros`, `mutex_usuarios`, `mutex_emprestimos`), garantindo exclusão mútua sem travar o sistema inteiro.

---

## 💾 Persistência de Dados

Os dados são armazenados em um banco **SQLite** local:

```
biblioteca.db
```

Substituindo o JSON da versão anterior, o SQLite oferece:
- Suporte a múltiplas threads com WAL mode
- Transações com rollback automático em caso de erro
- Validação de integridade com chaves estrangeiras e constraints

---

## 🌐 Arquitetura Cliente-Servidor

O sistema suporta dois modos de execução:

**Modo Standalone** — acesso direto ao banco, um terminal só:
```
main.py  →  database.py  →  biblioteca.db
```

**Modo Cliente-Servidor** — comunicação via TCP/IP na porta 5000:
```
cliente.py  →  TCP/JSON  →  servidor.py  →  database.py  →  biblioteca.db
```

O protocolo de comunicação é **JSON sobre TCP**. Exemplo de requisição:
```json
{"acao": "emprestar_livro", "usuario_id": 1, "livro_id": 2}
```
Exemplo de resposta:
```json
{"status": "ok", "mensagem": "Empréstimo realizado! Devolução prevista: 2026-06-04"}
```

---

## 🖥️ Interface

O sistema funciona via **CLI (Command Line Interface)**. Exemplo do menu:

```
========================================
  SISTEMA BIBLIOTECA — BiblioCore
========================================

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
```

---

## 🛠️ Tecnologias Utilizadas

- Python 3.10+
- `sqlite3` — banco de dados relacional local
- `threading` — concorrência com mutexes e eventos
- `socket` — comunicação TCP/IP cliente-servidor
- `json` — protocolo de comunicação entre cliente e servidor
- Estruturas de dados: Fila (Queue) e Pilha (Stack)

---

## 📂 Estrutura do Projeto

```
BiblioCore/
│
├── main.py           # Modo standalone — menu direto no terminal
├── servidor.py       # Servidor TCP (porta 5000)
├── cliente.py        # Cliente CLI que conecta ao servidor
├── models.py         # Classes Livro, Usuário e Empréstimo
├── database.py       # Camada de acesso ao SQLite (thread-safe)
├── queue_stack.py    # Fila de reservas e pilha de histórico
├── threads.py        # Threads de background e simulação
└── biblioteca.db     # Banco de dados (gerado automaticamente)
```

---

## ▶️ Como Executar

### Pré-requisito

Python 3.10 ou superior. Sem dependências externas — tudo usado é da biblioteca padrão do Python.

```bash
python --version
```

### Clonar o repositório

```bash
git clone https://github.com/tiagocosme1/Library-Management-Python.git
cd Library-Management-Python
```

### Modo Standalone (1 terminal)

```bash
python main.py
```

### Modo Cliente-Servidor (2 terminais)

**Terminal 1 — iniciar o servidor:**
```bash
python servidor.py
```

**Terminal 2 — iniciar o cliente:**
```bash
python cliente.py
```

O banco `biblioteca.db` é criado automaticamente na primeira execução.

---

## 👨‍💻 Autores

Projeto desenvolvido por:

- Tiago Geraldo de Lima Cosme
- Waldo Andrade Silva
- Álex de Almeida Santana
