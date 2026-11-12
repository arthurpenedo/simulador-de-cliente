from simulador_de_cliente.personas import PERSONAS, Persona, no_papel
from simulador_de_cliente.rubrica import DIMENSOES, Avaliacao, relatorio


def test_fala_longa_demais_nao_e_de_cliente():
    persona = next(iter(PERSONAS.values()))
    ok, motivo = no_papel(persona, "problema " * 81)
    assert not ok and "longa demais" in motivo


def test_fala_proibida_da_persona_e_apontada():
    persona = next(p for p in PERSONAS.values() if p.proibidas)
    modelo = Persona.__dataclass_fields__  # a persona real é só um molde; troca as proibidas por um padrão simples
    assert "proibidas" in modelo
    from dataclasses import replace
    p = replace(persona, proibidas=(r"\bgolpe\b",))
    ok, motivo = no_papel(p, "Isso parece um golpe")
    assert not ok and "fora do perfil" in motivo
    assert no_papel(p, "Quero entender a cobrança")[0] is True


def _av(nota: int) -> Avaliacao:
    return Avaliacao({d: nota for d in DIMENSOES}, {d: [] for d in DIMENSOES})


def test_relatorio_lista_dicas_quando_ha_nota_baixa():
    texto = relatorio(_av(1))
    assert "Total: 3/6" in texto
    assert "Onde melhorar:" in texto


def test_relatorio_sem_dicas_quando_tudo_certo():
    texto = relatorio(_av(2))
    assert "Total: 6/6" in texto
    assert "Onde melhorar" not in texto
