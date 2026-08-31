"""colsemantics: inferência semântica de colunas por acúmulo de evidências.

Dois eixos: papel (o que a coluna é) e domínio (do que ela fala).
Ex: `nome_departamento` -> papel "Nome", domínio "Estrutura Organizacional".

Detectores independentes emitem evidências com peso; combinação por
noisy-OR. Duas passadas — a segunda desambigua com os domínios já
resolvidos da primeira (contexto de tabela resolve `dep`: departamento,
dependente ou depósito).
"""
from typing import Any

from . import _taxonomy as config
from .detectors import (
    PAPEIS_ESTRUTURAIS,
    PerfilConteudo,
    por_assinatura_estrutural,
    por_contexto_da_tabela,
    por_fuzzy,
    por_gazetteer,
    por_padrao_conteudo,
    por_token_forte,
)
from .evidence import EIXO_DOMINIO, EIXO_PAPEL, Evidencia, escolher, ranquear
from .tokens import expandir_abreviatura, normalizar, tokenizar

__version__ = "0.1.1"

__all__ = [
    "Evidencia",
    "PAPEIS_ESTRUTURAIS",
    "PerfilConteudo",
    "expandir_abreviatura",
    "inferir_semantica",
    "inferir_semanticas_da_tabela",
    "normalizar",
    "semanticas_para_gap_analysis",
    "tokenizar",
]

# Confiança mínima pra um domínio da 1ª passada entrar no contexto de
# desambiguação.
_CONFIANCA_MINIMA_CONTEXTO = 0.7

# Piso pra afirmar um domínio; abaixo disso fica só em `hipoteses`.
_CONFIANCA_MINIMA_DOMINIO = 0.5

_MAX_HIPOTESES = 4


def _coletar_evidencias(
    nome_col: str,
    detectado_padrao: str,
    perfil: PerfilConteudo | None,
) -> list[Evidencia]:
    tokens = tokenizar(nome_col)
    nome_limpo = normalizar(nome_col)

    evidencias: list[Evidencia] = []
    evidencias += por_padrao_conteudo(detectado_padrao)
    evidencias += por_token_forte(tokens)
    evidencias += por_fuzzy(nome_limpo, tokens)

    if perfil is not None:
        evidencias += por_gazetteer(perfil)
        evidencias += por_assinatura_estrutural(perfil)

    return evidencias


def _refinar_papel(papel: str | None, dominio: str | None, perfil: PerfilConteudo | None) -> str | None:
    """Ajusta o papel com o domínio e a cardinalidade da coluna.

    FULL_NAME (pessoa) x DEPARTMENT_NAME (rótulo de entidade): separa pelo
    domínio. JOB_DESCRIPTION (texto livre) x SHIFT_TYPE_DESC (poucos
    valores -> categoria): separa pela cardinalidade.
    """
    if papel == config.SEMANTICA_NOME_PESSOA:
        if dominio is not None and dominio not in config.DOMINIOS_DE_PESSOA:
            return config.SEMANTICA_ROTULO_ENTIDADE
    elif papel == config.SEMANTICA_TEXTO_LIVRE and perfil is not None:
        cardinalidade_de_dimensao = (
            1 < perfil.n_unicos <= config.CARDINALIDADE_MAX_CATEGORIA
            and perfil.ratio_unicidade < 0.5
        )
        if cardinalidade_de_dimensao:
            return config.SEMANTICA_CATEGORIA
    return papel


def _montar_resultado(
    evidencias: list[Evidencia], perfil: PerfilConteudo | None = None
) -> dict[str, Any]:
    ranking_papel = ranquear(evidencias, EIXO_PAPEL)
    ranking_dominio = ranquear(evidencias, EIXO_DOMINIO)

    papel, conf_papel, origem_papel, papel_conclusivo = escolher(ranking_papel)
    dominio, conf_dominio, origem_dominio, _ = escolher(ranking_dominio)

    # Abaixo do piso, o domínio fica só em `hipoteses`, não vira fato.
    # `cod_dep` sem outra pista de estrutura organizacional é palpite.
    dominio_incerto = dominio is not None and conf_dominio < _CONFIANCA_MINIMA_DOMINIO
    if dominio_incerto:
        dominio, conf_dominio, origem_dominio = None, 0.0, "Sem evidência"

    papel = _refinar_papel(papel, dominio, perfil)

    # Papel estrutural decide o tratamento no pipeline. Papel "fraco" (Nome,
    # Texto Descritivo) só descreve a forma; aí o domínio importa mais.
    if papel in PAPEIS_ESTRUTURAIS:
        semantica, confianca, origem = papel, conf_papel, origem_papel
    elif dominio is not None:
        semantica, confianca, origem = dominio, conf_dominio, origem_dominio
    elif papel is not None:
        semantica, confianca, origem = papel, conf_papel, origem_papel
    else:
        semantica, confianca, origem = config.SEMANTICA_GENERICA, 0.0, "Unmatched"

    hipoteses = sorted(
        [{"semantica": r["categoria"], "eixo": eixo, "confianca": r["confianca"],
          "evidencias": r["origens"][:3]}
         for eixo, ranking in ((EIXO_PAPEL, ranking_papel), (EIXO_DOMINIO, ranking_dominio))
         for r in ranking],
        key=lambda h: -h["confianca"],
    )[:_MAX_HIPOTESES]

    return {
        "semantica": semantica,
        "papel": papel,
        "dominio": dominio,
        "confianca_score": round(confianca, 4),
        "origem": origem,
        # Conclusiva exige os dois eixos resolvidos. `diretoria` só tem
        # domínio e nenhum papel — está resolvida, entra no contexto mesmo
        # assim.
        "conclusiva": not (bool(ranking_papel) and not papel_conclusivo) and not dominio_incerto,
        "hipoteses": hipoteses,
    }


def inferir_semantica(
    nome_col: str,
    detectado_padrao: str = "Nenhum",
    perfil: PerfilConteudo | None = None,
) -> dict[str, Any]:
    """Infere papel, domínio e semântica primária de uma coluna isolada.

    `perfil` habilita os detectores de conteúdo (gazetteer, assinatura
    estrutural). Sem ele, a inferência usa só o nome.
    """
    return _montar_resultado(_coletar_evidencias(nome_col, detectado_padrao, perfil), perfil)


def inferir_semanticas_da_tabela(entradas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Infere a semântica de todas as colunas, com desambiguação por contexto.

    Cada entrada: `{"nome": str, "padrao": str, "perfil": PerfilConteudo}`.

    Passada 1 classifica cada coluna isolada. Passada 2 monta o assunto da
    tabela a partir do que ficou confiante e reprocessa só as colunas
    inconclusivas (`cod_dep` numa tabela de RH -> departamento).
    """
    evidencias_por_coluna: list[list[Evidencia]] = []
    resultados: list[dict[str, Any]] = []
    for entrada in entradas:
        evidencias = _coletar_evidencias(
            str(entrada["nome"]), entrada.get("padrao", "Nenhum"), entrada.get("perfil")
        )
        evidencias_por_coluna.append(evidencias)
        resultados.append(_montar_resultado(evidencias, entrada.get("perfil")))

    contexto = _perfil_de_assunto(resultados)
    if not contexto:
        return resultados

    for indice, (entrada, resultado) in enumerate(zip(entradas, resultados, strict=True)):
        if resultado["conclusiva"]:
            continue
        extras = por_contexto_da_tabela(tokenizar(str(entrada["nome"])), contexto)
        if not extras:
            continue
        resultados[indice] = _montar_resultado(
            evidencias_por_coluna[indice] + extras, entrada.get("perfil")
        )

    return resultados


def _perfil_de_assunto(resultados: list[dict[str, Any]]) -> dict[str, float]:
    """Resume o assunto da tabela a partir das colunas já classificadas.

    Só entram categorias com confiança acima do piso — contexto de palpite
    propagaria erro em vez de desambiguar.
    """
    forcas: dict[str, float] = {}
    for resultado in resultados:
        if not resultado["conclusiva"]:
            continue
        for categoria in (resultado["papel"], resultado["dominio"]):
            if not categoria or categoria == config.SEMANTICA_GENERICA:
                continue
            if resultado["confianca_score"] < _CONFIANCA_MINIMA_CONTEXTO:
                continue
            forcas[categoria] = max(forcas.get(categoria, 0.0), resultado["confianca_score"])
    return forcas


def semanticas_para_gap_analysis(registro: dict[str, Any]) -> list[str]:
    """Todas as semânticas que uma coluna aporta a uma análise de cobertura.

    `cod_departamento` aporta tanto "Chave Identificadora" quanto
    "Estrutura Organizacional".
    """
    return [
        v for v in (registro.get("semantica"), registro.get("papel"), registro.get("dominio"))
        if v and v != config.SEMANTICA_GENERICA
    ]
