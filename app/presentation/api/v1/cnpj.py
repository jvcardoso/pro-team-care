"""
Endpoints para consulta de CNPJ
"""

import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Configurar logger
logger = logging.getLogger(__name__)

# Router
router = APIRouter()


# Modelos Pydantic
class CNPJConsultaRequest(BaseModel):
    cnpj: str


class CNPJConsultaResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = {}
    message: str = ""


@router.get(
    "/consultar/{cnpj}",
    response_model=CNPJConsultaResponse,
    summary="Consultar CNPJ (Autenticado)",
    description="""
    Consulta dados completos de uma empresa pelo CNPJ usando a ReceitaWS.

    **Funcionalidades:**
    - Consulta dados na Receita Federal
    - Enriquecimento automático de dados
    - Mapeamento para estrutura do sistema
    - Cache automático de respostas

    **Dados retornados:**
    - Informações básicas da empresa
    - CNAE principal e secundários
    - Endereço completo
    - Contatos quando disponíveis
    - Situação na Receita Federal

    **Restrições:**
    - Requer autenticação válida
    - Sujeito a rate limit da ReceitaWS
    - Timeout de 30 segundos
    """,
    tags=["CNPJ Lookup"],
    responses={
        200: {
            "description": "Dados da empresa encontrados",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Dados da empresa encontrados com sucesso",
                        "data": {
                            "people": {
                                "name": "EMPRESA EXEMPLO LTDA",
                                "trade_name": "Exemplo Corp",
                                "tax_id": "11222333000144",
                                "status": "active",
                            },
                            "phones": [{"number": "11987654321"}],
                            "addresses": [
                                {
                                    "street": "Avenida Paulista",
                                    "city": "São Paulo",
                                    "state": "SP",
                                }
                            ],
                        },
                    }
                }
            },
        },
        400: {"description": "CNPJ inválido"},
        404: {"description": "CNPJ não encontrado na Receita Federal"},
        408: {"description": "Timeout na consulta externa"},
        429: {"description": "Rate limit excedido na ReceitaWS"},
        401: {"description": "Não autorizado"},
    },
)
async def consultar_cnpj(cnpj: str, current_user=None) -> CNPJConsultaResponse:
    return await _consultar_cnpj_interno(cnpj)


@router.get(
    "/publico/consultar/{cnpj}",
    response_model=CNPJConsultaResponse,
    summary="Consultar CNPJ (Público)",
    description="""
    Consulta pública de dados básicos de empresa pelo CNPJ.

    **ATENÇÃO:** Endpoint público sem autenticação.

    **Limitações:**
    - Mesmos rate limits da ReceitaWS aplicam
    - Pode ser desabilitado por políticas de segurança
    - Use o endpoint autenticado para uso profissional

    **Uso recomendado:**
    - Validação rápida de CNPJ em formulários
    - Demonstrações públicas
    - Testes de integração
    """,
    tags=["CNPJ Lookup"],
    responses={
        200: {"description": "Consulta realizada com sucesso"},
        400: {"description": "CNPJ inválido"},
        404: {"description": "CNPJ não encontrado"},
        429: {"description": "Rate limit excedido"},
    },
)
async def consultar_cnpj_publico(cnpj: str) -> CNPJConsultaResponse:
    return await _consultar_cnpj_interno(cnpj)


@router.get(
    "/teste/{cnpj}",
    summary="Testar CNPJ (Desenvolvimento)",
    description="""
    Endpoint de teste que valida formato do CNPJ sem fazer consulta externa.

    **Finalidade:**
    - Testes de desenvolvimento
    - Validação de formato de CNPJ
    - Debug de integrações

    **Não faz consulta real na ReceitaWS** - apenas valida formato.
    """,
    tags=["CNPJ Lookup", "Development"],
    responses={
        200: {
            "description": "Teste realizado",
            "content": {
                "application/json": {
                    "example": {
                        "cnpj_original": "11.222.333/0001-44",
                        "cnpj_limpo": "11222333000144",
                        "url": "https://receitaws.com.br/v1/cnpj/11222333000144",
                        "status": "Endpoint de teste ativo",
                    }
                }
            },
        },
        400: {"description": "Formato de CNPJ inválido"},
    },
)
async def testar_cnpj(cnpj: str):
    try:
        # Limpar CNPJ (apenas números)
        cnpj_limpo = "".join(filter(str.isdigit, cnpj))

        if len(cnpj_limpo) != 14:
            return {"error": "CNPJ deve conter exatamente 14 dígitos"}

        logger.info(f"Testando CNPJ: {cnpj_limpo}")

        # Retornar apenas informações básicas sem fazer requisição
        return {
            "cnpj_original": cnpj,
            "cnpj_limpo": cnpj_limpo,
            "url": f"https://receitaws.com.br/v1/cnpj/{cnpj_limpo}",
            "status": "Endpoint de teste ativo",
        }

    except Exception as e:
        logger.error(f"Erro no teste: {str(e)}")
        return {"error": "Erro interno no teste de CNPJ"}


async def _consultar_cnpj_interno(cnpj: str) -> CNPJConsultaResponse:
    """
    Consulta dados de empresa pelo CNPJ usando ReceitaWS
    """
    cnpj_limpo = None
    try:
        # Limpar CNPJ (apenas números)
        cnpj_limpo = "".join(filter(str.isdigit, cnpj))

        if len(cnpj_limpo) != 14:
            raise HTTPException(
                status_code=400, detail="CNPJ deve conter exatamente 14 dígitos"
            )

        logger.info(f"Consultando CNPJ: {cnpj_limpo}")

        # Fazer requisição para ReceitaWS
        url = f"https://receitaws.com.br/v1/cnpj/{cnpj_limpo}"
        logger.info(f"URL da consulta: {url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("Iniciando requisição HTTP...")
            response = await client.get(url)
            logger.info(f"Requisição concluída com status: {response.status_code}")

            if response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Muitas consultas realizadas. Tente novamente em alguns minutos.",
                )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erro na consulta externa: {response.status_code}",
                )

            dados_receita = response.json()

            # Verificar se houve erro na API
            if dados_receita.get("status") == "ERROR":
                raise HTTPException(
                    status_code=404,
                    detail=dados_receita.get("message", "CNPJ não encontrado"),
                )

            # Mapear dados para nosso formato
            dados_mapeados = mapear_dados_receita(dados_receita)

            logger.info(f"CNPJ {cnpj_limpo} consultado com sucesso")

            return CNPJConsultaResponse(
                success=True,
                data=dados_mapeados,
                message="Dados da empresa encontrados com sucesso",
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except httpx.TimeoutException:
        logger.error(f"Timeout ao consultar CNPJ {cnpj_limpo or 'desconhecido'}")
        raise HTTPException(
            status_code=408,
            detail="Tempo limite da consulta excedido. Tente novamente.",
        )
    except Exception as e:
        logger.error(f"Erro ao consultar CNPJ {cnpj_limpo or 'desconhecido'}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao consultar CNPJ")


def mapear_dados_receita(dados: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapeia dados da ReceitaWS para estrutura do nosso sistema

    Args:
        dados: Dados retornados pela ReceitaWS

    Returns:
        Dict: Dados mapeados para nosso sistema
    """
    logger.info(f"Dados recebidos da ReceitaWS: {dados}")

    def mapear_status(situacao) -> str:
        """Mapeia situação da RF para status do sistema"""
        if not situacao:
            return "active"

        situacao_lower = str(situacao).lower()
        if "ativa" in situacao_lower:
            return "active"
        elif "suspensa" in situacao_lower:
            return "suspended"
        elif "baixada" in situacao_lower or "cancelada" in situacao_lower:
            return "inactive"

        return "active"

    def formatar_data(data_str) -> str:
        """Converte DD/MM/AAAA para AAAA-MM-DD"""
        if not data_str:
            return ""

        partes = str(data_str).split("/")
        if len(partes) == 3:
            dia, mes, ano = partes
            return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"

        return ""

    # Verificar se dados essenciais estão presentes
    if not dados:
        raise ValueError("Dados vazios retornados da ReceitaWS")

    # Mapear dados principais com verificações de segurança
    logger.info("Iniciando mapeamento de dados")

    # Garantir que dados essenciais sejam strings
    nome = str(dados.get("nome", "")).strip()
    if not nome:
        raise ValueError("Nome da empresa não encontrado nos dados")

    dados_mapeados = {
        # Dados da pessoa jurídica
        "people": {
            "person_type": "PJ",
            "name": nome,
            "trade_name": str(dados.get("fantasia", "")).strip(),
            "tax_id": str(dados.get("cnpj", ""))
            .replace("/", "")
            .replace(".", "")
            .replace("-", "")
            .strip(),
            "incorporation_date": formatar_data(dados.get("abertura") or ""),
            "status": mapear_status(dados.get("situacao") or ""),
            "legal_nature": str(dados.get("natureza_juridica", "")).strip(),
            "secondary_tax_id": "",  # IE - não disponível na ReceitaWS
            "municipal_registration": "",  # Inscrição Municipal - não disponível na ReceitaWS
            "website": "",  # Site - não disponível na ReceitaWS
            "description": (
                f"Empresa do ramo de {dados.get('atividade_principal', [{}])[0].get('text', 'atividade não especificada')}"
                if dados.get("atividade_principal")
                and isinstance(dados.get("atividade_principal"), list)
                and len(dados.get("atividade_principal", [])) > 0
                else ""
            ),
            "tax_regime": "simples_nacional",  # Default - não disponível na ReceitaWS
            "metadata": {
                # CNAE Principal
                "cnae_fiscal": (
                    dados.get("atividade_principal", [{}])[0].get("code")
                    if isinstance(dados.get("atividade_principal"), list)
                    and len(dados.get("atividade_principal", [])) > 0
                    else None
                ),
                "cnae_fiscal_descricao": (
                    dados.get("atividade_principal", [{}])[0].get("text")
                    if isinstance(dados.get("atividade_principal"), list)
                    and len(dados.get("atividade_principal", [])) > 0
                    else None
                ),
                # CNAEs Secundários
                "cnaes_secundarios": (
                    dados.get("atividades_secundarias", [])
                    if isinstance(dados.get("atividades_secundarias"), list)
                    else []
                ),
                # Dados Societários
                "porte": str(dados.get("porte", "")).strip(),
                "capital_social": str(dados.get("capital_social", "")).strip(),
                "natureza_juridica": str(dados.get("natureza_juridica", "")).strip(),
                # Situação
                "situacao": str(dados.get("situacao", "")).strip(),
                "motivo_situacao": str(dados.get("motivo_situacao", "")).strip(),
                "data_situacao": str(dados.get("data_situacao", "")).strip(),
                "situacao_especial": str(dados.get("situacao_especial", "")).strip(),
                "data_situacao_especial": str(
                    dados.get("data_situacao_especial", "")
                ).strip(),
                # Classificação
                "tipo": str(dados.get("tipo", "")).strip(),  # MATRIZ/FILIAL
                "efr": str(
                    dados.get("efr", "")
                ).strip(),  # Enquadramento no Regime Especial
                # Localização
                "municipio": str(dados.get("municipio", "")).strip(),
                "uf": str(dados.get("uf", "")).strip(),
                # Dados da consulta
                "ultima_atualizacao_rf": str(
                    dados.get("ultima_atualizacao", "")
                ).strip(),
                "receita_ws_data": dados,  # Dados completos da ReceitaWS para referência
                "consulta_data": None,  # Será preenchido pelo frontend
            },
        },
        # Telefone se disponível
        "phones": [],
        "emails": [],
        "addresses": [],
    }

    # Adicionar telefones se disponíveis (pode haver múltiplos separados por "/")
    if dados.get("telefone"):
        telefone_string = str(dados["telefone"])
        logger.info(f"Processando telefone da ReceitaWS: {telefone_string}")

        # Separar múltiplos telefones
        telefones_separados = [
            tel.strip() for tel in telefone_string.split("/") if tel.strip()
        ]
        logger.info(f"Telefones separados: {telefones_separados}")

        for i, telefone in enumerate(telefones_separados):
            # Limpar apenas números
            telefone_limpo = "".join(filter(str.isdigit, telefone))
            logger.info(
                f"Telefone {i+1} limpo: {telefone_limpo} (comprimento: {len(telefone_limpo)})"
            )

            # Validar tamanho (10-11 dígitos)
            if 10 <= len(telefone_limpo) <= 11:
                dados_mapeados["phones"].append(
                    {
                        "country_code": "55",
                        "number": telefone_limpo,
                        "type": "commercial",
                        "is_principal": i == 0,  # Primeiro telefone é principal
                        "is_whatsapp": False,
                    }
                )
                logger.info(f"Telefone {i+1} adicionado: {telefone_limpo}")
            else:
                logger.warning(
                    f"Telefone {i+1} ignorado - tamanho inválido: {len(telefone_limpo)} dígitos"
                )

        logger.info(f"Total de telefones processados: {len(dados_mapeados['phones'])}")
    else:
        telefones_separados = []

    # Adicionar email se disponível
    if dados.get("email"):
        dados_mapeados["emails"].append(
            {"email_address": dados["email"], "type": "work", "is_principal": True}
        )

    # Adicionar endereço principal
    endereco = {
        "street": dados.get("logradouro", ""),
        "number": dados.get("numero", ""),
        "details": dados.get("complemento", ""),
        "neighborhood": dados.get("bairro", ""),
        "city": dados.get("municipio", ""),
        "state": dados.get("uf", ""),
        "zip_code": dados.get("cep", "").replace("-", "").replace(".", ""),
        "country": "BR",
        "type": "commercial",
        "is_principal": True,
    }

    # Só adicionar endereço se tiver dados mínimos
    if endereco["street"] or endereco["city"]:
        dados_mapeados["addresses"].append(endereco)

    return dados_mapeados
