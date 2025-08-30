"""
Utilities for data validation
"""
import re
from typing import List, Optional


def validate_email_format(email: str) -> bool:
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email.strip()) is not None


def validate_phone_format(phone: str) -> bool:
    """Validate Brazilian phone number format"""
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove non-numeric characters
    numbers_only = re.sub(r'\D', '', phone)
    
    # Brazilian phone: 10 digits (landline) or 11 digits (mobile)
    if len(numbers_only) not in [10, 11]:
        return False
    
    # Validate DDD (area code)
    valid_ddds = [
        11, 12, 13, 14, 15, 16, 17, 18, 19,  # SP
        21, 22, 24,  # RJ
        27, 28,  # ES
        31, 32, 33, 34, 35, 37, 38,  # MG
        41, 42, 43, 44, 45, 46,  # PR
        47, 48, 49,  # SC
        51, 53, 54, 55,  # RS
        61,  # DF
        62, 64,  # GO
        63,  # TO
        65, 66,  # MT
        67,  # MS
        68,  # AC
        69,  # RO
        71, 73, 74, 75, 77,  # BA
        79,  # SE
        81, 87,  # PE
        82,  # AL
        83,  # PB
        84,  # RN
        85, 88,  # CE
        86, 89,  # PI
        91, 93, 94,  # PA
        92, 97,  # AM
        95,  # RR
        96,  # AP
        98, 99,  # MA
    ]
    
    ddd = int(numbers_only[:2])
    if ddd not in valid_ddds:
        return False
    
    # Mobile phone validation (must start with 9)
    if len(numbers_only) == 11:
        if numbers_only[2] != '9':
            return False
    
    return True


def validate_cep_format(cep: str) -> bool:
    """Validate Brazilian postal code (CEP) format"""
    if not cep or not isinstance(cep, str):
        return False
    
    numbers_only = re.sub(r'\D', '', cep)
    return len(numbers_only) == 8 and numbers_only.isdigit()


def validate_address_completeness(address_data: dict) -> tuple[bool, Optional[str]]:
    """Validate that address has required fields"""
    required_fields = ['street', 'neighborhood', 'city', 'state']
    
    for field in required_fields:
        value = address_data.get(field, '').strip() if address_data.get(field) else ''
        if not value:
            return False, f"Campo '{field}' é obrigatório no endereço"
    
    # Validate CEP if provided
    zip_code = address_data.get('zip_code', '').strip()
    if zip_code and not validate_cep_format(zip_code):
        return False, "CEP inválido"
    
    # Validate state (should be 2 letters)
    state = address_data.get('state', '').strip()
    if len(state) != 2:
        return False, "Estado deve ter 2 caracteres (ex: SP)"
    
    return True, None


def validate_contacts_quality(phones: List[dict], emails: List[dict], addresses: List[dict]) -> tuple[bool, Optional[str]]:
    """Validate that all contact data has good quality"""
    
    # Validate phones
    valid_phones = 0
    for phone in phones:
        number = phone.get('number', '').strip()
        if not number:
            continue
        
        if not validate_phone_format(number):
            return False, f"Telefone inválido: {number}"
        
        valid_phones += 1
    
    if valid_phones == 0:
        return False, "Pelo menos um telefone válido é obrigatório"
    
    # Validate emails
    valid_emails = 0
    for email in emails:
        address = email.get('email_address', '').strip()
        if not address:
            continue
        
        if not validate_email_format(address):
            return False, f"E-mail inválido: {address}"
        
        valid_emails += 1
    
    if valid_emails == 0:
        return False, "Pelo menos um e-mail válido é obrigatório"
    
    # Validate addresses
    valid_addresses = 0
    for address in addresses:
        is_valid, error_msg = validate_address_completeness(address)
        if not is_valid:
            return False, error_msg
        
        valid_addresses += 1
    
    if valid_addresses == 0:
        return False, "Pelo menos um endereço completo é obrigatório"
    
    return True, None