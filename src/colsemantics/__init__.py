from dataclasses import dataclass, field
from typing import Any

from . import _taxonomy as config
from .context import SemanticContext, current_context
from .detectors import (
    PAPEIS_ESTRUTURAIS as _STRUCTURAL_ROLES,
)
from .detectors import (
    PerfilConteudo as _LegacyContentProfile,
)
from .detectors import (
    por_assinatura_estrutural,
    por_contexto_da_tabela,
    por_fuzzy,
    por_gazetteer,
    por_padrao_conteudo,
    por_token_forte,
)
from .evidence import EIXO_DOMINIO, EIXO_PAPEL, Evidencia, escolher, ranquear
from .tokens import normalizar, tokenizar
from .vocabularies import export_overrides_template, load_vocabularies, temporary_vocabulary

__version__ = "0.3.0"

__all__ = [
    "ContentProfile",
    "SemanticContext",
    "current_context",
    "infer_column",
    "infer_table",
    "normalizar",
    "load_vocabularies",
    "temporary_vocabulary",
    "export_overrides_template",
    "tokenizar",
]


@dataclass
class ContentProfile:
    data_type: str = ""
    distinct_values: list[str] = field(default_factory=list)
    distinct_count: int = 0
    uniqueness_ratio: float = 0.0
    mean_string_length: float | None = None
    fixed_length: bool = False
    skewness: float | None = None
    minimum: float | None = None
    monotonically_increasing: bool = False
    fixed_decimal_places: int | None = None


_CATEGORY_LABELS = {
    "Genérico / Não mapeado": "Generic / Unmapped",
    "Data / Calendário": "Date / Calendar",
    "Chave Identificadora (ID)": "Identifier (ID)",
    "Texto Descritivo Livre": "Free-form Text",
    "Nome / Identificação Pessoal": "Person Name / Identifier",
    "Rótulo / Nome de Entidade": "Entity Label / Name",
    "Categoria / Classificação": "Category / Classification",
    "Status / Indicador / Flag": "Status / Indicator / Flag",
    "Valor Financeiro": "Financial Value",
    "Quantidade / Métrica": "Quantity / Metric",
    "Contato / Rede": "Contact / Network",
    "Resultado de Avaliação": "Assessment Result",
    "Localização Geográfica": "Geographic Location",
    "Estrutura Organizacional": "Organizational Structure",
    "Perfil do Colaborador": "Workforce Profile",
    "Produto / Item": "Product / Item",
    "Cargo / Função": "Job / Function",
    "Financeiro / Custo": "Finance / Cost",
    "Curso / Treinamento": "Course / Training",
    "Processo Eleitoral": "Electoral Process",
}


_CONFIANCA_MINIMA_CONTEXTO = 0.7


_CONFIANCA_MINIMA_DOMINIO = 0.5

_MAX_HIPOTESES = 4


def _coletar_evidencias(
    nome_col: str,
    detectado_padrao: str,
    perfil: _LegacyContentProfile | None,
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


def _refinar_papel(
    papel: str | None, dominio: str | None, perfil: _LegacyContentProfile | None
) -> str | None:
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
    evidencias: list[Evidencia], perfil: _LegacyContentProfile | None = None
) -> dict[str, Any]:
    ranking_papel = ranquear(evidencias, EIXO_PAPEL)
    ranking_dominio = ranquear(evidencias, EIXO_DOMINIO)

    papel, conf_papel, origem_papel, papel_conclusivo = escolher(ranking_papel)
    dominio, conf_dominio, origem_dominio, _ = escolher(ranking_dominio)

    dominio_incerto = dominio is not None and conf_dominio < _CONFIANCA_MINIMA_DOMINIO
    if dominio_incerto:
        dominio, conf_dominio, origem_dominio = None, 0.0, "Sem evidência"

    papel = _refinar_papel(papel, dominio, perfil)

    if papel in _STRUCTURAL_ROLES:
        semantica, confianca, origem = papel, conf_papel, origem_papel
    elif dominio is not None:
        semantica, confianca, origem = dominio, conf_dominio, origem_dominio
    elif papel is not None:
        semantica, confianca, origem = papel, conf_papel, origem_papel
    else:
        semantica, confianca, origem = config.SEMANTICA_GENERICA, 0.0, "Unmatched"

    hipoteses = sorted(
        [
            {
                "semantica": r["categoria"],
                "eixo": eixo,
                "confianca": r["confianca"],
                "evidencias": r["origens"][:3],
            }
            for eixo, ranking in ((EIXO_PAPEL, ranking_papel), (EIXO_DOMINIO, ranking_dominio))
            for r in ranking
        ],
        key=lambda h: -h["confianca"],
    )[:_MAX_HIPOTESES]

    return {
        "semantica": semantica,
        "papel": papel,
        "dominio": dominio,
        "confianca_score": round(confianca, 4),
        "origem": origem,
        "conclusiva": not (bool(ranking_papel) and not papel_conclusivo) and not dominio_incerto,
        "hipoteses": hipoteses,
    }


def _infer_column(
    nome_col: str,
    detectado_padrao: str = "Nenhum",
    perfil: _LegacyContentProfile | None = None,
) -> dict[str, Any]:
    override = current_context().column_overrides.get(nome_col)
    if override:
        axis = EIXO_PAPEL if override in _STRUCTURAL_ROLES else EIXO_DOMINIO
        result = _montar_resultado([Evidencia(override, axis, 1.0, "vocabulary override")], perfil)
        result["conclusiva"] = True
        return result
    return _montar_resultado(_coletar_evidencias(nome_col, detectado_padrao, perfil), perfil)


def _infer_table(entradas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidencias_por_coluna: list[list[Evidencia]] = []
    resultados: list[dict[str, Any]] = []
    for entrada in entradas:
        nome = str(entrada["nome"])
        override = current_context().column_overrides.get(nome)
        evidencias = (
            [
                Evidencia(
                    override,
                    EIXO_PAPEL if override in _STRUCTURAL_ROLES else EIXO_DOMINIO,
                    1.0,
                    "vocabulary override",
                )
            ]
            if override
            else _coletar_evidencias(nome, entrada.get("padrao", "Nenhum"), entrada.get("perfil"))
        )
        evidencias_por_coluna.append(evidencias)
        resultado = _montar_resultado(evidencias, entrada.get("perfil"))
        if override:
            resultado["conclusiva"] = True
        resultados.append(resultado)

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


def _semantics_for_gap_analysis(registro: dict[str, Any]) -> list[str]:
    return [
        v
        for v in (registro.get("semantica"), registro.get("papel"), registro.get("dominio"))
        if v and v != config.SEMANTICA_GENERICA
    ]


def _english_result(result: dict[str, Any]) -> dict[str, Any]:
    hypotheses = [
        {
            "semantic": _CATEGORY_LABELS.get(item["semantica"], item["semantica"]),
            "axis": "role" if item["eixo"] == EIXO_PAPEL else "domain",
            "confidence": item["confianca"],
            "evidence": item["evidencias"],
        }
        for item in result["hipoteses"]
    ]
    return {
        "semantic": _CATEGORY_LABELS.get(result["semantica"], result["semantica"]),
        "role": _CATEGORY_LABELS.get(result["papel"], result["papel"]),
        "domain": _CATEGORY_LABELS.get(result["dominio"], result["dominio"]),
        "confidence": result["confianca_score"],
        "evidence": result["origem"],
        "conclusive": result["conclusiva"],
        "hypotheses": hypotheses,
    }


def _legacy_profile(profile: ContentProfile | None) -> _LegacyContentProfile | None:
    if profile is None:
        return None
    return _LegacyContentProfile(
        tipo_dados=profile.data_type,
        valores_distintos=profile.distinct_values,
        n_unicos=profile.distinct_count,
        ratio_unicidade=profile.uniqueness_ratio,
        str_len_media=profile.mean_string_length,
        comprimento_fixo=profile.fixed_length,
        assimetria=profile.skewness,
        minimo=profile.minimum,
        monotonica_crescente=profile.monotonically_increasing,
        casas_decimais_fixas=profile.fixed_decimal_places,
    )


def infer_column(
    column_name: str,
    detected_pattern: str = "None",
    profile: ContentProfile | None = None,
) -> dict[str, Any]:
    pattern = "Nenhum" if detected_pattern == "None" else detected_pattern
    return _english_result(_infer_column(column_name, pattern, _legacy_profile(profile)))


def infer_table(columns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries = [
        {
            "nome": column.get("column_name", column.get("name")),
            "padrao": column.get("detected_pattern", column.get("pattern", "Nenhum")),
            "perfil": _legacy_profile(column.get("profile")),
        }
        for column in columns
    ]
    return [_english_result(result) for result in _infer_table(entries)]
