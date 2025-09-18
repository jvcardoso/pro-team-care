"""
Testes abrangentes para validadores do sistema
Expande cobertura de testes conforme auditoria de qualidade
"""

from typing import Any, Dict, List

import pytest

from app.utils.validators import (
    validate_address_completeness,
    validate_cep_format,
    validate_contacts_quality,
    validate_email_format,
    validate_phone_format,
)


class TestCNPJValidator:
    """Testes completos para validação de CNPJ"""

    def test_validate_cnpj_valid_formats(self):
        """Test CNPJs válidos em diferentes formatos"""
        valid_cnpjs = [
            "11222333000144",  # Apenas números
            "11.222.333/0001-44",  # Formato completo
            "11222333/0001-44",  # Sem pontos
            "11.222.333000144",  # Sem barra e hífen
        ]

        for cnpj in valid_cnpjs:
            assert validate_cnpj(cnpj) == True, f"CNPJ {cnpj} deveria ser válido"

    def test_validate_cnpj_invalid_formats(self):
        """Test CNPJs inválidos"""
        invalid_cnpjs = [
            "",  # Vazio
            "1122233300014",  # Menos de 14 dígitos
            "112223330001455",  # Mais de 14 dígitos
            "11222333000100",  # Dígito verificador incorreto
            "00000000000000",  # Todos zeros
            "11111111111111",  # Todos iguais
            "abc.def.ghi/jklm-no",  # Caracteres não numéricos
            "11.222.333/0001-99",  # Dígito verificador incorreto
            None,  # None
        ]

        for cnpj in invalid_cnpjs:
            assert validate_cnpj(cnpj) == False, f"CNPJ {cnpj} deveria ser inválido"

    def test_validate_cnpj_edge_cases(self):
        """Test casos extremos de CNPJ"""
        edge_cases = [
            ("11222333000144", True),  # Válido
            ("  11222333000144  ", True),  # Com espaços
            ("11.222.333/0001-44", True),  # Formatado
            ("11-222-333-0001-44", False),  # Formato incorreto
        ]

        for cnpj, expected in edge_cases:
            result = validate_cnpj(cnpj)
            assert (
                result == expected
            ), f"CNPJ '{cnpj}' esperado {expected}, obtido {result}"


class TestCPFValidator:
    """Testes completos para validação de CPF"""

    def test_validate_cpf_valid_formats(self):
        """Test CPFs válidos em diferentes formatos"""
        valid_cpfs = [
            "11144477735",  # Apenas números
            "111.444.777-35",  # Formato completo
            "111444777-35",  # Sem pontos
            "111.44477735",  # Sem hífen
        ]

        for cpf in valid_cpfs:
            assert validate_cpf(cpf) == True, f"CPF {cpf} deveria ser válido"

    def test_validate_cpf_invalid_formats(self):
        """Test CPFs inválidos"""
        invalid_cpfs = [
            "",  # Vazio
            "1114447773",  # Menos de 11 dígitos
            "111444777355",  # Mais de 11 dígitos
            "11144477799",  # Dígito verificador incorreto
            "00000000000",  # Todos zeros
            "11111111111",  # Todos iguais
            "abc.def.ghi-jk",  # Caracteres não numéricos
            "111.444.777-99",  # Dígito verificador incorreto
            None,  # None
        ]

        for cpf in invalid_cpfs:
            assert validate_cpf(cpf) == False, f"CPF {cpf} deveria ser inválido"

    def test_validate_cpf_known_invalid_sequences(self):
        """Test sequências conhecidas como inválidas"""
        invalid_sequences = [
            "00000000000",
            "11111111111",
            "22222222222",
            "33333333333",
            "44444444444",
            "55555555555",
            "66666666666",
            "77777777777",
            "88888888888",
            "99999999999",
        ]

        for cpf in invalid_sequences:
            assert (
                validate_cpf(cpf) == False
            ), f"CPF {cpf} (sequência) deveria ser inválido"


class TestEmailValidator:
    """Testes completos para validação de email"""

    def test_validate_email_valid_formats(self):
        """Test emails válidos"""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@example123.com",
            "test@subdomain.example.com",
            "user@example.com.br",
            "user_name@example.org",
            "user-name@example.net",
        ]

        for email in valid_emails:
            assert validate_email(email) == True, f"Email {email} deveria ser válido"

    def test_validate_email_invalid_formats(self):
        """Test emails inválidos"""
        invalid_emails = [
            "",  # Vazio
            "@example.com",  # Sem usuário
            "user@",  # Sem domínio
            "user.example.com",  # Sem @
            "user@@example.com",  # Duplo @
            "user@.com",  # Domínio inválido
            "user@example.",  # TLD incompleto
            "user name@example.com",  # Espaço no usuário
            "user@exam ple.com",  # Espaço no domínio
            None,  # None
            "user@",  # Incompleto
        ]

        for email in invalid_emails:
            assert validate_email(email) == False, f"Email {email} deveria ser inválido"

    def test_validate_email_edge_cases(self):
        """Test casos extremos de email"""
        edge_cases = [
            ("  user@example.com  ", True),  # Com espaços
            ("USER@EXAMPLE.COM", True),  # Maiúsculas
            ("user@example.COM", True),  # TLD maiúsculo
            ("a@b.co", True),  # Mínimo válido
            (
                "very.long.email.address@very.long.domain.name.com",
                True,
            ),  # Longo mas válido
        ]

        for email, expected in edge_cases:
            result = validate_email(email)
            assert (
                result == expected
            ), f"Email '{email}' esperado {expected}, obtido {result}"


class TestPhoneValidator:
    """Testes completos para validação de telefone"""

    def test_validate_phone_valid_formats(self):
        """Test telefones válidos brasileiros"""
        valid_phones = [
            "11987654321",  # Celular SP com 9
            "1133334444",  # Fixo SP
            "21987654321",  # Celular RJ com 9
            "2133334444",  # Fixo RJ
            "85987654321",  # Celular CE com 9
            "8533334444",  # Fixo CE
            "11912345678",  # Celular SP formato novo
        ]

        for phone in valid_phones:
            assert validate_phone(phone) == True, f"Telefone {phone} deveria ser válido"

    def test_validate_phone_invalid_formats(self):
        """Test telefones inválidos"""
        invalid_phones = [
            "",  # Vazio
            "1198765432",  # Menos de 10 dígitos
            "119876543210",  # Mais de 11 dígitos
            "00987654321",  # DDD inválido
            "99987654321",  # DDD inválido
            "1187654321",  # Celular sem 9 (formato antigo não aceito)
            "abcdefghijk",  # Não numérico
            None,  # None
        ]

        for phone in invalid_phones:
            assert (
                validate_phone(phone) == False
            ), f"Telefone {phone} deveria ser inválido"

    def test_validate_phone_ddd_validation(self):
        """Test validação específica de DDDs válidos"""
        # Alguns DDDs válidos
        valid_ddds = ["11", "12", "13", "21", "22", "85", "47", "51"]

        for ddd in valid_ddds:
            phone = f"{ddd}987654321"  # Celular
            assert (
                validate_phone(phone) == True
            ), f"Telefone com DDD {ddd} deveria ser válido"

        # Alguns DDDs inválidos
        invalid_ddds = ["00", "01", "99", "10"]

        for ddd in invalid_ddds:
            phone = f"{ddd}987654321"
            assert (
                validate_phone(phone) == False
            ), f"Telefone com DDD {ddd} deveria ser inválido"

    def test_validate_phone_mobile_format(self):
        """Test validação específica de formato de celular"""
        # Celulares válidos (devem começar com 9)
        valid_mobiles = [
            "11987654321",  # 9 + 8 dígitos
            "21912345678",  # 9 + 8 dígitos
        ]

        for mobile in valid_mobiles:
            assert (
                validate_phone(mobile) == True
            ), f"Celular {mobile} deveria ser válido"

        # Celulares inválidos (11 dígitos mas não começam com 9)
        invalid_mobiles = [
            "11887654321",  # Não começa com 9
            "21812345678",  # Não começa com 9
        ]

        for mobile in invalid_mobiles:
            assert (
                validate_phone(mobile) == False
            ), f"Celular {mobile} deveria ser inválido"


class TestCEPValidator:
    """Testes completos para validação de CEP"""

    def test_validate_cep_valid_formats(self):
        """Test CEPs válidos em diferentes formatos"""
        valid_ceps = [
            "01310100",  # Apenas números
            "01310-100",  # Com hífen
            "12345678",  # Genérico válido
            "00000000",  # Zeros (válido estruturalmente)
            "99999999",  # Noves (válido estruturalmente)
        ]

        for cep in valid_ceps:
            assert validate_cep(cep) == True, f"CEP {cep} deveria ser válido"

    def test_validate_cep_invalid_formats(self):
        """Test CEPs inválidos"""
        invalid_ceps = [
            "",  # Vazio
            "0131010",  # Menos de 8 dígitos
            "013101000",  # Mais de 8 dígitos
            "abcdefgh",  # Não numérico
            "01310-10",  # Com hífen mas formato incompleto
            "01310--100",  # Hífen duplo
            None,  # None
        ]

        for cep in invalid_ceps:
            assert validate_cep(cep) == False, f"CEP {cep} deveria ser inválido"

    def test_validate_cep_edge_cases(self):
        """Test casos extremos de CEP"""
        edge_cases = [
            ("  01310100  ", True),  # Com espaços
            ("01310-100", True),  # Com hífen
            ("01-310-100", False),  # Múltiplos hífens
            ("01.310.100", False),  # Com pontos
        ]

        for cep, expected in edge_cases:
            result = validate_cep(cep)
            assert (
                result == expected
            ), f"CEP '{cep}' esperado {expected}, obtido {result}"


class TestContactsQualityValidator:
    """Testes para validação de qualidade de contatos"""

    def test_validate_contacts_quality_good_data(self):
        """Test validação com dados de boa qualidade"""
        phones = [
            {
                "country_code": "55",
                "number": "11987654321",
                "type": "mobile",
                "is_principal": True,
            }
        ]
        emails = [
            {
                "email_address": "contact@company.com",
                "type": "work",
                "is_principal": True,
            }
        ]
        addresses = [
            {
                "street": "Avenida Paulista",
                "number": "1000",
                "city": "São Paulo",
                "state": "SP",
                "zip_code": "01310100",
                "type": "commercial",
                "is_principal": True,
            }
        ]

        is_valid, message = validate_contacts_quality(phones, emails, addresses)
        assert is_valid == True
        assert message is None

    def test_validate_contacts_quality_no_contacts(self):
        """Test validação sem contatos"""
        is_valid, message = validate_contacts_quality([], [], [])
        assert is_valid == False
        assert "pelo menos um" in message.lower()

    def test_validate_contacts_quality_invalid_phone(self):
        """Test validação com telefone inválido"""
        phones = [{"country_code": "55", "number": "invalid", "type": "mobile"}]

        is_valid, message = validate_contacts_quality(phones, [], [])
        assert is_valid == False
        assert "telefone" in message.lower() and "inválido" in message.lower()

    def test_validate_contacts_quality_invalid_email(self):
        """Test validação com email inválido"""
        emails = [{"email_address": "invalid-email", "type": "work"}]

        is_valid, message = validate_contacts_quality([], emails, [])
        assert is_valid == False
        assert "email" in message.lower() and "inválido" in message.lower()

    def test_validate_contacts_quality_missing_address_fields(self):
        """Test validação com endereço incompleto"""
        addresses = [
            {
                "street": "Rua Teste",
                # Missing required fields like city, state
                "type": "commercial",
            }
        ]

        is_valid, message = validate_contacts_quality([], [], addresses)
        assert is_valid == False
        assert "endereço" in message.lower()

    def test_validate_contacts_quality_multiple_principals(self):
        """Test validação com múltiplos contatos principais"""
        phones = [
            {
                "country_code": "55",
                "number": "11987654321",
                "type": "mobile",
                "is_principal": True,
            },
            {
                "country_code": "55",
                "number": "21987654321",
                "type": "mobile",
                "is_principal": True,
            },
        ]

        is_valid, message = validate_contacts_quality(phones, [], [])
        # Dependendo da implementação, pode ou não permitir múltiplos principais
        # Este teste verifica se a validação é consistente
        assert isinstance(is_valid, bool)
        assert isinstance(message, (str, type(None)))


class TestValidatorsIntegration:
    """Testes de integração dos validadores"""

    def test_all_validators_with_empty_input(self):
        """Test todos os validadores com entrada vazia"""
        validators_and_inputs = [
            (validate_cnpj, ""),
            (validate_cpf, ""),
            (validate_email, ""),
            (validate_phone, ""),
            (validate_cep, ""),
        ]

        for validator_func, empty_input in validators_and_inputs:
            result = validator_func(empty_input)
            assert (
                result == False
            ), f"{validator_func.__name__} deveria retornar False para entrada vazia"

    def test_all_validators_with_none_input(self):
        """Test todos os validadores com entrada None"""
        validators_and_inputs = [
            (validate_cnpj, None),
            (validate_cpf, None),
            (validate_email, None),
            (validate_phone, None),
            (validate_cep, None),
        ]

        for validator_func, none_input in validators_and_inputs:
            result = validator_func(none_input)
            assert (
                result == False
            ), f"{validator_func.__name__} deveria retornar False para entrada None"

    def test_validators_type_safety(self):
        """Test se os validadores lidam bem com tipos inesperados"""
        invalid_types = [123, [], {}, object()]

        validators = [
            validate_cnpj,
            validate_cpf,
            validate_email,
            validate_phone,
            validate_cep,
        ]

        for validator_func in validators:
            for invalid_input in invalid_types:
                try:
                    result = validator_func(invalid_input)
                    # Se não gerar exceção, deve retornar False
                    assert (
                        result == False
                    ), f"{validator_func.__name__} deveria retornar False para tipo {type(invalid_input)}"
                except (TypeError, AttributeError):
                    # É aceitável que some validadores gerem exceções para tipos inválidos
                    # Desde que seja tratado adequadamente no uso
                    pass


class TestValidatorsPerformance:
    """Testes básicos de performance dos validadores"""

    def test_cnpj_validation_performance(self):
        """Test performance da validação de CNPJ"""
        import time

        cnpj = "11222333000144"
        iterations = 1000

        start_time = time.time()
        for _ in range(iterations):
            validate_cnpj(cnpj)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time = total_time / iterations

        # Cada validação deve ser muito rápida (menos de 1ms)
        assert (
            avg_time < 0.001
        ), f"Validação CNPJ muito lenta: {avg_time:.6f}s por validação"

    def test_email_validation_performance(self):
        """Test performance da validação de email"""
        import time

        email = "test@example.com"
        iterations = 1000

        start_time = time.time()
        for _ in range(iterations):
            validate_email(email)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time = total_time / iterations

        # Cada validação deve ser muito rápida (menos de 1ms)
        assert (
            avg_time < 0.001
        ), f"Validação email muito lenta: {avg_time:.6f}s por validação"
