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

    async def send_contract_acceptance_email(
        self,
        company_name: str,
        recipient_email: str,
        recipient_name: str,
        contract_token: str,
    ) -> bool:
        """
        Envia email de aceite de contrato para empresa

        Args:
            company_name: Nome da empresa
            recipient_email: Email do destinatário
            recipient_name: Nome do destinatário
            contract_token: Token de aceite do contrato

        Returns:
            bool: True se enviado com sucesso
        """
        if not self.send_emails:
            print(f"[EMAIL SIMULADO] Aceite de contrato para: {recipient_email}")
            print(f"Token: {contract_token}")
            print(f"Link: {self.frontend_url}/contract-acceptance/{contract_token}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = "ProTeamCare <noreply@protiamcare.com>"
            msg["To"] = recipient_email
            msg["Subject"] = f"Ative sua empresa no ProTeamCare - {company_name}"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Aceite de Contrato - ProTeamCare</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 14px 40px; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                    .token {{ background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; word-break: break-all; margin: 15px 0; }}
                    .highlight {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
                    .checklist {{ background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .checklist li {{ margin: 10px 0; padding-left: 25px; position: relative; }}
                    .checklist li:before {{ content: "✓"; position: absolute; left: 0; color: #28a745; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Bem-vindo ao ProTeamCare!</h1>
                        <p>Sua empresa <strong>{company_name}</strong> foi cadastrada</p>
                    </div>
                    <div class="content">
                        <h2>Olá, {recipient_name}!</h2>

                        <p>Sua empresa foi cadastrada com sucesso no <strong>ProTeamCare</strong>, o sistema completo de gestão para empresas de home care.</p>

                        <div class="highlight">
                            <strong>⚠️ Ação necessária:</strong> Para ativar o acesso ao sistema, você precisa aceitar nossos Termos de Uso e Política de Privacidade.
                        </div>

                        <p><strong>📋 Próximos passos:</strong></p>

                        <div class="checklist">
                            <ul style="list-style: none; padding: 0; margin: 0;">
                                <li>Clique no botão abaixo para acessar os termos</li>
                                <li>Leia atentamente os Termos de Uso</li>
                                <li>Aceite os termos clicando em "Aceitar"</li>
                                <li>Receba email para criar seu usuário gestor</li>
                                <li>Acesse o sistema e comece a usar!</li>
                            </ul>
                        </div>

                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{self.frontend_url}/contract-acceptance/{contract_token}" class="button">
                                📄 Aceitar Termos de Uso
                            </a>
                        </div>

                        <p><strong>Ou copie e cole este link no seu navegador:</strong></p>
                        <div class="token">{self.frontend_url}/contract-acceptance/{contract_token}</div>

                        <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>🔒 Segurança:</strong></p>
                            <p style="margin: 5px 0 0 0;">Este link é único e seguro. Ele expira em <strong>7 dias</strong> por motivos de segurança.</p>
                        </div>

                        <p>Se você não solicitou este cadastro, pode ignorar este email.</p>

                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">

                        <p style="font-size: 12px; color: #666;">
                            <strong>Precisa de ajuda?</strong><br>
                            Entre em contato: suporte@proteamcare.com<br>
                            WhatsApp: (11) 99999-9999
                        </p>
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
            Bem-vindo ao ProTeamCare!

            Olá, {recipient_name}!

            Sua empresa {company_name} foi cadastrada com sucesso no ProTeamCare.

            Para ativar o acesso, você precisa aceitar nossos Termos de Uso.

            Acesse o link abaixo:
            {self.frontend_url}/contract-acceptance/{contract_token}

            Este link expira em 7 dias.

            Próximos passos:
            1. Aceitar os termos de uso
            2. Receber email para criar usuário gestor
            3. Acessar o sistema

            Se você não solicitou este cadastro, pode ignorar este email.

            --
            ProTeamCare
            suporte@proteamcare.com
            """

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with self._create_smtp_connection() as server:
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Erro ao enviar email de aceite de contrato: {str(e)}")
            return False

    async def send_create_manager_email(
        self,
        company_name: str,
        recipient_email: str,
        recipient_name: str,
        user_creation_token: str,
    ) -> bool:
        """
        Envia email para criar usuário gestor após aceite de contrato

        Args:
            company_name: Nome da empresa
            recipient_email: Email do destinatário
            recipient_name: Nome do destinatário
            user_creation_token: Token de criação de usuário

        Returns:
            bool: True se enviado com sucesso
        """
        if not self.send_emails:
            print(f"[EMAIL SIMULADO] Criação de usuário gestor para: {recipient_email}")
            print(f"Token: {user_creation_token}")
            print(f"Link: {self.frontend_url}/create-manager/{user_creation_token}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = "ProTeamCare <noreply@protiamcare.com>"
            msg["To"] = recipient_email
            msg["Subject"] = f"Configure seu acesso - Gestor da {company_name}"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Criar Usuário Gestor - ProTeamCare</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ display: inline-block; background: #28a745; color: white; padding: 14px 40px; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                    .token {{ background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; word-break: break-all; margin: 15px 0; }}
                    .success {{ background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0; }}
                    .steps {{ background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .step {{ margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
                    .step-number {{ display: inline-block; width: 30px; height: 30px; background: #28a745; color: white; border-radius: 50%; text-align: center; line-height: 30px; font-weight: bold; margin-right: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Contrato Aceito!</h1>
                        <p>Agora vamos configurar seu acesso</p>
                    </div>
                    <div class="content">
                        <h2>Olá, {recipient_name}!</h2>

                        <div class="success">
                            <strong>✓ Contrato aceito com sucesso!</strong><br>
                            Agora você precisa criar sua conta de gestor para acessar o sistema.
                        </div>

                        <p>Você será o <strong>Gestor Principal</strong> da empresa <strong>{company_name}</strong>, com acesso total ao sistema.</p>

                        <div class="steps">
                            <h3 style="margin-top: 0;">📝 Como criar sua conta:</h3>

                            <div class="step">
                                <span class="step-number">1</span>
                                <strong>Clique no botão abaixo</strong><br>
                                <small>Você será redirecionado para a página de criação de conta</small>
                            </div>

                            <div class="step">
                                <span class="step-number">2</span>
                                <strong>Preencha seus dados</strong><br>
                                <small>Nome completo, email e senha segura</small>
                            </div>

                            <div class="step">
                                <span class="step-number">3</span>
                                <strong>Confirme a criação</strong><br>
                                <small>Sua conta será criada e você poderá fazer login</small>
                            </div>

                            <div class="step">
                                <span class="step-number">4</span>
                                <strong>Acesse o sistema</strong><br>
                                <small>Comece a usar o ProTeamCare!</small>
                            </div>
                        </div>

                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{self.frontend_url}/create-manager/{user_creation_token}" class="button">
                                👤 Criar Minha Conta
                            </a>
                        </div>

                        <p><strong>Ou copie e cole este link no seu navegador:</strong></p>
                        <div class="token">{self.frontend_url}/create-manager/{user_creation_token}</div>

                        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>⏰ Importante:</strong></p>
                            <p style="margin: 5px 0 0 0;">Este link expira em <strong>24 horas</strong>. Se expirar, entre em contato com o suporte.</p>
                        </div>

                        <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>🎯 O que você poderá fazer:</strong></p>
                            <ul style="margin: 10px 0 0 0;">
                                <li>Gerenciar estabelecimentos</li>
                                <li>Cadastrar clientes e profissionais</li>
                                <li>Controlar contratos e serviços</li>
                                <li>Emitir relatórios gerenciais</li>
                                <li>Configurar assinatura e faturamento</li>
                            </ul>
                        </div>

                        <p>Estamos ansiosos para ter você conosco!</p>
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
            Contrato Aceito! Configure seu acesso

            Olá, {recipient_name}!

            Contrato aceito com sucesso!

            Agora você precisa criar sua conta de gestor da empresa {company_name}.

            Acesse o link abaixo:
            {self.frontend_url}/create-manager/{user_creation_token}

            Este link expira em 24 horas.

            Próximos passos:
            1. Acessar o link
            2. Preencher seus dados
            3. Criar senha segura
            4. Fazer login no sistema

            --
            ProTeamCare
            suporte@proteamcare.com
            """

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with self._create_smtp_connection() as server:
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Erro ao enviar email de criação de gestor: {str(e)}")
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
