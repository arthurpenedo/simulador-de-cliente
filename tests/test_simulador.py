import json

from simulador_de_cliente import backends
from simulador_de_cliente.backends import OllamaBackend, RoteiroBackend, criar_backend
from simulador_de_cliente.benchmark import acerto_curados, rodar
from simulador_de_cliente.cli import main
from simulador_de_cliente.personas import PERSONAS, no_papel
from simulador_de_cliente.rubrica import avaliar_texto, avaliar_turnos
from simulador_de_cliente.simulador import simular
from simulador_de_cliente.sintetico import AtendenteSintetico, avaliar_acerto


def test_senha_pedida_e_violacao_mas_negada_nao():
    assert avaliar_texto("Qual é a sua senha?").notas["seguranca"] == 0
    assert avaliar_texto("Nunca peço sua senha, use o aplicativo oficial.").notas["seguranca"] == 2


def test_hostilidade_zera_empatia_mesmo_com_cortesia():
    assert avaliar_texto("Bom dia. Calma, não é problema meu.").notas["empatia"] == 0


def test_promessa_fora_da_regra_zera_politica():
    assert avaliar_texto("Garanto o reembolso, vou abrir o protocolo.").notas["politica"] == 0
    assert avaliar_texto("Vou abrir o protocolo, prazo de 5 dias.").notas["politica"] == 2


def test_violacao_em_qualquer_turno_derruba_a_conversa():
    av = avaliar_turnos(["Entendo, sinto muito.", "Me passe o CVV."])
    assert av.notas["seguranca"] == 0
    assert any("cvv" in e for e in av.evidencias["seguranca"])
    assert av.dicas()


def test_no_papel_pega_quebra_de_personagem():
    p = PERSONAS["irritado"]
    assert no_papel(p, "Como assistente, posso ajudar você com isso.")[0] is False
    assert no_papel(p, "")[0] is False
    assert no_papel(p, "Isso é um absurdo!")[0] is True


def test_atendente_bom_acalma_e_ruim_escala():
    cliente = RoteiroBackend()
    for persona in PERSONAS.values():
        bom = simular(persona, AtendenteSintetico(2, 1), cliente)
        ruim = simular(persona, AtendenteSintetico(0, 1), cliente)
        assert bom.desfecho == "bom", persona.id
        assert ruim.desfecho == "ruim", persona.id


def test_golpista_vaza_dado_encerra_na_hora():
    r = simular(PERSONAS["golpista"], lambda h: "Qual é a sua senha do app?", RoteiroBackend())
    assert r.desfecho == "ruim" and r.humor_final >= 9
    assert len(r.turnos) == 2


def test_atendente_vazio_encerra():
    r = simular(PERSONAS["irritado"], lambda h: "", RoteiroBackend())
    assert r.desfecho == "atendente encerrou"


def test_acerto_da_rubrica_supera_baseline():
    ac = avaliar_acerto(150, 1)
    assert ac["media"] > ac["baseline"] + 0.3
    certos, total, _ = acerto_curados()
    assert certos >= total - 3


def test_benchmark_gera_tabelas_e_e_deterministico():
    a, b = rodar(5, 30, 3), rodar(5, 30, 3)
    assert a == b and "| golpista | bom |" in a


def test_ollama_monta_requisicao_e_le_resposta(monkeypatch):
    capturado = {}

    class Resp:
        def read(self):
            return json.dumps({"message": {"content": " Cadê meu dinheiro? "}}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def falso(req, timeout):
        capturado["url"], capturado["corpo"] = req.full_url, json.loads(req.data)
        return Resp()

    monkeypatch.setattr(backends.urllib.request, "urlopen", falso)
    p = PERSONAS["irritado"]
    fala = OllamaBackend("m").responder(p, [("cliente", "oi"), ("atendente", "olá")], 7)
    assert fala == "Cadê meu dinheiro?"
    assert capturado["url"].endswith("/api/chat")
    papeis = [m["role"] for m in capturado["corpo"]["messages"]]
    assert papeis == ["system", "assistant", "user"]
    assert "7/10" in capturado["corpo"]["messages"][0]["content"]


def test_motor_desconhecido():
    try:
        criar_backend("x")
    except ValueError:
        return
    raise AssertionError


def test_cli_treinar_auto_e_avaliar(tmp_path, capsys):
    arq = tmp_path / "c.json"
    assert main(["treinar", "irritado", "--auto", "bom", "--salvar", str(arq)]) == 0
    saida = capsys.readouterr().out
    assert "Desfecho: cliente acalmado" in saida and "Total:" in saida
    assert main(["avaliar", str(arq)]) == 0
    assert "empatia" in capsys.readouterr().out


def test_demo_html_tem_tres_conversas_e_notas():
    from simulador_de_cliente.demo import gerar_html
    html = gerar_html()
    assert html.count("class='conv'") == 3
    assert "atendente bom" in html and "atendente ruim" in html and "Total:" in html


def test_cli_demo_grava_arquivo(tmp_path):
    saida = tmp_path / "site" / "index.html"
    assert main(["demo", "--saida", str(saida)]) == 0
    assert "simulador-de-cliente: demo" in saida.read_text(encoding="utf-8")
