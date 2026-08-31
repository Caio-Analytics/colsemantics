"""Acúmulo e combinação de evidências semânticas.

Cada detector emite `Evidencia`; a combinação é por noisy-OR:
`1 - Π(1 - peso)`. Duas pistas de 0,5 dão 0,75; três dão 0,875.
"""
from dataclasses import dataclass
from typing import Any

EIXO_PAPEL = "papel"
EIXO_DOMINIO = "dominio"

# Diferença mínima entre a 1ª e a 2ª hipótese pra considerar conclusiva.
_MARGEM_CONCLUSIVA = 0.15


@dataclass(frozen=True)
class Evidencia:
    """Uma pista sobre o significado de uma coluna.

    `peso`: confiança da pista isolada (0-1). `origem`: texto exibido no
    relatório.
    """
    categoria: str
    eixo: str
    peso: float
    origem: str


def _noisy_or(pesos: list[float]) -> float:
    resultado = 1.0
    for peso in pesos:
        resultado *= 1.0 - max(0.0, min(1.0, peso))
    return 1.0 - resultado


def ranquear(evidencias: list[Evidencia], eixo: str) -> list[dict[str, Any]]:
    """Ranqueia as categorias candidatas de um eixo pelo peso combinado."""
    por_categoria: dict[str, list[Evidencia]] = {}
    for evidencia in evidencias:
        if evidencia.eixo == eixo:
            por_categoria.setdefault(evidencia.categoria, []).append(evidencia)

    ranking: list[dict[str, Any]] = [
        {
            "categoria": categoria,
            "confianca": round(_noisy_or([e.peso for e in itens]), 4),
            "origens": [e.origem for e in sorted(itens, key=lambda e: -e.peso)],
        }
        for categoria, itens in por_categoria.items()
    ]
    ranking.sort(key=lambda r: -float(r["confianca"]))
    return ranking


def escolher(ranking: list[dict[str, Any]]) -> tuple[str | None, float, str, bool]:
    """Escolhe a categoria vencedora de um ranking já ordenado.

    Devolve `(categoria, confiança, origem, conclusiva)`. `conclusiva` é
    falso quando a 2ª hipótese está perto demais da 1ª.
    """
    if not ranking:
        return None, 0.0, "Sem evidência", False
    melhor = ranking[0]
    margem = melhor["confianca"] - (ranking[1]["confianca"] if len(ranking) > 1 else 0.0)
    return (
        melhor["categoria"],
        float(melhor["confianca"]),
        " + ".join(melhor["origens"][:3]),
        bool(margem >= _MARGEM_CONCLUSIVA),
    )
