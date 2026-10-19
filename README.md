# simulador-de-cliente

[![CI](https://github.com/arthurpenedo/simulador-de-cliente/actions/workflows/ci.yml/badge.svg)](https://github.com/arthurpenedo/simulador-de-cliente/actions/workflows/ci.yml)

Treinar atendente para cliente difícil (irritado, golpista, pedido fora da política) normalmente depende de role-play com outra pessoa. Este projeto coloca uma **persona de cliente** na conversa e avalia o atendente com uma **rubrica explicável** (empatia, política, segurança), mostrando a evidência de cada nota e onde melhorar.

Tudo gratuito e local: zero dependências, sem API paga. O cliente pode ser um roteiro determinístico (testes/CI) ou um modelo aberto via [Ollama](https://ollama.com). A empresa e as regras são fictícias (Banco Exemplo).

## Como funciona

- **4 personas** (`simulador-de-cliente personas`): cliente irritado com cobrança indevida, idoso confuso com o app, golpista que se diz marido da titular, e cliente com pedido fora do prazo de contestação.
- **Humor do cliente (0 a 10):** a cada fala do atendente a rubrica dá uma nota de 0 a 6 e o humor sobe ou desce. Humor ≥ 9 = cliente escala (desfecho ruim); humor ≤ 2 = cliente acalmado (desfecho bom). Com o golpista, pedir senha/token ou passar dado de terceiro encerra na hora com vazamento.
- **Rubrica** (`rubrica.py`): regras explícitas sobre o texto normalizado. Empatia (hostilidade zera, reconhecer o sentimento = 2, só cortesia = 1), política (promessa fora da regra zera, citar protocolo/prazo = 2) e segurança (pedir senha/token/CVV zera, mas "nunca peço sua senha" não conta; validar identidade/canal oficial = 2).
- **Consistência do cliente** (`no_papel`): detecta fala vazia, quebra de personagem ("como assistente...") e fala fora do perfil, útil para checar a saída de um modelo.

## Uso

```bash
pip install -e ".[dev]"
simulador-de-cliente treinar irritado                    # você é o atendente, no terminal
simulador-de-cliente treinar golpista --auto ruim        # atendente sintético
simulador-de-cliente treinar irritado --motor ollama --modelo qwen2.5:7b --salvar conversa.json
simulador-de-cliente avaliar conversa.json               # nota de uma conversa salva
simulador-de-cliente benchmark --saida BENCHMARK.md
pytest -q
```

## Números medidos (`BENCHMARK.md`, semente 42)

| | Resultado |
|---|---|
| Acerto da rubrica por dimensão (300 diálogos sintéticos com níveis conhecidos) | empatia 95,3%, política 92,7%, segurança 98,0% (média 95,3%) |
| Baseline "sempre nota 1" | 31,1% |
| Casos escritos à mão (negações, tom hostil, paráfrases) | 9/10 |
| Simulação, atendente "bom" | desfecho bom em 100% das 200 simulações (50 por persona) |
| Simulação, atendente "regular" ou "ruim" | desfecho bom em 0% das 400 simulações |

## Limites honestos

- Os diálogos sintéticos e o cliente por roteiro foram escritos pelo mesmo autor da rubrica: o benchmark mede a **mecânica** (rubrica, humor, desfecho), não o desempenho com atendentes reais nem com um modelo. Por isso os 100%/0% das simulações são esperados.
- Parte do erro da rubrica é proposital: o gerador inclui paráfrases que as regras não cobrem ("Fico no seu lugar e sei o quanto isso chateia"). No teste à mão, "Que chato isso ter acontecido contigo" recebe empatia 0 em vez de 2. Regra por palavra-chave não entende sinônimo.
- Não há avaliação com atendentes humanos nem comparação com um avaliador feito por LLM; o motor Ollama está implementado e testado com requisição simulada, mas não foi medido com um modelo real.
- Política fictícia (prazo de 30 dias etc.): troque pelas regras da sua operação em `personas.py` e `rubrica.py`.

## Licença

MIT
