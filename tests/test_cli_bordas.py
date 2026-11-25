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


def test_saida_apontando_para_pasta_devolve_2(tmp_path, capsys):
    assert main(["demo", "--saida", str(tmp_path)]) == 2
    assert main(["benchmark", "--simulacoes", "1", "--dialogos", "1", "--saida", str(tmp_path)]) == 2
    assert main(["treinar", "irritado", "--auto", "bom", "--salvar", str(tmp_path)]) == 2
    assert "pasta" in capsys.readouterr().err


def test_saida_dentro_de_arquivo_devolve_2_sem_traceback(tmp_path, capsys):
    arq = tmp_path / "arq.txt"
    arq.write_text("x", encoding="utf-8")
    assert main(["demo", "--saida", str(arq / "x.html")]) == 2
    assert main(["benchmark", "--simulacoes", "1", "--dialogos", "1", "--saida", str(arq / "x.md")]) == 2
    assert main(["treinar", "irritado", "--auto", "bom", "--salvar", str(arq / "c.json")]) == 2
    assert "passa por um arquivo" in capsys.readouterr().err


def test_avaliar_ignora_fala_com_texto_que_nao_e_string(tmp_path, capsys):
    arq = tmp_path / "conversa.json"
    arq.write_text(json.dumps([
        {"autor": "atendente", "texto": None},
        {"autor": "atendente", "texto": 123},
        {"autor": "atendente", "texto": "Sinto muito pelo transtorno, vou resolver agora."},
    ]), encoding="utf-8")
    assert main(["avaliar", str(arq)]) == 0
    assert "empatia" in capsys.readouterr().out
