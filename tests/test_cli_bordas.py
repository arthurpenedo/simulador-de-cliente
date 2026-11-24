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
