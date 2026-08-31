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
# Nome de coisa: `DEPARTMENT_NAME`, `POSITION_NAME`.
SEMANTICA_ROTULO_ENTIDADE: str = "Rótulo / Nome de Entidade"
# Descrição com poucos valores distintos é categoria, não texto livre.
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
        # "ano" é subsequência de "aluno" (a-n-o ⊂ al-u-n-o); sem entrada
        # própria, `ANO_BASE` saía como dado pessoal.
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
        # dado público: `NOME_ORGAO_SUPERIOR` não é nome de pessoa.
        "orgao", "secretaria", "ministerio", "autarquia",
    ],
    # dado do TSE. Não inclui "candidato": `NOME_CANDIDATO` precisa
    # continuar sendo dado pessoal.
    "Processo Eleitoral": [
        "eleicao", "partido", "pleito", "coligacao", "chapa", "urna",
        "votacao", "sufragio", "candidatura",
    ],
    "Perfil do Colaborador": [
        "gender", "nationality", "career", "workforce", "staff",
        "genero", "nacionalidade", "idade", "raca", "escolaridade",
        "deficiencia", "etnia",
    ],
    # `NOME_PRODUTO` não é nome de pessoa.
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
    # Separado do papel "Valor Financeiro": `cost_center_code` é chave
    # (papel) que fala de custo (domínio).
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
# Tokens que descrevem o papel da coluna, não a entidade (em
# `nome_departamento`, `nome` é qualificador e `departamento` é a entidade).
TOKENS_QUALIFICADORES: frozenset[str] = frozenset({
    "id", "cod", "codigo", "code", "key", "chave", "pk", "fk", "nr", "num",
    "number", "matricula", "mat", "iden", "identifier", "registro",
    "nome", "name", "desc", "descricao", "description", "sigla", "abrev",
    "tipo", "type", "categoria", "class", "flag", "flg", "status",
    "qtd", "quantidade", "total", "vlr", "valor", "pct", "percentual",
    "dt", "date", "data", "hora", "time", "timestamp",
    # `PRAZO_ENTREGA_DIAS`: `dias` qualifica como contagem, não data.
    "dias",
    # `SQ_CANDIDATO_FORNECEDOR`: número sequencial, não nome de pessoa.
    "sequencial",
})

# Peso do token qualificador no ranking; perde para a entidade quando
# competem.
PESO_TOKEN_QUALIFICADOR: float = 0.45
PESO_TOKEN_ENTIDADE: float = 1.0

# Domínios que falam de gente — só neles "Nome" vira nome de pessoa.
DOMINIOS_DE_PESSOA: frozenset[str] = frozenset({"Perfil do Colaborador"})

# Acima disso a coluna vira texto, não categoria.
CARDINALIDADE_MAX_CATEGORIA: int = 100
