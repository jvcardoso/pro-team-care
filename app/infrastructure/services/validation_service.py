"""
Validation Service - Integração com Functions PostgreSQL de Validação
"""

from typing import Optional, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

logger = structlog.get_logger()


class ValidationService:
    """
    Serviço de validação que integra com functions PostgreSQL
    Implementa validações de documentos, telefones, coordenadas, etc.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_cpf(self, cpf: str) -> bool:
        """
        Valida CPF usando algorithm do banco
        Function: fn_validate_cpf
        """
        if not cpf:
            return False
            
        try:
            query = text("SELECT master.fn_validate_cpf(:cpf)")
            result = await self.session.execute(query, {"cpf": cpf})
            is_valid = result.scalar() or False
            
            logger.debug("cpf_validation", cpf=cpf[:3] + "***", is_valid=is_valid)
            return is_valid
            
        except Exception as e:
            logger.error("cpf_validation_failed", cpf=cpf[:3] + "***", error=str(e))
            return False

    async def validate_cnpj(self, cnpj: str) -> bool:
        """
        Valida CNPJ usando algorithm do banco
        Function: fn_validate_cnpj
        """
        if not cnpj:
            return False
            
        try:
            query = text("SELECT master.fn_validate_cnpj(:cnpj)")
            result = await self.session.execute(query, {"cnpj": cnpj})
            is_valid = result.scalar() or False
            
            logger.debug("cnpj_validation", cnpj=cnpj[:2] + "***", is_valid=is_valid)
            return is_valid
            
        except Exception as e:
            logger.error("cnpj_validation_failed", cnpj=cnpj[:2] + "***", error=str(e))
            return False

    async def validate_phone_format(self, phone: str) -> Tuple[bool, Optional[str]]:
        """
        Valida e formata número de telefone
        Function: fn_validate_phone_format
        Returns: (is_valid, formatted_phone)
        """
        if not phone:
            return False, None
            
        try:
            query = text("SELECT master.fn_validate_phone_format(:phone)")
            result = await self.session.execute(query, {"phone": phone})
            formatted = result.scalar()
            
            is_valid = formatted is not None and formatted != phone
            
            logger.debug(
                "phone_validation", 
                original=phone[-4:], 
                formatted=formatted[-4:] if formatted else None,
                is_valid=is_valid
            )
            
            return is_valid, formatted
            
        except Exception as e:
            logger.error("phone_validation_failed", phone=phone[-4:], error=str(e))
            return False, None

    async def format_whatsapp_number(
        self, 
        phone: str, 
        country_code: str = "55"
    ) -> Optional[str]:
        """
        Formata número WhatsApp
        Function: fn_format_whatsapp_number
        """
        if not phone:
            return None
            
        try:
            query = text("""
                SELECT master.fn_format_whatsapp_number(:phone, :country_code)
            """)
            result = await self.session.execute(query, {
                "phone": phone, 
                "country_code": country_code
            })
            
            formatted = result.scalar()
            
            logger.debug(
                "whatsapp_format", 
                original=phone[-4:],
                formatted=formatted[-4:] if formatted else None
            )
            
            return formatted
            
        except Exception as e:
            logger.error("whatsapp_format_failed", phone=phone[-4:], error=str(e))
            return phone  # Return original on error

    async def validate_coordinates(
        self, 
        latitude: float, 
        longitude: float
    ) -> bool:
        """
        Valida coordenadas geográficas (Brasil)
        Function: fn_validate_coordinates
        """
        try:
            query = text("""
                SELECT master.fn_validate_coordinates(:lat, :lng)
            """)
            result = await self.session.execute(query, {
                "lat": latitude,
                "lng": longitude
            })
            
            is_valid = result.scalar() or False
            
            logger.debug(
                "coordinates_validation",
                lat=latitude,
                lng=longitude,
                is_valid=is_valid
            )
            
            return is_valid
            
        except Exception as e:
            logger.error(
                "coordinates_validation_failed",
                lat=latitude,
                lng=longitude, 
                error=str(e)
            )
            return False

    async def calculate_address_quality_score(
        self,
        street: str,
        number: Optional[str],
        neighborhood: str,
        city: str,
        state: str,
        zip_code: str
    ) -> int:
        """
        Calcula score de qualidade do endereço
        Function: fn_calculate_address_quality_score
        """
        try:
            query = text("""
                SELECT master.fn_calculate_address_quality_score(
                    :street, :number, :neighborhood, :city, :state, :zip_code
                )
            """)
            result = await self.session.execute(query, {
                "street": street,
                "number": number,
                "neighborhood": neighborhood,
                "city": city,
                "state": state,
                "zip_code": zip_code
            })
            
            score = result.scalar() or 0
            
            logger.debug(
                "address_quality_score",
                city=city,
                state=state,
                score=score
            )
            
            return score
            
        except Exception as e:
            logger.error(
                "address_quality_score_failed",
                city=city,
                state=state,
                error=str(e)
            )
            return 0

    async def validate_tax_id(self, tax_id: str, person_type: str) -> bool:
        """
        Valida documento fiscal baseado no tipo de pessoa
        """
        if person_type == 'PF':
            return await self.validate_cpf(tax_id)
        elif person_type == 'PJ':
            return await self.validate_cnpj(tax_id)
        else:
            logger.warning("invalid_person_type", person_type=person_type)
            return False

    async def format_and_validate_phone(
        self, 
        phone: str, 
        is_whatsapp: bool = False,
        country_code: str = "55"
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida e formata telefone, com tratamento especial para WhatsApp
        """
        if is_whatsapp:
            formatted = await self.format_whatsapp_number(phone, country_code)
            return formatted is not None, formatted
        else:
            return await self.validate_phone_format(phone)


# Função de conveniência para dependency injection
async def get_validation_service(session: AsyncSession) -> ValidationService:
    """Factory function for ValidationService"""
    return ValidationService(session)