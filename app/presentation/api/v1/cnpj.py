"""
Endpoints para consulta de CNPJ
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import httpx
import logging

from ....infrastructure.auth import get_current_user

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


@router.get("/consultar/{cnpj}")
async def consultar_cnpj(
    cnpj: str,
    current_user: dict = Depends(get_current_user)
) -> CNPJConsultaResponse:
    """
    Consulta dados de empresa pelo CNPJ usando ReceitaWS
    
    Args:
        cnpj: CNPJ da empresa (apenas números)
        current_user: Usuário autenticado
    
    Returns:
        CNPJConsultaResponse: Dados da empresa ou erro
    """
    try:
        # Limpar CNPJ (apenas números)
        cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
        
        if len(cnpj_limpo) != 14:
            raise HTTPException(
                status_code=400,
                detail="CNPJ deve conter exatamente 14 dígitos"
            )
        
        logger.info(f"Consultando CNPJ: {cnpj_limpo}")
        
        # Fazer requisição para ReceitaWS
        url = f"https://receitaws.com.br/v1/cnpj/{cnpj_limpo}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            if response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Muitas consultas realizadas. Tente novamente em alguns minutos."
                )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erro na consulta externa: {response.status_code}"
                )
            
            dados_receita = response.json()
            
            # Verificar se houve erro na API
            if dados_receita.get("status") == "ERROR":
                raise HTTPException(
                    status_code=404,
                    detail=dados_receita.get("message", "CNPJ não encontrado")
                )
            
            # Mapear dados para nosso formato
            dados_mapeados = mapear_dados_receita(dados_receita)
            
            logger.info(f"CNPJ {cnpj_limpo} consultado com sucesso")
            
            return CNPJConsultaResponse(
                success=True,
                data=dados_mapeados,
                message="Dados da empresa encontrados com sucesso"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except httpx.TimeoutException:
        logger.error(f"Timeout ao consultar CNPJ {cnpj_limpo}")
        raise HTTPException(
            status_code=408,
            detail="Tempo limite da consulta excedido. Tente novamente."
        )
    except Exception as e:
        logger.error(f"Erro ao consultar CNPJ {cnpj_limpo}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao consultar CNPJ"
        )


def mapear_dados_receita(dados: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapeia dados da ReceitaWS para estrutura do nosso sistema
    
    Args:
        dados: Dados retornados pela ReceitaWS
        
    Returns:
        Dict: Dados mapeados para nosso sistema
    """
    
    def mapear_status(situacao: str) -> str:
        """Mapeia situação da RF para status do sistema"""
        if not situacao:
            return 'active'
        
        situacao_lower = situacao.lower()
        if 'ativa' in situacao_lower:
            return 'active'
        elif 'suspensa' in situacao_lower:
            return 'suspended'
        elif 'baixada' in situacao_lower or 'cancelada' in situacao_lower:
            return 'inactive'
        
        return 'active'
    
    def formatar_data(data_str: str) -> str:
        """Converte DD/MM/AAAA para AAAA-MM-DD"""
        if not data_str:
            return None
            
        partes = data_str.split('/')
        if len(partes) == 3:
            dia, mes, ano = partes
            return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
        
        return None
    
    # Mapear dados principais
    dados_mapeados = {
        # Dados da pessoa jurídica
        "people": {
            "person_type": "PJ",
            "name": dados.get("nome", ""),
            "trade_name": dados.get("fantasia", ""),
            "tax_id": dados.get("cnpj", "").replace("/", "").replace(".", "").replace("-", ""),
            "incorporation_date": formatar_data(dados.get("abertura")),
            "status": mapear_status(dados.get("situacao")),
            "legal_nature": dados.get("natureza_juridica", ""),
            "secondary_tax_id": "",  # IE - não disponível na ReceitaWS
            "municipal_registration": "",  # Inscrição Municipal - não disponível na ReceitaWS  
            "website": "",  # Site - não disponível na ReceitaWS
            "description": f"Empresa do ramo de {dados.get('atividade_principal', {}).get('text', 'atividade não especificada')}" if dados.get('atividade_principal') else "",
            "tax_regime": "simples_nacional",  # Default - não disponível na ReceitaWS
            "metadata": {
                # CNAE Principal
                "cnae_fiscal": dados.get("atividade_principal", {}).get("code") if dados.get("atividade_principal") else None,
                "cnae_fiscal_descricao": dados.get("atividade_principal", {}).get("text") if dados.get("atividade_principal") else None,
                
                # CNAEs Secundários
                "cnaes_secundarios": dados.get("atividades_secundarias", []),
                
                # Dados Societários
                "porte": dados.get("porte", ""),
                "capital_social": dados.get("capital_social", ""),
                "natureza_juridica": dados.get("natureza_juridica", ""),
                
                # Situação
                "situacao": dados.get("situacao", ""),
                "motivo_situacao": dados.get("motivo_situacao", ""),
                "data_situacao": dados.get("data_situacao", ""),
                "situacao_especial": dados.get("situacao_especial", ""),
                "data_situacao_especial": dados.get("data_situacao_especial", ""),
                
                # Classificação
                "tipo": dados.get("tipo", ""),  # MATRIZ/FILIAL
                "efr": dados.get("efr", ""),  # Enquadramento no Regime Especial
                
                # Localização
                "municipio": dados.get("municipio", ""),
                "uf": dados.get("uf", ""),
                
                # Dados da consulta
                "ultima_atualizacao_rf": dados.get("ultima_atualizacao", ""),
                "receita_ws_data": dados,  # Dados completos da ReceitaWS para referência
                "consulta_data": None  # Será preenchido pelo frontend
            }
        },
        
        # Telefone se disponível
        "phones": [],
        "emails": [],
        "addresses": []
    }
    
    # Adicionar telefone se disponível
    if dados.get("telefone"):
        telefone_limpo = ''.join(filter(str.isdigit, dados["telefone"]))
        if len(telefone_limpo) >= 10:
            dados_mapeados["phones"].append({
                "country_code": "55",
                "number": telefone_limpo,
                "type": "commercial",
                "is_principal": True,
                "is_whatsapp": False
            })
    
    # Adicionar email se disponível
    if dados.get("email"):
        dados_mapeados["emails"].append({
            "email_address": dados["email"],
            "type": "work",
            "is_principal": True
        })
    
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
        "is_principal": True
    }
    
    # Só adicionar endereço se tiver dados mínimos
    if endereco["street"] or endereco["city"]:
        dados_mapeados["addresses"].append(endereco)
    
    return dados_mapeados