"""Taxonomia e thresholds da inferência semântica.

Este módulo é só dado: categorias, regexes de vocabulário e limiares. Toda a
lógica que consome esses valores vive em `detectors.py`, `tokens.py` e
`vocabulary.py`.
"""

# ── Nomes de categorias/papéis referenciados fora deste módulo ─────────────
SEMANTICA_GENERICA: str = "Genérico / Não mapeado"
SEMANTICA_DATA_CALENDARIO: str = "Data / Calendário"
SEMANTICA_CHAVE_ID: str = "Chave Identificadora (ID)"
SEMANTICA_TEXTO_LIVRE: str = "Texto Descritivo Livre"
SEMANTICA_NOME_PESSOA: str = "Nome / Identificação Pessoal"
# Nome *de coisa*: `DEPARTMENT_NAME`, `POSITION_NAME`. Sem este papel, tudo que
# terminava em `_NAME` virava nome de pessoa.
SEMANTICA_ROTULO_ENTIDADE: str = "Rótulo / Nome de Entidade"
# Coluna de descrição com poucos valores distintos é categoria, não texto: quem
# vai modelar precisa saber que aquilo vira dimensão, não campo livre.
SEMANTICA_CATEGORIA: str = "Categoria / Classificação"

# ── Thresholds gerais ────────────────────────────────────────────────────
THRESHOLD_FUZZY_PADRAO: float = 0.85
THRESHOLD_FUZZY_CURTO: float = 0.95

# ── Categorias fortes (match exato por token) ───────────────────────────────
CATEGORIAS_FORTES: dict[str, list[str]] = {
    SEMANTICA_CHAVE_ID: [
        "id", "cod", "codigo", "code", "key", "number", "matricula", "mat",
        "cpf", "cnpj", "registro", "chave", "identifier", "iden", "nr", "num", "pk", "fk",
        "sequencial",
    ],
    SEMANTICA_DATA_CALENDARIO: [
        "date", "dt", "data", "time", "timestamp", "periodo", "competencia",
        "admissao", "demissao", "nascimento", "vencimento", "inicio", "fim",
        "prazo", "realizacao", "referencia", "vigencia", "expiracao",
        # Sem "ano" cadastrado, o token não tinha vocabulário próprio e caía
        # no palpite de abreviatura: "ano" é subsequência de "aluno"
        # (a-n-o ⊂ al-u-n-o), e `ANO_BASE` saía marcada como dado pessoal
        # (LGPD) com recomendação de mascarar — apagaria a série temporal
        # inteira se aplicada sem checar.
        "ano",
    ],
    "Status / Indicador / Flag": [
        "status", "flg", "flag", "is", "has", "state", "situacao",
        "enforced", "ativo", "inativo", "habilitado", "bloqueado",
    ],
    "Valor Financeiro": [
        "salario", "salary", "wage", "remuneracao", "vlr", "valor",
        "custo", "cost", "preco", "price", "receita", "revenue",
        "despesa", "expense", "budget", "orcamento", "bonus",
        "comissao", "honorario", "verba", "provisao", "encargo",
    ],
    "Quantidade / Métrica": [
        "qtd", "quantidade", "count", "total", "volume", "horas", "dias", "carga",
        "duracao", "frequencia", "score", "nota", "percentual", "pct",
        "indice", "taxa", "ratio", "proporcao", "media",
    ],
    "Texto Descritivo Livre": [
        "desc", "descricao", "description", "obs", "observacao", "comentario",
        "justificativa", "detalhe", "motivo", "complemento", "historico",
        "task", "function", "resumo", "anotacao", "mensagem",
    ],
    "Nome / Identificação Pessoal": [
        "nome", "name", "colaborador", "funcionario", "empregado",
        "pessoa", "participante", "aluno", "candidato", "usuario", "user",
    ],
    "Contato / Rede": [
        "email", "mail", "telefone", "celular", "ramal",
        "whatsapp", "contato", "fone", "phone",
    ],
    "Resultado de Avaliação": [
        "resultado", "result", "aprovacao", "reprovacao", "conceito",
        "avaliacao", "desempenho", "conclusao", "outcome", "performance",
        "feedback", "rating", "classificacao",
    ],
}

# ── Categorias fuzzy (Jaro-Winkler) ─────────────────────────────────────────
CATEGORIAS_FUZZY: dict[str, list[str]] = {
    "Localização Geográfica": [
        "country", "province", "city", "facility", "pais", "cidade",
        "estado", "regiao", "municipio", "cep", "uf", "endereco", "local",
        "latitude", "longitude", "bairro", "logradouro",
    ],
    "Estrutura Organizacional": [
        "department", "company", "business", "hierarquia", "departamento",
        "diretoria", "gerencia", "setor", "area", "divisao", "celula",
        "squad", "lotacao", "unidade", "filial", "subsidiaria", "agencia",
        "coordenacao", "superintendencia", "nucleo", "equipe", "time",
        # Vocabulário de dado público brasileiro: sem "orgao"/"secretaria",
        # `NOME_ORGAO_SUPERIOR` (nome do órgão do governo, não de pessoa)
        # não tinha domínio nenhum pra competir com o default de nome
        # pessoal do qualificador "nome".
        "orgao", "secretaria", "ministerio", "autarquia",
    ],
    # Vocabulário de processo eleitoral (dados do TSE): sem domínio próprio,
    # `NM_PARTIDO`/`NM_TIPO_ELEICAO` (nome do partido, tipo de eleição — não
    # de pessoa) ficavam sem nada pra competir com o qualificador "nome" e
    # saíam como dado pessoal. Não inclui "candidato" de propósito: um
    # candidato é uma pessoa, e a coluna `NOME_CANDIDATO` precisa continuar
    # sendo dado pessoal — misturar o termo aqui derrubaria isso.
    "Processo Eleitoral": [
        "eleicao", "partido", "pleito", "coligacao", "chapa", "urna",
        "votacao", "sufragio", "candidatura",
    ],
    "Perfil do Colaborador": [
        "gender", "nationality", "career", "workforce", "staff",
        "genero", "nacionalidade", "idade", "raca", "escolaridade",
        "deficiencia", "etnia",
    ],
    # Sem este domínio, `NOME_PRODUTO` não tinha nenhuma categoria de domínio
    # para competir com "Perfil do Colaborador" vazio, e o papel "Nome" caía
    # no default de nome de pessoa — mesmo bug de `DEPARTMENT_NAME`, só que
    # sem um domínio já cadastrado para resolvê-lo. Qualquer "nome de coisa"
    # que caia fora dos domínios já cadastrados ainda tem esse risco; este é o
    # caso mais comum (produto/item/SKU), não uma cobertura exaustiva.
    "Produto / Item": [
        "product", "item", "sku", "merchandise", "produto", "mercadoria",
        "insumo", "material", "ativo", "equipamento", "veiculo", "artigo",
        "marca", "brand", "modelo", "model",
    ],
    "Cargo / Função": [
        "cargo", "funcao", "nivel", "grade", "posicao", "categoria",
        "classe", "faixa", "perfil", "role", "position", "job",
        "title", "occupation",
    ],
    # Domínio financeiro separado do *papel* "Valor Financeiro": `cost_center_code`
    # é uma chave (papel) que fala de custo (domínio). Sem esta categoria, a
    # evidência de `cost` só tinha o eixo de papel para disputar, e a coluna
    # saía como valor monetário — pronta para alguém somar um centro de custo.
    "Financeiro / Custo": [
        "custo", "cost", "centro de custo", "despesa", "orcamento", "budget",
        "financeiro", "finance", "contabil", "fiscal", "conta", "rateio",
    ],
    "Curso / Treinamento": [
        "curso", "treinamento", "capacitacao", "formacao", "modulo",
        "trilha", "programa", "workshop", "disciplina", "tema",
        "course", "training", "learning", "certificacao",
    ],
}

# ── Qualificadores estruturais de nome de coluna ────────────────────────────
# Tokens que descrevem o *papel* da coluna, não a *entidade* de que ela trata.
# Em `nome_departamento` o `nome` é qualificador e `departamento` é a entidade:
# a coluna é sobre estrutura organizacional, não sobre uma pessoa. Sem essa
# distinção o desempate cai no comprimento da palavra e erra sistematicamente.
TOKENS_QUALIFICADORES: frozenset[str] = frozenset({
    "id", "cod", "codigo", "code", "key", "chave", "pk", "fk", "nr", "num",
    "number", "matricula", "mat", "iden", "identifier", "registro",
    "nome", "name", "desc", "descricao", "description", "sigla", "abrev",
    "tipo", "type", "categoria", "class", "flag", "flg", "status",
    "qtd", "quantidade", "total", "vlr", "valor", "pct", "percentual",
    "dt", "date", "data", "hora", "time", "timestamp",
    # Unidade de duração: `PRAZO_ENTREGA_DIAS` tem `prazo` (que É data em outros
    # contextos, como "data de prazo") competindo com `dias`, que qualifica a
    # coluna como contagem, não data. Sem `dias` como borda, `prazo` vencia
    # sozinho e uma coluna numérica de dias virava "Data / Calendário".
    "dias",
    # `SQ_CANDIDATO_FORNECEDOR` (dado real do TSE) é um número sequencial que
    # referencia um candidato — não o nome dele. Sem `sequencial` como borda,
    # `candidato` (palavra forte de nome de pessoa) vencia sozinho.
    "sequencial",
})

# Peso do token qualificador no ranking semântico. Ele ainda conta (um
# `id_x` continua tendo cara de identificador) mas perde para a entidade
# quando as duas categorias competem.
PESO_TOKEN_QUALIFICADOR: float = 0.45
PESO_TOKEN_ENTIDADE: float = 1.0

# Domínios que falam de gente. Só neles um papel "Nome" é nome de pessoa: em
# `DEPARTMENT_NAME` (Estrutura Organizacional) o nome é de um departamento.
DOMINIOS_DE_PESSOA: frozenset[str] = frozenset({"Perfil do Colaborador"})

# Acima desta cardinalidade a coluna deixa de ser categoria e vira texto de
# verdade. 79 mil linhas com 4 valores distintos são uma dimensão.
CARDINALIDADE_MAX_CATEGORIA: int = 100
