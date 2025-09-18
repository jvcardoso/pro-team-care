import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings


class EmailService:
    """Serviço de envio de emails para ativação de contas e notificações"""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.smtp_use_tls = settings.smtp_use_tls
        self.smtp_use_ssl = settings.smtp_use_ssl
        self.send_emails = settings.send_emails
        self.frontend_url = settings.frontend_url

    def _create_smtp_connection(self):
        """Cria conexão SMTP"""
        if self.smtp_use_ssl:
            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
        else:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.smtp_use_tls:
                server.starttls()

        if self.smtp_user and self.smtp_password:
            server.login(self.smtp_user, self.smtp_password)

        return server

    async def send_activation_email(
        self,
        email: str,
        activation_token: str,
        user_name: str,
        company_name: str,
        context_type: str = "establishment",
    ) -> bool:
        """
        Envia email de ativação de conta

        Args:
            email: Email do destinatário
            activation_token: Token de ativação
            user_name: Nome do usuário
            company_name: Nome da empresa
            context_type: Tipo de contexto (company, establishment, client)

        Returns:
            bool: True se enviado com sucesso
        """
        if not self.send_emails:
            print(f"[EMAIL SIMULADO] Ativação para: {email}")
            print(f"Token: {activation_token}")
            print(f"Link: {self.frontend_url}/activate/{activation_token}")
            return True

        try:
            # Determinar tipo de gestor
            manager_type = {
                "company": "Gestor da Empresa",
                "establishment": "Gestor do Estabelecimento",
                "client": "Cliente",
            }.get(context_type, "Usuário")

            # Criar mensagem
            msg = MIMEMultipart("alternative")
            msg["From"] = "ProTeamCare <noreply@protiamcare.com>"
            msg["To"] = email
            msg["Subject"] = f"Ative sua conta - {manager_type} | {company_name}"

            # Template HTML
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Ativação de Conta</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                    .token {{ background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; word-break: break-all; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Bem-vindo ao ProTeamCare!</h1>
                        <p>Sua conta foi criada com sucesso</p>
                    </div>
                    <div class="content">
                        <h2>Olá, {user_name}!</h2>

                        <p>Você foi convidado para ser <strong>{manager_type}</strong> da empresa <strong>{company_name}</strong>.</p>

                        <p>Para ativar sua conta e definir sua senha, clique no botão abaixo:</p>

                        <div style="text-align: center;">
                            <a href="{self.frontend_url}/activate/{activation_token}" class="button">
                                🔐 Ativar Conta
                            </a>
                        </div>

                        <p><strong>Ou copie e cole este link no seu navegador:</strong></p>
                        <div class="token">{self.frontend_url}/activate/{activation_token}</div>

                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">

                        <h3>📋 Próximos passos:</h3>
                        <ul>
                            <li>Clique no link de ativação acima</li>
                            <li>Defina uma senha segura</li>
                            <li>Faça login no sistema</li>
                            <li>Complete seu perfil</li>
                        </ul>

                        <p><strong>⚠️ Importante:</strong> Este link expira em 24 horas por segurança.</p>

                        <p>Se você não solicitou esta conta, pode ignorar este email.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 ProTeamCare. Todos os direitos reservados.</p>
                        <p>Este é um email automático, não responda.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Template texto simples
            text_content = f"""
            Bem-vindo ao ProTeamCare!

            Olá, {user_name}!

            Você foi convidado para ser {manager_type} da empresa {company_name}.

            Para ativar sua conta, acesse o link abaixo:
            {self.frontend_url}/activate/{activation_token}

            Este link expira em 24 horas.

            Se você não solicitou esta conta, pode ignorar este email.

            --
            ProTeamCare
            """

            # Anexar conteúdo
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Enviar email
            with self._create_smtp_connection() as server:
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Erro ao enviar email de ativação: {str(e)}")
            return False

    async def send_password_reset_email(
        self, email: str, reset_token: str, user_name: str
    ) -> bool:
        """
        Envia email de reset de senha

        Args:
            email: Email do destinatário
            reset_token: Token de reset
            user_name: Nome do usuário

        Returns:
            bool: True se enviado com sucesso
        """
        if not self.send_emails:
            print(f"[EMAIL SIMULADO] Reset de senha para: {email}")
            print(f"Token: {reset_token}")
            print(f"Link: {self.frontend_url}/reset-password/{reset_token}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = "ProTeamCare <noreply@protiamcare.com>"
            msg["To"] = email
            msg["Subject"] = "Redefinir sua senha - ProTeamCare"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Redefinir Senha</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #dc3545; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                    .token {{ background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; word-break: break-all; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔒 Redefinir Senha</h1>
                        <p>Solicitação de nova senha</p>
                    </div>
                    <div class="content">
                        <h2>Olá, {user_name}!</h2>

                        <p>Recebemos uma solicitação para redefinir a senha da sua conta.</p>

                        <p>Para criar uma nova senha, clique no botão abaixo:</p>

                        <div style="text-align: center;">
                            <a href="{self.frontend_url}/reset-password/{reset_token}" class="button">
                                🔐 Redefinir Senha
                            </a>
                        </div>

                        <p><strong>Ou copie e cole este link no seu navegador:</strong></p>
                        <div class="token">{self.frontend_url}/reset-password/{reset_token}</div>

                        <p><strong>⚠️ Importante:</strong> Este link expira em 1 hora por segurança.</p>

                        <p>Se você não solicitou esta redefinição, pode ignorar este email. Sua senha atual permanecerá inalterada.</p>
                    </div>
                    <div class="footer">
                        <p>© 2025 ProTeamCare. Todos os direitos reservados.</p>
                        <p>Este é um email automático, não responda.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_content = f"""
            Redefinir Senha - ProTeamCare

            Olá, {user_name}!

            Recebemos uma solicitação para redefinir a senha da sua conta.

            Para criar uma nova senha, acesse o link abaixo:
            {self.frontend_url}/reset-password/{reset_token}

            Este link expira em 1 hora.

            Se você não solicitou esta redefinição, pode ignorar este email.

            --
            ProTeamCare
            """

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with self._create_smtp_connection() as server:
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Erro ao enviar email de reset: {str(e)}")
            return False

    @staticmethod
    def generate_token() -> str:
        """Gera token seguro para ativação/reset"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def get_token_expiry(hours: int = 24) -> datetime:
        """Retorna data de expiração do token"""
        return datetime.utcnow() + timedelta(hours=hours)

    @staticmethod
    def is_token_valid(expires_at: Optional[datetime]) -> bool:
        """Verifica se token ainda é válido"""
        if not expires_at:
            return False
        return datetime.utcnow() < expires_at
