"""
Plataforma de Comércio Eletrônico — Núcleo Lógico
==================================================

Projeto final de Estruturas de Dados (Tema 2).

Estruturas utilizadas e seus papéis:
    LISTA  (list)              -> Catálogo geral de produtos ativos na loja.
    PILHA  (list: append/pop)  -> Pilha de ações do carrinho, permitindo "desfazer".
    FILA   (collections.deque) -> Ordem de processamento/aprovação de pagamentos.
    ÁRVORE (dicts aninhados)   -> Hierarquia Departamento > Categoria > Subcategoria.

Persistência: arquivo texto único "dados_sistema.txt", delimitado por "|".
"""

from collections import deque

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES E ESTRUTURAS GLOBAIS (o sistema inicia totalmente vazio)
# ---------------------------------------------------------------------------

ARQUIVO_DADOS = "dados_sistema.txt"
SEP = "|"           # Delimitador dos campos no arquivo
SEP_CAMINHO = "/"   # Separador dos níveis da árvore (ex.: Eletronicos/Celulares)

# LISTA: cada produto é um dicionário {id, nome, preco, estoque, categoria}
catalogo = []

# ÁRVORE: dicionários aninhados. Cada chave é um nó; o valor é o dicionário de filhos.
# Ex.: {"Eletronicos": {"Celulares": {"Smartphones": {}}}}
arvore_departamentos = {}

# PILHA: cada elemento é uma ação {acao: "ADICIONAR"/"REMOVER", produto_id, qtd}.
# O topo é o último elemento da lista (pilha_acoes[-1]).
pilha_acoes = []

# FILA: cada elemento é um pedido aguardando aprovação de pagamento.
# Inserção no fim (append) e remoção no início (popleft), ambas O(1) com deque.
fila_pagamentos = deque()

# Contador para gerar IDs de pedidos únicos
contadores = {"pedido": 1}


# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES DE ENTRADA
# ---------------------------------------------------------------------------

def ler_texto(mensagem, permitir_vazio=False):
    """Lê um texto do usuário, impedindo o caractere delimitador do arquivo."""
    while True:
        valor = input(mensagem).strip()
        if SEP in valor:
            print(f"  [!] O caractere '{SEP}' não é permitido.")
            continue
        if not valor and not permitir_vazio:
            print("  [!] Valor obrigatório.")
            continue
        return valor


def ler_inteiro(mensagem, minimo=None, permitir_vazio=False):
    """Lê um número inteiro, com valor mínimo opcional. Retorna None se vazio permitido."""
    while True:
        valor = input(mensagem).strip()
        if not valor and permitir_vazio:
            return None
        try:
            numero = int(valor)
        except ValueError:
            print("  [!] Digite um número inteiro válido.")
            continue
        if minimo is not None and numero < minimo:
            print(f"  [!] O valor deve ser maior ou igual a {minimo}.")
            continue
        return numero


def ler_decimal(mensagem, minimo=0.0, permitir_vazio=False):
    """Lê um número decimal (aceita vírgula ou ponto)."""
    while True:
        valor = input(mensagem).strip().replace(",", ".")
        if not valor and permitir_vazio:
            return None
        try:
            numero = float(valor)
        except ValueError:
            print("  [!] Digite um valor numérico válido.")
            continue
        if numero < minimo:
            print(f"  [!] O valor deve ser maior ou igual a {minimo}.")
            continue
        return numero


def confirmar(mensagem):
    """Pergunta de sim/não."""
    return input(f"{mensagem} (s/n): ").strip().lower() == "s"


def formatar_moeda(valor):
    return f"R$ {valor:.2f}"


# ---------------------------------------------------------------------------
# ÁRVORE — Departamentos, categorias e subcategorias (dicionários aninhados)
# ---------------------------------------------------------------------------

def caminho_de_texto(texto):
    """Converte 'A/B/C' em ['A', 'B', 'C'], ignorando níveis vazios."""
    return [parte.strip() for parte in texto.split(SEP_CAMINHO) if parte.strip()]


def texto_de_caminho(caminho):
    """Converte ['A', 'B', 'C'] em 'A/B/C'."""
    return SEP_CAMINHO.join(caminho)


def arvore_obter_no(caminho):
    """Desce a árvore nível a nível. Retorna o dicionário de filhos do nó ou None."""
    no = arvore_departamentos
    for nome in caminho:
        if nome not in no:
            return None
        no = no[nome]
    return no


def arvore_inserir_caminho(caminho):
    """
    Insere um caminho hierárquico. Níveis inexistentes são criados;
    níveis existentes são reaproveitados (setdefault). Retorna True se criou algo novo.
    """
    no = arvore_departamentos
    criou = False
    for nome in caminho:
        if nome not in no:
            criou = True
        no = no.setdefault(nome, {})
    return criou


def arvore_exibir(no=None, nivel=0):
    """Imprime a árvore recursivamente, com recuo proporcional à profundidade."""
    if no is None:
        no = arvore_departamentos
    for nome, filhos in no.items():
        prefixo = "    " * nivel + ("└── " if nivel > 0 else "■ ")
        print(prefixo + nome)
        arvore_exibir(filhos, nivel + 1)


def arvore_listar_caminhos(no=None, prefixo=None):
    """
    Percorre a árvore em profundidade e devolve todos os caminhos até as folhas.
    Usado na persistência: cada folha vira uma linha ARVORE|nivel1|nivel2|...
    (os nós intermediários ficam implícitos no caminho).
    """
    if no is None:
        no = arvore_departamentos
    if prefixo is None:
        prefixo = []
    caminhos = []
    for nome, filhos in no.items():
        atual = prefixo + [nome]
        if filhos:
            caminhos.extend(arvore_listar_caminhos(filhos, atual))
        else:
            caminhos.append(atual)
    return caminhos


def produtos_na_categoria(caminho):
    """Retorna os produtos cuja categoria é o caminho informado ou está abaixo dele."""
    alvo = texto_de_caminho(caminho)
    return [p for p in catalogo
            if p["categoria"] == alvo or p["categoria"].startswith(alvo + SEP_CAMINHO)]


def arvore_renomear(caminho, novo_nome):
    """Renomeia um nó preservando a ordem dos irmãos e atualiza os produtos vinculados."""
    pai = arvore_obter_no(caminho[:-1])
    antigo = caminho[-1]
    if pai is None or antigo not in pai:
        return False, "Nó não encontrado."
    if novo_nome in pai:
        return False, "Já existe um nó com esse nome neste nível."

    # Reconstrói o dicionário do pai para manter a posição original do nó
    itens = list(pai.items())
    pai.clear()
    for nome, filhos in itens:
        pai[novo_nome if nome == antigo else nome] = filhos

    # Atualiza a categoria dos produtos que apontavam para o caminho antigo
    antigo_txt = texto_de_caminho(caminho)
    novo_txt = texto_de_caminho(caminho[:-1] + [novo_nome])
    for p in catalogo:
        if p["categoria"] == antigo_txt:
            p["categoria"] = novo_txt
        elif p["categoria"].startswith(antigo_txt + SEP_CAMINHO):
            p["categoria"] = novo_txt + p["categoria"][len(antigo_txt):]
    return True, "Nó renomeado."


def arvore_remover(caminho):
    """Remove um nó e toda a sua subárvore, desde que não haja produtos vinculados."""
    pai = arvore_obter_no(caminho[:-1])
    if pai is None or caminho[-1] not in pai:
        return False, "Nó não encontrado."
    vinculados = produtos_na_categoria(caminho)
    if vinculados:
        return False, f"Existem {len(vinculados)} produto(s) vinculados a este ramo."
    del pai[caminho[-1]]
    return True, "Nó (e subníveis) removido."


def menu_arvore():
    while True:
        print("\n--- DEPARTAMENTOS / CATEGORIAS (Árvore) ---")
        print("1. Inserir departamento/categoria/subcategoria")
        print("2. Exibir hierarquia completa")
        print("3. Navegar em um nó (ver filhos e produtos)")
        print("4. Renomear nó")
        print("5. Remover nó")
        print("0. Voltar")
        opcao = input("Opção: ").strip()

        if opcao == "1":
            print(f"Informe o caminho separado por '{SEP_CAMINHO}' "
                  "(ex.: Eletronicos/Celulares/Smartphones)")
            caminho = caminho_de_texto(ler_texto("Caminho: "))
            if not caminho:
                print("  [!] Caminho inválido.")
            elif arvore_inserir_caminho(caminho):
                print(f"  [OK] Caminho '{texto_de_caminho(caminho)}' inserido.")
            else:
                print("  [i] Esse caminho já existia.")

        elif opcao == "2":
            if not arvore_departamentos:
                print("  [i] Nenhum departamento cadastrado.")
            else:
                arvore_exibir()

        elif opcao == "3":
            caminho = caminho_de_texto(ler_texto("Caminho do nó: "))
            no = arvore_obter_no(caminho)
            if no is None or not caminho:
                print("  [!] Nó não encontrado.")
            else:
                print(f"Nó: {texto_de_caminho(caminho)}")
                print("Filhos diretos:", ", ".join(no.keys()) if no else "(nenhum — é folha)")
                produtos = produtos_na_categoria(caminho)
                print(f"Produtos neste ramo: {len(produtos)}")
                for p in produtos:
                    print(f"   #{p['id']} {p['nome']} — {formatar_moeda(p['preco'])}")

        elif opcao == "4":
            caminho = caminho_de_texto(ler_texto("Caminho do nó a renomear: "))
            if not caminho:
                print("  [!] Caminho inválido.")
                continue
            novo = ler_texto("Novo nome: ")
            if SEP_CAMINHO in novo:
                print(f"  [!] O nome não pode conter '{SEP_CAMINHO}'.")
                continue
            ok, msg = arvore_renomear(caminho, novo)
            print(("  [OK] " if ok else "  [!] ") + msg)

        elif opcao == "5":
            caminho = caminho_de_texto(ler_texto("Caminho do nó a remover: "))
            if caminho and confirmar(f"Remover '{texto_de_caminho(caminho)}' e todos os subníveis?"):
                ok, msg = arvore_remover(caminho)
                print(("  [OK] " if ok else "  [!] ") + msg)

        elif opcao == "0":
            return
        else:
            print("  [!] Opção inválida.")


# ---------------------------------------------------------------------------
# LISTA — Catálogo de produtos (manipulação por índice/chave)
# ---------------------------------------------------------------------------

def lista_buscar_indice(produto_id):
    """Busca linear pelo ID; retorna o índice na lista ou -1."""
    for indice, produto in enumerate(catalogo):
        if produto["id"] == produto_id:
            return indice
    return -1


def lista_buscar_produto(produto_id):
    indice = lista_buscar_indice(produto_id)
    return catalogo[indice] if indice != -1 else None


def ler_categoria_valida(permitir_vazio=False):
    """
    Lê o caminho da categoria e garante que ele exista na árvore.
    Integra Lista e Árvore: todo produto pertence a um nó da hierarquia.
    """
    while True:
        texto = ler_texto("Categoria (ex.: Eletronicos/Celulares): ", permitir_vazio)
        if not texto and permitir_vazio:
            return None
        caminho = caminho_de_texto(texto)
        if not caminho:
            print("  [!] Caminho inválido.")
            continue
        if arvore_obter_no(caminho) is None:
            if confirmar("  Categoria inexistente na árvore. Deseja criá-la agora?"):
                arvore_inserir_caminho(caminho)
            else:
                continue
        return texto_de_caminho(caminho)


def lista_adicionar(produto_id, nome, preco, estoque, categoria):
    """Insere um produto no fim da lista (append)."""
    catalogo.append({"id": produto_id, "nome": nome, "preco": preco,
                     "estoque": estoque, "categoria": categoria})


def lista_exibir(produtos):
    if not produtos:
        print("  [i] Nenhum produto para exibir.")
        return
    print(f"{'Pos':<4}{'ID':<6}{'Nome':<25}{'Preço':>12}{'Estoque':>9}  Categoria")
    for p in produtos:
        pos = lista_buscar_indice(p["id"])
        print(f"{pos:<4}{p['id']:<6}{p['nome'][:24]:<25}{formatar_moeda(p['preco']):>12}"
              f"{p['estoque']:>9}  {p['categoria']}")


def produto_no_carrinho(produto_id):
    return calcular_carrinho().get(produto_id, 0) > 0


def menu_lista():
    while True:
        print("\n--- CATÁLOGO DE PRODUTOS (Lista) ---")
        print("1. Cadastrar produto")
        print("2. Listar todos os produtos")
        print("3. Consultar produto por ID")
        print("4. Consultar produto por posição (índice)")
        print("5. Atualizar produto")
        print("6. Remover produto")
        print("0. Voltar")
        opcao = input("Opção: ").strip()

        if opcao == "1":
            produto_id = ler_inteiro("ID do produto: ", minimo=1)
            if lista_buscar_indice(produto_id) != -1:
                print("  [!] Já existe um produto com esse ID.")
                continue
            nome = ler_texto("Nome: ")
            preco = ler_decimal("Preço: ", minimo=0.01)
            estoque = ler_inteiro("Estoque: ", minimo=0)
            categoria = ler_categoria_valida()
            lista_adicionar(produto_id, nome, preco, estoque, categoria)
            print("  [OK] Produto cadastrado.")

        elif opcao == "2":
            lista_exibir(catalogo)

        elif opcao == "3":
            produto = lista_buscar_produto(ler_inteiro("ID: "))
            lista_exibir([produto] if produto else [])

        elif opcao == "4":
            indice = ler_inteiro("Posição (0 a n-1): ", minimo=0)
            if indice < len(catalogo):
                lista_exibir([catalogo[indice]])  # acesso direto por índice: O(1)
            else:
                print("  [!] Posição fora da lista.")

        elif opcao == "5":
            produto = lista_buscar_produto(ler_inteiro("ID do produto a atualizar: "))
            if not produto:
                print("  [!] Produto não encontrado.")
                continue
            print("Deixe em branco para manter o valor atual.")
            nome = ler_texto(f"Nome [{produto['nome']}]: ", permitir_vazio=True)
            preco = ler_decimal(f"Preço [{produto['preco']:.2f}]: ", 0.01, permitir_vazio=True)
            estoque = ler_inteiro(f"Estoque [{produto['estoque']}]: ", 0, permitir_vazio=True)
            print(f"Categoria atual: {produto['categoria']}")
            categoria = ler_categoria_valida(permitir_vazio=True)
            if nome:
                produto["nome"] = nome
            if preco is not None:
                produto["preco"] = preco
            if estoque is not None:
                produto["estoque"] = estoque
            if categoria:
                produto["categoria"] = categoria
            print("  [OK] Produto atualizado.")

        elif opcao == "6":
            produto_id = ler_inteiro("ID do produto a remover: ")
            indice = lista_buscar_indice(produto_id)
            if indice == -1:
                print("  [!] Produto não encontrado.")
            elif produto_no_carrinho(produto_id):
                print("  [!] O produto está no carrinho. Remova-o do carrinho antes.")
            else:
                removido = catalogo.pop(indice)  # remoção por índice
                print(f"  [OK] Produto '{removido['nome']}' removido.")

        elif opcao == "0":
            return
        else:
            print("  [!] Opção inválida.")


# ---------------------------------------------------------------------------
# PILHA — Ações do carrinho com "desfazer" (LIFO)
# ---------------------------------------------------------------------------

def pilha_empilhar(acao, produto_id, qtd):
    """Push: insere a ação no topo da pilha."""
    pilha_acoes.append({"acao": acao, "produto_id": produto_id, "qtd": qtd})


def pilha_desempilhar():
    """Pop: remove a ação do topo (desfazer). Retorna None se vazia."""
    return pilha_acoes.pop() if pilha_acoes else None


def pilha_topo():
    """Peek: consulta o topo sem remover."""
    return pilha_acoes[-1] if pilha_acoes else None


def calcular_carrinho(acoes=None):
    """
    O carrinho NÃO é armazenado separadamente: ele é reconstruído
    "reproduzindo" as ações da pilha da base até o topo. Assim, desfazer
    (pop) a última ação automaticamente reverte o carrinho ao estado anterior.
    """
    if acoes is None:
        acoes = pilha_acoes
    carrinho = {}
    for a in acoes:
        sinal = 1 if a["acao"] == "ADICIONAR" else -1
        carrinho[a["produto_id"]] = carrinho.get(a["produto_id"], 0) + sinal * a["qtd"]
    return {pid: q for pid, q in carrinho.items() if q > 0}


def validar_acao(acao, produto_id, qtd, carrinho):
    """Verifica se uma ação é possível sobre um determinado estado do carrinho."""
    atual = carrinho.get(produto_id, 0)
    if acao == "ADICIONAR":
        produto = lista_buscar_produto(produto_id)
        if not produto:
            return False, "Produto não existe no catálogo."
        if atual + qtd > produto["estoque"]:
            return False, f"Estoque insuficiente (disponível: {produto['estoque']}, no carrinho: {atual})."
    else:
        if qtd > atual:
            return False, f"O carrinho só possui {atual} unidade(s) desse produto."
    return True, ""


def exibir_carrinho():
    carrinho = calcular_carrinho()
    if not carrinho:
        print("  [i] Carrinho vazio.")
        return 0.0
    total = 0.0
    for pid, qtd in carrinho.items():
        produto = lista_buscar_produto(pid)
        nome = produto["nome"] if produto else "(produto removido)"
        preco = produto["preco"] if produto else 0.0
        subtotal = preco * qtd
        total += subtotal
        print(f"  #{pid} {nome:<25} {qtd:>3} x {formatar_moeda(preco):>12} = {formatar_moeda(subtotal):>12}")
    print(f"  TOTAL: {formatar_moeda(total)}")
    return total


def exibir_pilha():
    if not pilha_acoes:
        print("  [i] Pilha de ações vazia.")
        return
    print("  (topo)")
    for a in reversed(pilha_acoes):  # do topo para a base
        print(f"  {a['acao']:<10} produto #{a['produto_id']} — qtd {a['qtd']}")
    print("  (base)")


def finalizar_compra():
    """Transforma o carrinho em um pedido no FIM da fila de pagamentos."""
    carrinho = calcular_carrinho()
    if not carrinho:
        print("  [!] Carrinho vazio.")
        return
    total = exibir_carrinho()
    cliente = ler_texto("Nome do cliente: ")
    metodo = ler_texto("Forma de pagamento (Pix/Cartao/Boleto): ")
    pedido_id = fila_enfileirar(cliente, metodo, total, carrinho)
    pilha_acoes.clear()  # compra concluída: o histórico de ações do carrinho é zerado
    print(f"  [OK] Pedido #{pedido_id} enviado para a fila de pagamentos "
          f"(posição {len(fila_pagamentos)}).")


def menu_pilha():
    while True:
        print("\n--- CARRINHO DE COMPRAS (Pilha de ações) ---")
        print("1. Adicionar produto ao carrinho (push)")
        print("2. Remover produto do carrinho (push)")
        print("3. Ver carrinho e pilha de ações")
        print("4. Ver última ação (topo)")
        print("5. Alterar quantidade da última ação (topo)")
        print("6. Desfazer última ação (pop)")
        print("7. Finalizar compra (envia para a fila de pagamentos)")
        print("0. Voltar")
        opcao = input("Opção: ").strip()

        if opcao in ("1", "2"):
            acao = "ADICIONAR" if opcao == "1" else "REMOVER"
            produto_id = ler_inteiro("ID do produto: ")
            qtd = ler_inteiro("Quantidade: ", minimo=1)
            ok, msg = validar_acao(acao, produto_id, qtd, calcular_carrinho())
            if ok:
                pilha_empilhar(acao, produto_id, qtd)
                print(f"  [OK] Ação '{acao}' empilhada.")
            else:
                print("  [!] " + msg)

        elif opcao == "3":
            print("Carrinho:")
            exibir_carrinho()
            print("Pilha de ações:")
            exibir_pilha()

        elif opcao == "4":
            topo = pilha_topo()
            print(f"  Topo: {topo['acao']} produto #{topo['produto_id']} — qtd {topo['qtd']}"
                  if topo else "  [i] Pilha vazia.")

        elif opcao == "5":
            topo = pilha_topo()
            if not topo:
                print("  [i] Pilha vazia.")
                continue
            nova_qtd = ler_inteiro(f"Nova quantidade [{topo['qtd']}]: ", minimo=1)
            # Valida contra o carrinho como estava ANTES da ação do topo
            ok, msg = validar_acao(topo["acao"], topo["produto_id"], nova_qtd,
                                   calcular_carrinho(pilha_acoes[:-1]))
            if ok:
                topo["qtd"] = nova_qtd
                print("  [OK] Ação do topo atualizada.")
            else:
                print("  [!] " + msg)

        elif opcao == "6":
            desfeita = pilha_desempilhar()
            if desfeita:
                print(f"  [OK] Desfeito: {desfeita['acao']} produto #{desfeita['produto_id']} "
                      f"(qtd {desfeita['qtd']}).")
            else:
                print("  [i] Nada para desfazer.")

        elif opcao == "7":
            finalizar_compra()

        elif opcao == "0":
            return
        else:
            print("  [!] Opção inválida.")


# ---------------------------------------------------------------------------
# FILA — Processamento e aprovação de pagamentos (FIFO)
# ---------------------------------------------------------------------------

def fila_enfileirar(cliente, metodo, valor, itens):
    """Enqueue: insere o pedido no FIM da fila."""
    pedido_id = contadores["pedido"]
    contadores["pedido"] += 1
    fila_pagamentos.append({"id": pedido_id, "cliente": cliente, "metodo": metodo,
                            "valor": valor, "itens": dict(itens)})
    return pedido_id


def fila_frente():
    """Consulta o primeiro da fila sem removê-lo."""
    return fila_pagamentos[0] if fila_pagamentos else None


def descrever_pedido(p):
    itens = ", ".join(f"#{pid} x{q}" for pid, q in p["itens"].items()) or "(sem itens)"
    return (f"Pedido #{p['id']} | {p['cliente']} | {p['metodo']} | "
            f"{formatar_moeda(p['valor'])} | Itens: {itens}")


def processar_pagamento():
    """
    Dequeue: retira o pedido do INÍCIO da fila e decide aprovação.
    Na aprovação, o estoque é baixado; se faltar estoque, o pagamento é recusado.
    """
    pedido = fila_frente()
    if not pedido:
        print("  [i] Nenhum pagamento pendente.")
        return
    print("Processando: " + descrever_pedido(pedido))
    aprovar = confirmar("Aprovar pagamento?")
    fila_pagamentos.popleft()  # remoção sempre no início (FIFO)

    if not aprovar:
        print(f"  [X] Pedido #{pedido['id']} RECUSADO.")
        return

    # Confere o estoque de todos os itens antes de baixar qualquer um (operação atômica)
    for pid, qtd in pedido["itens"].items():
        produto = lista_buscar_produto(pid)
        if not produto or produto["estoque"] < qtd:
            print(f"  [X] Pedido #{pedido['id']} RECUSADO: estoque insuficiente do produto #{pid}.")
            return
    for pid, qtd in pedido["itens"].items():
        lista_buscar_produto(pid)["estoque"] -= qtd
    print(f"  [OK] Pedido #{pedido['id']} APROVADO. Estoque atualizado.")


def menu_fila():
    while True:
        print("\n--- PAGAMENTOS (Fila) ---")
        print("1. Registrar pagamento avulso (entra no fim da fila)")
        print("2. Listar fila de pagamentos")
        print("3. Consultar próximo pagamento (início)")
        print("4. Atualizar forma de pagamento do próximo")
        print("5. Processar próximo pagamento (aprovar/recusar)")
        print("0. Voltar")
        opcao = input("Opção: ").strip()

        if opcao == "1":
            cliente = ler_texto("Cliente: ")
            metodo = ler_texto("Forma de pagamento: ")
            valor = ler_decimal("Valor: ", minimo=0.01)
            pedido_id = fila_enfileirar(cliente, metodo, valor, {})
            print(f"  [OK] Pedido #{pedido_id} enfileirado (posição {len(fila_pagamentos)}).")

        elif opcao == "2":
            if not fila_pagamentos:
                print("  [i] Fila vazia.")
            for posicao, p in enumerate(fila_pagamentos, start=1):
                print(f"  {posicao}º  " + descrever_pedido(p))

        elif opcao == "3":
            p = fila_frente()
            print("  " + descrever_pedido(p) if p else "  [i] Fila vazia.")

        elif opcao == "4":
            p = fila_frente()
            if not p:
                print("  [i] Fila vazia.")
                continue
            p["metodo"] = ler_texto(f"Nova forma de pagamento [{p['metodo']}]: ")
            print("  [OK] Pedido atualizado.")

        elif opcao == "5":
            processar_pagamento()

        elif opcao == "0":
            return
        else:
            print("  [!] Opção inválida.")


# ---------------------------------------------------------------------------
# PERSISTÊNCIA EM ARQUIVO TEXTO
# ---------------------------------------------------------------------------

def itens_para_texto(itens):
    """{1: 2, 5: 1} -> '1:2,5:1'"""
    return ",".join(f"{pid}:{qtd}" for pid, qtd in itens.items())


def texto_para_itens(texto):
    """'1:2,5:1' -> {1: 2, 5: 1}"""
    itens = {}
    for par in texto.split(","):
        if par:
            pid, qtd = par.split(":")
            itens[int(pid)] = int(qtd)
    return itens


def salvar_dados():
    """
    Exporta o estado da memória para o disco. A ordem das linhas importa:
      - ARVORE primeiro (produtos referenciam categorias);
      - PILHA da base para o topo (para reempilhar na mesma ordem);
      - FILA do início para o fim (para preservar a ordem de chegada);
      - CONTADOR por último (próximo número de pedido, para não repetir IDs).
    """
    linhas = []
    for caminho in arvore_listar_caminhos():
        linhas.append(SEP.join(["ARVORE"] + caminho))
    for p in catalogo:
        linhas.append(SEP.join(["LISTA", str(p["id"]), p["nome"], f"{p['preco']:.2f}",
                                str(p["estoque"]), p["categoria"]]))
    for a in pilha_acoes:
        linhas.append(SEP.join(["PILHA", a["acao"], str(a["produto_id"]), str(a["qtd"])]))
    for f in fila_pagamentos:
        linhas.append(SEP.join(["FILA", str(f["id"]), f["cliente"], f["metodo"],
                                f"{f['valor']:.2f}", itens_para_texto(f["itens"])]))
    linhas.append(SEP.join(["CONTADOR", str(contadores["pedido"])]))

    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
        for linha in linhas:
            arquivo.write(linha + "\n")
    print(f"  [OK] {len(linhas)} registro(s) salvos em '{ARQUIVO_DADOS}'.")


def carregar_dados():
    """Limpa as estruturas e as reconstrói a partir do arquivo texto."""
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
            linhas = arquivo.read().splitlines()
    except FileNotFoundError:
        print(f"  [!] Arquivo '{ARQUIVO_DADOS}' não encontrado. Salve os dados primeiro.")
        return

    # Esvazia as estruturas mantendo os mesmos objetos (evita variáveis globais reatribuídas)
    catalogo.clear()
    arvore_departamentos.clear()
    pilha_acoes.clear()
    fila_pagamentos.clear()

    carregados, ignorados = 0, 0
    contador_salvo = 1
    for numero, linha in enumerate(linhas, start=1):
        if not linha.strip():
            continue
        campos = linha.split(SEP)
        tipo = campos[0]
        try:
            if tipo == "ARVORE" and len(campos) >= 2:
                arvore_inserir_caminho(campos[1:])
            elif tipo == "LISTA" and len(campos) == 6:
                lista_adicionar(int(campos[1]), campos[2], float(campos[3]),
                                int(campos[4]), campos[5])
            elif tipo == "PILHA" and len(campos) == 4:
                pilha_empilhar(campos[1], int(campos[2]), int(campos[3]))
            elif tipo == "FILA" and len(campos) == 6:
                fila_pagamentos.append({"id": int(campos[1]), "cliente": campos[2],
                                        "metodo": campos[3], "valor": float(campos[4]),
                                        "itens": texto_para_itens(campos[5])})
            elif tipo == "CONTADOR" and len(campos) == 2:
                contador_salvo = int(campos[1])
            else:
                raise ValueError("formato desconhecido")
            carregados += 1
        except ValueError:
            ignorados += 1
            print(f"  [!] Linha {numero} ignorada (formato inválido): {linha}")

    # O próximo ID de pedido continua de onde parou (linha CONTADOR). Se o arquivo
    # não tiver essa linha, usa o maior ID que ainda está na fila + 1.
    maior_id_na_fila = max((p["id"] for p in fila_pagamentos), default=0)
    contadores["pedido"] = max(contador_salvo, maior_id_na_fila + 1)
    print(f"  [OK] {carregados} registro(s) carregados de '{ARQUIVO_DADOS}'"
          + (f" ({ignorados} ignorado(s))." if ignorados else "."))


# ---------------------------------------------------------------------------
# MENU PRINCIPAL
# ---------------------------------------------------------------------------

def menu_principal():
    print("=" * 52)
    print("   PLATAFORMA DE COMÉRCIO ELETRÔNICO — Núcleo")
    print("=" * 52)
    while True:
        print("\n=========== MENU PRINCIPAL ===========")
        print(f"1. Catálogo de produtos (Lista)        [{len(catalogo)} produto(s)]")
        print(f"2. Departamentos e categorias (Árvore) [{len(arvore_departamentos)} depto(s)]")
        print(f"3. Carrinho de compras (Pilha)         [{len(pilha_acoes)} ação(ões)]")
        print(f"4. Pagamentos (Fila)                   [{len(fila_pagamentos)} pendente(s)]")
        print("5. Salvar dados")
        print("6. Carregar dados")
        print("0. Sair")
        opcao = input("Opção: ").strip()

        if opcao == "1":
            menu_lista()
        elif opcao == "2":
            menu_arvore()
        elif opcao == "3":
            menu_pilha()
        elif opcao == "4":
            menu_fila()
        elif opcao == "5":
            salvar_dados()
        elif opcao == "6":
            carregar_dados()
        elif opcao == "0":
            if confirmar("Deseja salvar antes de sair?"):
                salvar_dados()
            print("Sistema encerrado.")
            return
        else:
            print("  [!] Opção inválida.")


if __name__ == "__main__":
    try:
        menu_principal()
    except (KeyboardInterrupt, EOFError):
        print("\nSistema encerrado.")
