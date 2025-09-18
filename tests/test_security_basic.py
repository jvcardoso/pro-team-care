"""
Testes básicos de segurança usando funções realmente disponíveis
"""

from datetime import datetime, timedelta

import jwt
import pytest

from app.infrastructure.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from config.settings import settings


class TestPasswordSecurity:
    """Testes para segurança de senhas"""

    def test_password_hashing_basic(self):
        """Test hash básico de senha"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        # Hash deve ser diferente da senha original
        assert hashed != password

        # Hash deve ter tamanho adequado (bcrypt)
        assert len(hashed) > 50

        # Deve começar com identificador bcrypt
        assert hashed.startswith("$2b$")

    def test_password_verification_correct(self):
        """Test verificação de senha correta"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        # Senha correta deve verificar
        assert verify_password(password, hashed) == True

    def test_password_verification_incorrect(self):
        """Test verificação de senha incorreta"""
        password = "testpassword123"
        wrong_password = "wrongpassword456"
        hashed = get_password_hash(password)

        # Senha incorreta não deve verificar
        assert verify_password(wrong_password, hashed) == False

    def test_password_hash_uniqueness(self):
        """Test que cada hash é único (salt diferente)"""
        password = "testpassword123"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes devem ser diferentes devido ao salt aleatório
        assert hash1 != hash2

        # Mas ambos devem verificar a mesma senha
        assert verify_password(password, hash1) == True
        assert verify_password(password, hash2) == True

    def test_password_security_edge_cases(self):
        """Test casos extremos de segurança de senha"""
        test_cases = [
            "a" * 200,  # Senha muito longa
            "password with spaces",  # Senha com espaços
            "ção@#$%&*()áéíóú",  # Caracteres especiais e acentos
            "123456789",  # Números apenas
        ]

        for password in test_cases:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) == True
            assert verify_password(password + "x", hashed) == False


class TestJWTSecurity:
    """Testes para segurança JWT"""

    def test_create_access_token_basic(self):
        """Test criação básica de token JWT"""
        data = {"sub": "user@example.com", "user_id": 1}
        token = create_access_token(data)

        # Token deve ser string não vazia
        assert isinstance(token, str)
        assert len(token) > 0

        # Token deve ter estrutura JWT (3 partes separadas por .)
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_token_with_expiry(self):
        """Test criação de token com expiração customizada"""
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(minutes=15)

        token = create_access_token(data, expires_delta=expires_delta)

        # Decodificar para verificar expiração
        decoded = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        # Verificar se tem campo de expiração
        assert "exp" in decoded

        # Verificar se expiração é aproximadamente 15 minutos no futuro
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()
        time_diff = exp_time - now

        # Deve ser próximo a 15 minutos (com margem de erro)
        assert 14 * 60 < time_diff.total_seconds() < 16 * 60

    def test_jwt_decode_valid_token(self):
        """Test decodificação de token válido"""
        data = {"sub": "user@example.com", "user_id": 1}
        token = create_access_token(data)

        # Decodificar token
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        assert payload["sub"] == "user@example.com"
        assert payload["user_id"] == 1

    def test_jwt_decode_invalid_token(self):
        """Test decodificação de token inválido"""
        invalid_tokens = [
            "invalid.token.here",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "not-a-jwt-at-all",
        ]

        for token in invalid_tokens:
            with pytest.raises(jwt.InvalidTokenError):
                jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

    def test_jwt_decode_expired_token(self):
        """Test decodificação de token expirado"""
        data = {"sub": "user@example.com"}
        # Criar token que expira imediatamente
        expires_delta = timedelta(seconds=-1)

        token = create_access_token(data, expires_delta=expires_delta)

        # Token expirado deve gerar exceção
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

    def test_jwt_security_manipulation(self):
        """Test resistência a manipulação de JWT"""
        data = {"sub": "user@example.com", "user_id": 1}
        token = create_access_token(data)

        # Tentar modificar o token
        parts = token.split(".")

        # Modificar payload (parte do meio)
        modified_token = f"{parts[0]}.{parts[1][:-1]}x.{parts[2]}"

        # Token modificado deve ser inválido
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(
                modified_token, settings.secret_key, algorithms=[settings.algorithm]
            )


class TestSecurityConfiguration:
    """Testes para configuração de segurança"""

    def test_jwt_secret_strength(self):
        """Test força da chave JWT"""
        secret = settings.secret_key

        # Secret deve ter tamanho mínimo para segurança
        assert len(secret) >= 32, "JWT secret muito curta"

        # Secret não deve ser padrão de desenvolvimento
        default_secrets = [
            "secret",
            "password",
            "your-secret-key-here",
            "development-secret",
        ]

        assert secret.lower() not in default_secrets, "JWT secret insegura detectada"

    def test_cors_configuration(self):
        """Test configuração CORS"""
        allowed_origins = settings.cors_origins_list

        # CORS não deve permitir wildcard em produção
        if settings.is_production:
            assert "*" not in allowed_origins, "CORS wildcard não permitido em produção"

        # Deve ter pelo menos uma origem configurada
        assert len(allowed_origins) > 0, "Nenhuma origem CORS configurada"

    def test_database_url_security(self):
        """Test segurança da URL do banco"""
        db_url = settings.database_url

        # URL não deve estar vazia
        assert db_url, "Database URL não configurada"

        # URL deve usar conexão segura em produção
        if settings.is_production:
            # PostgreSQL com SSL seria ideal
            assert "postgresql" in db_url.lower(), "Banco não PostgreSQL em produção"


class TestInputValidation:
    """Testes básicos de validação de entrada"""

    def test_password_hash_with_none(self):
        """Test hash com entrada None"""
        with pytest.raises((TypeError, AttributeError)):
            get_password_hash(None)

    def test_password_verification_with_none(self):
        """Test verificação com entrada None"""
        password = "test123"
        hashed = get_password_hash(password)

        # Verificar com None deve retornar False ou gerar erro
        try:
            result = verify_password(None, hashed)
            assert result == False
        except (TypeError, AttributeError):
            pass  # É aceitável que gere erro

    def test_jwt_creation_with_empty_data(self):
        """Test criação JWT com dados vazios"""
        empty_data = {}
        token = create_access_token(empty_data)

        # Deve criar token mesmo vazio
        assert isinstance(token, str)
        assert len(token) > 0

        # Deve poder decodificar
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        assert "exp" in payload  # Expiração sempre presente


class TestPerformance:
    """Testes básicos de performance"""

    def test_password_hashing_performance(self):
        """Test performance de hash de senha"""
        import time

        password = "testpassword123"
        iterations = 10  # Bcrypt é intencionalente lento

        start_time = time.time()
        for _ in range(iterations):
            get_password_hash(password)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time = total_time / iterations

        # Bcrypt deve ser relativamente lento (segurança)
        # Mas não excessivamente lento (< 1 segundo por hash)
        assert avg_time < 1.0, f"Hash muito lento: {avg_time:.3f}s por hash"
        assert (
            avg_time > 0.01
        ), f"Hash muito rápido (inseguro): {avg_time:.3f}s por hash"

    def test_jwt_creation_performance(self):
        """Test performance de criação JWT"""
        import time

        data = {"sub": "user@example.com", "user_id": 1}
        iterations = 1000

        start_time = time.time()
        for _ in range(iterations):
            create_access_token(data)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time = total_time / iterations

        # Criação de JWT deve ser rápida (< 1ms)
        assert avg_time < 0.001, f"JWT creation muito lenta: {avg_time:.6f}s por token"
