# Análise do Sistema - Erro de CORS no Login

**Data:** 2025-09-07 18:00
**Versão:** v001
**Autor:** Gemini

## Histórico de Versões
- v001 (2025-09-07): Versão inicial do documento com a análise do erro de CORS.

## Objetivo
Diagnosticar a causa raiz do erro de CORS (Cross-Origin Resource Sharing) que está impedindo a funcionalidade de login na aplicação e fornecer um roteiro técnico claro para a equipe de desenvolvimento investigar e resolver o problema.

## Metodologia
A análise foi conduzida utilizando os seguintes métodos, baseados nos logs de console do navegador e do servidor fornecidos:
- **Forensic Analysis:** Análise detalhada dos logs de erro do console do navegador (origem: `http://192.168.11.83:3000`) e dos logs de acesso do servidor FastAPI (destino: `http://192.168.11.83:8000`).
- **Differential Analysis:** Comparação entre o comportamento esperado de uma negociação CORS bem-sucedida (resposta `200 OK` para a requisição `OPTIONS`) e o comportamento observado (resposta `400 Bad Request`).
- **Systematic Investigation:** Rastreamento do fluxo da requisição, desde a tentativa de `POST` no frontend, passando pela requisição "preflight" `OPTIONS` do navegador, até a resposta de erro do backend.

## Resultados
A análise dos logs revelou os seguintes fatos:
1.  **Erro no Navegador:** O console do navegador exibe a mensagem: `Access to XMLHttpRequest at 'http://192.168.11.83:8000/api/v1/auth/login' from origin 'http://192.168.11.83:3000' has been blocked by CORS policy`.
2.  **Falha no Preflight:** A causa específica do bloqueio é: `Response to preflight request doesn't pass access control check: It does not have HTTP ok status.` Isso indica que a requisição `OPTIONS` (preflight) enviada pelo navegador antes do `POST` de login não foi bem-sucedida.
3.  **Resposta do Servidor:** Os logs do servidor FastAPI confirmam o problema, mostrando que ele recebe a requisição `OPTIONS` e responde com um erro: `INFO: 192.168.11.6:47896 - "OPTIONS /api/v1/... HTTP/1.1" 400 Bad Request`.

## Conclusões
1.  **Causa Raiz:** O problema não está no frontend, mas sim na **configuração do backend**. A aplicação FastAPI não está configurada para lidar corretamente com o protocolo CORS.
2.  **Mecanismo da Falha:** O backend está tratando a requisição `OPTIONS` (parte padrão do handshake CORS para requisições "complexas") como uma chamada de API inválida, resultando em um `400 Bad Request`. O correto seria responder com `200 OK` e os cabeçalhos `Access-Control-*` apropriados.
3.  **Impacto:** Esta falha de configuração bloqueia completamente a comunicação entre o frontend e o backend para o endpoint de login e, muito provavelmente, para todos os outros endpoints que necessitam de um preflight CORS.

## Próximos passos
Recomenda-se que a equipe de desenvolvimento execute os seguintes passos no **código do backend**:

1.  **Localizar o Ponto de Configuração:** Identificar o arquivo principal da aplicação onde a instância do FastAPI é criada (geralmente `app/main.py`).
2.  **Verificar a Existência do Middleware CORS:** Procurar no arquivo por `CORSMiddleware` e `app.add_middleware`.
3.  **Implementar ou Corrigir a Configuração:**
    *   **Se o middleware não existir**, ele deve ser adicionado.
    *   **Se já existir**, a sua configuração deve ser validada.

    **Exemplo de configuração correta:**
    '''python
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI()

    # Lista de origens permitidas. Para desenvolvimento, pode-se usar ["*"].
    # Para produção, deve ser restrito ao domínio do frontend.
    origins = [
        "http://192.168.11.83:3000",
        "http://localhost:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"], # Permitir todos os métodos (GET, POST, OPTIONS, etc.)
        allow_headers=["*"], # Permitir todos os cabeçalhos
    )

    # ... resto do código da aplicação
    '''
A aplicação desta configuração permitirá que o backend responda corretamente às requisições `OPTIONS` do navegador, desbloqueando a comunicação e permitindo que a funcionalidade de login seja concluída.
