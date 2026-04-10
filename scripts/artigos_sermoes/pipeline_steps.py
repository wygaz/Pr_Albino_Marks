from __future__ import annotations

from dataclasses import dataclass

STEP_LABELS: dict[int, str] = {
    1: "Extrair artigos",
    2: "Preparar ambiente operacional",
    3: "Gerar prompts de imagem",
    4: "Gerar imagens",
    5: "Gerar PDFs de artigos",
    6: "Publicar artigos",
    7: "Gerar relatório técnico",
    8: "Gerar sermão",
    9: "Exportar formatos",
    10: "Pipeline completo",
    11: "Republicar artefatos existentes",
}


@dataclass
class OperationPlan:
    raw: str
    normalized: str
    steps: list[int]
    labels: list[str]
    valid: bool
    error: str = ""


def parse_operation_spec(spec: str | None) -> OperationPlan:
    raw = (spec or "").strip()
    if not raw:
        return OperationPlan(raw="", normalized="", steps=[], labels=[], valid=True)

    tokens = [tok.strip() for tok in raw.split(",") if tok.strip()]
    steps: list[int] = []
    try:
        for tok in tokens:
            if "-" in tok:
                parts = [p.strip() for p in tok.split("-") if p.strip()]
                if len(parts) != 2:
                    raise ValueError(f"Faixa invalida: {tok}")
                start, end = int(parts[0]), int(parts[1])
                if start > end:
                    start, end = end, start
                if start < 1 or end > 11:
                    raise ValueError(f"Faixa fora do intervalo 1-11: {tok}")
                steps.extend(range(start, end + 1))
            else:
                n = int(tok)
                if n < 1 or n > 11:
                    raise ValueError(f"Etapa fora do intervalo 1-11: {tok}")
                steps.append(n)
    except ValueError as exc:
        return OperationPlan(raw=raw, normalized="", steps=[], labels=[], valid=False, error=str(exc))

    seen: set[int] = set()
    unique_steps: list[int] = []
    for step in sorted(steps):
        if step not in seen:
            seen.add(step)
            unique_steps.append(step)

    labels = [STEP_LABELS[s] for s in unique_steps]
    normalized = ",".join(str(s) for s in unique_steps)
    return OperationPlan(raw=raw, normalized=normalized, steps=unique_steps, labels=labels, valid=True)
