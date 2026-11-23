# Plataforma de Comércio Eletrônico — Núcleo Lógico em Python

Projeto final da disciplina de Estruturas de Dados (Tema 2: Plataforma de Comércio Eletrônico).

O sistema roda pelo terminal e usa as quatro estruturas fundamentais (**Lista, Pilha, Fila e Árvore**), cada uma com um papel no fluxo de uma loja virtual. Os dados ficam salvos em um arquivo texto (`dados_sistema.txt`), então não se perdem quando o programa é encerrado.

---

## 1. Como executar

### Pré-requisitos
- Python **3.8 ou superior** (não precisa instalar nenhuma biblioteca externa).

### Passo a passo
```bash
# 1. Clone o repositório
git clone https://github.com/gustavoobezerra/plataforma-ecommerce-estruturas-de-dados.git
cd plataforma-ecommerce-estruturas-de-dados

# 2. Execute o sistema
python main.py        # Windows
python3 main.py       # Linux / macOS
```

O sistema começa **vazio**. Para navegar, digite o número da opção e pressione Enter.

### Menu principal
```
1. Catálogo de produtos (Lista)
2. Departamentos e categorias (Árvore)
3. Carrinho de compras (Pilha)
4. Pagamentos (Fila)
5. Salvar dados
6. Carregar dados
0. Sair
```

### Fluxo sugerido (caminho feliz)
1. **Árvore (2 → 1):** cadastre a hierarquia, por exemplo `Eletronicos/Celulares/Smartphones`.
2. **Lista (1 → 1):** cadastre produtos e vincule cada um a uma categoria da árvore (se a categoria não existir, o sistema oferece criá-la).
3. **Pilha (3):** adicione e remova itens do carrinho, use **Desfazer** para voltar atrás e depois **Finalizar compra**.
4. **Fila (4):** o pedido finalizado entra no fim da fila. Use **Processar próximo** para aprovar ou recusar. Na aprovação, o estoque é baixado.
5. **Salvar (5):** grava tudo em `dados_sistema.txt`.
6. Feche o programa, abra de novo e use **Carregar (6)** para reconstruir o estado.

---

## 2. Operações por estrutura

| Estrutura | Implementação | Create | Read | Update | Delete |
|---|---|---|---|---|---|
| **Lista** (catálogo) | `list` de dicionários | `append` de novo produto | listar tudo / buscar por ID / acessar por índice | editar por ID | `pop(indice)` por ID |
| **Árvore** (departamentos) | `dict` aninhado | inserir caminho hierárquico | exibir a árvore recursivamente / navegar em um nó | renomear nó | remover nó e subárvore |
| **Pilha** (ações do carrinho) | `list` (`append`/`pop`) | *push* de ação ADICIONAR/REMOVER | ver o topo / ver a pilha e o carrinho | alterar a quantidade da ação do topo | *pop* (desfazer) |
| **Fila** (pagamentos) | `collections.deque` | `append` no fim | listar / consultar o início | alterar a forma de pagamento do primeiro | `popleft` (processar) |

As regras de cada estrutura são seguidas à risca: a Pilha só mexe no **topo**, a Fila só insere no **fim** e só remove do **início**, a Lista é manipulada por **índice/chave** e a Árvore por **caminho hierárquico**.

---

## 3. Justificativa técnica das estruturas

### Lista: catálogo de produtos
O catálogo é uma coleção de produtos que o usuário consulta, edita e remove em **qualquer posição**, e não apenas nas pontas. A `list` do Python oferece:
- **Acesso direto por índice em O(1)** (opção "Consultar por posição");
- **Inserção no fim em O(1) amortizado** (`append`), que é o cadastro de novos produtos;
- **Percorrer em ordem**, para listar o catálogo e filtrar produtos por categoria.

A busca por ID é linear, O(n), o que é adequado ao porte do sistema. Se o catálogo crescesse muito, um índice auxiliar `dict` (ID → produto) deixaria a busca em O(1). Pilha e fila não serviriam aqui, porque restringem o acesso às extremidades, e o catálogo precisa de acesso aleatório.

### Pilha: desfazer modificações no carrinho
"Desfazer" segue naturalmente a lógica **LIFO** (*Last In, First Out*): a última modificação feita é a primeira a ser revertida. Cada ação (ADICIONAR ou REMOVER, com produto e quantidade) é empilhada com `append` e desfeita com `pop`, ambas em **O(1)**.

Decisão de projeto: o carrinho **não é guardado separadamente**. Ele é **reconstruído reproduzindo as ações da pilha**, da base até o topo (função `calcular_carrinho`). Isso traz duas vantagens:
- **Desfazer é só um `pop`.** Não há "operação inversa" para programar, e o carrinho volta exatamente ao estado anterior.
- **Consistência garantida.** Pilha e carrinho nunca ficam dessincronizados, e persistir a pilha já é suficiente para restaurar o carrinho.

A `list` nativa é a pilha idiomática em Python, porque as operações acontecem na extremidade final, onde são O(1).

### Fila: processamento e aprovação de pagamentos
Pagamentos têm de ser tratados por **ordem de chegada** (**FIFO**, *First In, First Out*): seria injusto e arriscado aprovar um pedido posterior antes de um anterior (por exemplo, dois clientes disputando o último item em estoque). Por isso:
- Pedidos finalizados entram no **fim** (`append`);
- O processamento sempre retira do **início** (`popleft`).

Foi usado `collections.deque` em vez de `list` porque `list.pop(0)` custa **O(n)**: todos os elementos são deslocados. Já `deque.popleft()` custa **O(1)**. Em uma fila de pagamentos com alto volume, essa diferença evita um gargalo de processamento.

Na aprovação, o sistema confere o estoque de **todos** os itens antes de baixar qualquer um, então o pedido é aprovado inteiro ou recusado inteiro, sem baixa parcial.

### Árvore: departamentos, categorias e subcategorias
A organização da loja é **hierárquica por natureza**: um departamento contém categorias, que contêm subcategorias (`Eletronicos → Celulares → Smartphones`). Estruturas lineares (lista, pilha, fila) não representam relações pai-filho. A árvore representa.

Como o Python não tem árvore nativa, ela foi feita com **dicionários aninhados**: cada chave é um nó e seu valor é o dicionário de filhos (vazio = folha).
- **Navegar/buscar** um caminho custa O(profundidade), porque cada nível é uma consulta de `dict` em O(1) médio;
- **Inserir** reaproveita níveis existentes com `setdefault`;
- **Exibir** e **serializar** usam percurso recursivo em profundidade;
- **Remover** um nó elimina automaticamente toda a sua subárvore.

**Integração Lista ↔ Árvore:** todo produto guarda o caminho da sua categoria (ex.: `Eletronicos/Celulares`), que precisa existir na árvore. Ao renomear um nó, os produtos vinculados são atualizados. A remoção de um ramo que ainda tenha produtos é bloqueada, para não deixar produtos "órfãos".

---

## 4. Persistência (`dados_sistema.txt`)

Toda a persistência acontece em **um único arquivo texto**, sem banco de dados, JSON, CSV ou `pickle`. Cada linha começa com o identificador da estrutura, e os campos são separados por `|`. O caractere `|` é bloqueado na entrada do usuário para não corromper o arquivo.

```
ARVORE|Tecnologia|Celulares|Smartphones
ARVORE|Tecnologia|Informatica|Notebooks
ARVORE|Casa|Cozinha
LISTA|101|Galaxy S24|3999.90|8|Tecnologia/Celulares/Smartphones
LISTA|103|Liquidificador|250.00|5|Casa/Cozinha
PILHA|ADICIONAR|103|2
PILHA|REMOVER|103|1
FILA|2|Bruno|Boleto|80.00|
FILA|3|Ana|Pix|4249.90|101:1,103:1
CONTADOR|4
```

| Identificador | Campos |
|---|---|
| `ARVORE` | um nível por campo, da raiz até a folha (nós intermediários ficam implícitos) |
| `LISTA` | id, nome, preço, estoque, categoria |
| `PILHA` | ação, id do produto, quantidade, **da base para o topo** |
| `FILA` | id do pedido, cliente, forma de pagamento, valor, itens (`id:qtd,id:qtd`), **do início para o fim** |
| `CONTADOR` | próximo número de pedido, para que um pedido novo nunca repita o número de um antigo |

A **ordem das linhas preserva a semântica** de cada estrutura: ao carregar, a pilha é reempilhada na mesma sequência (o topo continua sendo o topo) e a fila é reenfileirada na mesma ordem de chegada. Linhas com formato inválido são ignoradas com um aviso, sem interromper o carregamento.

---

## 5. Organização do código (`main.py`)

O código está em um único arquivo, separado em seções:

1. **Configurações e estruturas globais:** as quatro estruturas, que começam vazias.
2. **Funções auxiliares de entrada:** leitura validada de texto, inteiros e decimais.
3. **Árvore:** inserir, buscar, exibir, renomear, remover e serializar caminhos.
4. **Lista:** cadastro, consulta por ID e índice, atualização e remoção.
5. **Pilha:** push, pop, peek, reconstrução do carrinho e finalização da compra.
6. **Fila:** enfileirar, consultar, atualizar e processar pagamentos.
7. **Persistência:** `salvar_dados()` e `carregar_dados()`.
8. **Menu principal:** ponto de entrada da CLI.

---

## 6. Estrutura do repositório

```
.
├── main.py              # código-fonte completo do sistema
├── README.md            # esta documentação
└── dados_sistema.txt    # gerado ao salvar (opção 5); não é versionado
```

---

## Autor

Gustavo de Oliveira Bezerra
