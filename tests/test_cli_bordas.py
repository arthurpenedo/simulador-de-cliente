import json

from simulador_de_cliente.cli import main


def test_benchmark_zero_devolve_2(capsys):
    assert main(["benchmark", "--simulacoes", "0"]) == 2
    assert main(["benchmark", "--dialogos", "0"]) == 2
    assert "1 ou mais" in capsys.readouterr().err


def test_benchmark_saida_cria_a_pasta(tmp_path):
    saida = tmp_path / "novo" / "bench.txt"
    assert main(["benchmark", "--simulacoes", "2", "--dialogos", "5", "--saida", str(saida)]) == 0
    assert saida.read_text(encoding="utf-8").strip()


def test_treinar_salvar_cria_a_pasta(tmp_path):
    saida = tmp_path / "conversas" / "c.json"
    assert main(["treinar", "irritado", "--auto", "bom", "--salvar", str(saida)]) == 0
    assert isinstance(json.loads(saida.read_text(encoding="utf-8")), list)


def test_treinar_max_turnos_zero_devolve_2(capsys):
    assert main(["treinar", "irritado", "--auto", "bom", "--max-turnos", "0"]) == 2
    assert "1 ou mais" in capsys.readouterr().err


def test_avaliar_ignora_fala_com_texto_que_nao_e_string(tmp_path, capsys):
    arq = tmp_path / "conversa.json"
    arq.write_text(json.dumps([
        {"autor": "atendente", "texto": None},
        {"autor": "atendente", "texto": 123},
        {"autor": "atendente", "texto": "Sinto muito pelo transtorno, vou resolver agora."},
    ]), encoding="utf-8")
    assert main(["avaliar", str(arq)]) == 0
    assert "empatia" in capsys.readouterr().out
