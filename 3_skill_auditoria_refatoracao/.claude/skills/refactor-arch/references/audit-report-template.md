# Template do relatório de auditoria

Use este formato em cada execução. Troque placeholders por evidência observada e remova campos realmente indisponíveis explicando o motivo.

```markdown
# Relatório de Auditoria — <projeto>

## Análise do projeto
- Linguagem/framework:
- Banco e dependências relevantes:
- Domínio:
- Arquitetura atual:
- Arquivos-fonte analisados / excluídos:
- Comandos de teste e boot disponíveis:

## Resumo
| Severidade | Quantidade |
|---|---:|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **Total** | **0** |

## Achados
### [<SEVERIDADE>] <nome curto>
- **Local:** `caminho/relativo:linha`
- **Evidência:** <trecho ou comportamento observado>
- **Descrição:** <o que acontece>
- **Impacto:** <consequência concreta>
- **Recomendação:** <correção proposta>

## APIs deprecated
<achados comprovados ou “Nenhuma identificada após checagem de ...”>

## Gate da Fase 2
A auditoria não alterou o código-alvo. Aprovar a Fase 3? (sim/não)
```

Ordene os blocos de achados em CRITICAL → HIGH → MEDIUM → LOW. Linhas são 1-based; confira no arquivo atual após qualquer alteração. Não inclua valores de credenciais nos achados: registre apenas que há segredo embutido e sua localização.
