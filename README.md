# colsemantics

Infere o papel de uma coluna (o que ela é: chave, data, valor financeiro...)
e o domínio (do que ela fala: estrutura organizacional, cargo,
localidade...) a partir do nome, de abreviações corporativas e do conteúdo.

`cd_dpto_lot` não está em nenhum dicionário, mas a abreviatura reconstrói
`codigo` / `departamento` / `lotacao` e o conteúdo confirma baixa
cardinalidade:

```python
from colsemantics import inferir_semantica

inferir_semantica("cd_dpto_lot")
# {
#   "semantica": "Chave Identificadora (ID)",
#   "papel": "Chave Identificadora (ID)",
#   "dominio": "Estrutura Organizacional",
#   "confianca_score": 0.87,
#   "origem": "abreviatura 'cd' → 'codigo' + abreviatura 'lot' → 'lotacao'",
#   "conclusiva": True,
#   "hipoteses": [...],
# }
```

## Como funciona

Cascata de detectores independentes, combinados por noisy-OR
(`1 - Π(1 - peso)` — pistas fracas se somam):

1. Padrão de conteúdo validado (CPF, CNPJ, e-mail...).
2. Token forte — match exato contra dicionário curado, com abreviações expandidas (`vl` → `valor`).
3. Fuzzy (Jaro-Winkler) — nome parecido com palavra-chave de domínio, tolera erro de digitação.
4. Gazetteer de conteúdo — valores batem com um conjunto fechado (UFs, meses, sexo/gênero...), independente do nome.
5. Assinatura estrutural — forma dos dados (inteiro crescente e único, decimal de 2 casas assimétrico...).
6. Contexto da tabela — colunas vizinhas já resolvidas desambiguam abreviaturas ambíguas (`dep`: departamento, dependente ou depósito).

## Instalação

```bash
pip install colsemantics
```

## Uso

### Uma coluna isolada

```python
from colsemantics import inferir_semantica

inferir_semantica("nome_departamento")
# semântica = "Estrutura Organizacional" (domínio vence: "nome" é só a forma)

inferir_semantica("uf")
# semântica = "Localização Geográfica"
```

### Com o conteúdo da coluna (resolve nomes opacos)

```python
from colsemantics import PerfilConteudo, inferir_semantica

perfil = PerfilConteudo(
    tipo_dados="Texto",
    valores_distintos=["SP", "RJ", "MG", "BA"],
    n_unicos=4,
    ratio_unicidade=4 / 40,
)
inferir_semantica("f27", perfil=perfil)["semantica"]
# "Localização Geográfica"
```

`PerfilConteudo` é um dataclass simples — todos os campos são opcionais além
dos primeiros, então passe só o que você já sabe sobre a coluna:

| campo | o que é |
|---|---|
| `tipo_dados` | `"Texto"`, `"Número Inteiro"`, `"Número Decimal"`, `"Booleano"`... |
| `valores_distintos` | amostra de valores únicos (usada pelo gazetteer) |
| `n_unicos`, `ratio_unicidade` | cardinalidade |
| `str_len_media`, `comprimento_fixo` | forma do texto |
| `assimetria`, `minimo`, `casas_decimais_fixas` | forma do número |
| `monotonica_crescente` | sinal de chave sequencial |

### Uma tabela inteira (desambiguação por contexto)

```python
from colsemantics import inferir_semanticas_da_tabela

resultados = inferir_semanticas_da_tabela([
    {"nome": "matricula", "padrao": "Nenhum", "perfil": None},
    {"nome": "nome_func", "padrao": "Nenhum", "perfil": None},
    {"nome": "cod_dep",   "padrao": "Nenhum", "perfil": None},
    {"nome": "diretoria", "padrao": "Nenhum", "perfil": None},
])
# "cod_dep" sozinho é ambíguo (departamento? dependente? depósito?).
# Com "diretoria" na mesma tabela, o contexto resolve para "Estrutura Organizacional".
```

`padrao` é o que seu próprio detector de padrão estruturado encontrou no
conteúdo (`"CPF"`, `"CNPJ"`, `"UUID"`, `"E-mail"`, `"Telefone"`, `"CEP"` ou
`"Nenhum"`) — `colsemantics` não faz essa detecção, só consome o resultado.

## O que a saída traz

```python
{
    "semantica": str,       # papel estrutural, ou domínio quando o papel é só formal
    "papel": str | None,
    "dominio": str | None,
    "confianca_score": float,   # 0-1, noisy-OR das evidências
    "origem": str,               # por que — as evidências que decidiram
    "conclusiva": bool,          # False = havia ambiguidade, olhe "hipoteses"
    "hipoteses": list[dict],     # até 4 alternativas ranqueadas, com evidência cada
}
```

## Licença

MIT. Extraído do módulo de inferência semântica do
[Recon](https://github.com/Caio-Analytics/Recon), ferramenta de profiling de
dados desconhecidos.
