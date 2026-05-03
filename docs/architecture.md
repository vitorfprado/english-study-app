# Arquitetura (MVP local)

Fluxo atual:

```text
Navegador → FastAPI (porta 8000) → Jinja2 + HTMX → Serviços → PostgreSQL (container `db`)
```

Integração com IA é opcional: sem `AI_API_KEY`, o serviço de IA usa um gerador local baseado no texto do material.
