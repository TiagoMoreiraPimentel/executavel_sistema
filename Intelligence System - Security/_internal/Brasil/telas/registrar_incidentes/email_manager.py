"""
Módulo para gerenciamento de emails de incidentes.
Autor: Sistema InCON
Versão: 1.2 - Corrigido para permissão "Send on behalf"
"""

import smtplib
import json
import os
import logging
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import oracledb

# ----------------------------------------------------
# FUNÇÃO DE CAMINHO PARA PYINSTALLER
# ----------------------------------------------------
def resource_path(relative_path):
    """
    Obtém o caminho absoluto para o recurso, suportando ambiente PyInstaller (sys._MEIPASS).
    O path relativo deve ser em relação à raiz do executável.
    """
    try:
        # Quando rodando no executável, a base é a pasta temporária (_internal)
        base_path = sys._MEIPASS
    except Exception:
        # Quando rodando em desenvolvimento (PyCharm), a base é o diretório do projeto (SINISTROS)
        # O caminho completo deve ser resolvido a partir daqui.
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ----------------------------------------------------

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailManager:
    """
    Classe principal para gerenciar o envio de emails de notificação de incidentes.
    Configurado para servidor SMTP da DHL com suporte a permissão "Send on behalf".
    """

    def __init__(self, config_path=None):
        """
        Inicializa o gerenciador de emails.
        """
        if config_path is None:
            # ⚠️ NOVO: Caminhos relativos à raiz do projeto SINISTROS
            dhl_config_rel_path = os.path.join('Brasil', 'telas', 'registrar_incidentes', 'up_email_config_dhl.json')

            # Tenta encontrar o arquivo usando o resolvedor de caminho
            resolved_dhl_config = resource_path(dhl_config_rel_path)

            if os.path.exists(resolved_dhl_config):
                config_path = resolved_dhl_config
                print("✅ Usando configuração DHL")
            else:
                # Se não encontrar, config_path é None e passamos para _load_config
                pass

        self.config = self._load_config(config_path)
        logger.info(f"EmailManager inicializado para: {self.config['sender_email']}")
        logger.info(f"Usuário autenticação: {self.config['auth_user']}")

    def _load_config(self, config_path):
        """
        Carrega a configuração do email.
        """
        # 💥 Adicionar verificação para config_path None 💥
        if config_path is None:
            logger.error("Erro: Caminho de configuração não fornecido. Usando fallback.")
            # Configuração padrão de fallback para DHL (mantida de sua função original)
            return {
                "smtp_server": "smtp.dhl.com",
                "smtp_port": 25,
                "sender_email": "system.incon@dhl.com",  # Caixa compartilhada (From)
                "auth_user": "tiago.moreirap@dhl.com",  # QUEM LOGA (usuário com permissão)
                "sender_password": "Security302416*",  # SENHA DO TIAGO
                "default_recipient": "tiago.moreirap@dhl.com",
                "use_tls": True,
                "use_ssl": False
            }
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Validação mínima
            if 'smtp_server' not in config:
                config['smtp_server'] = 'smtp.dhl.com'
            if 'smtp_port' not in config:
                config['smtp_port'] = 25  # Alterado para 25 (padrão DHL)
            if 'sender_email' not in config:
                config['sender_email'] = 'system.incon@dhl.com'
            if 'auth_user' not in config:
                config['auth_user'] = 'tiago.moreirap@dhl.com'
            if 'sender_password' not in config:
                config['sender_password'] = 'Security302416*'
            if 'default_recipient' not in config:
                config['default_recipient'] = 'tiago.moreirap@dhl.com'
            if 'use_tls' not in config:
                config['use_tls'] = True
            if 'use_ssl' not in config:
                config['use_ssl'] = False

            logger.info(f"Configuração carregada de: {os.path.basename(config_path)}")
            return config

        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            # Configuração padrão de fallback para DHL
            return {
                "smtp_server": "smtp.dhl.com",
                "smtp_port": 25,
                "sender_email": "system.incon@dhl.com",
                "auth_user": "tiago.moreirap@dhl.com",
                "sender_password": "Security302416*",
                "default_recipient": "tiago.moreirap@dhl.com",
                "use_tls": True,
                "use_ssl": False
            }

    @staticmethod
    def _formatar_valor(valor):
        """
        Formata um valor para exibição, tratando valores nulos ou vazios.
        """
        if valor in [None, "", "N/A", "Selecione uma informação", "NÃO INFORMADO"]:
            return "NÃO INFORMADO"
        return valor

    def enviar_notificacao_incidente(self, dados_incidente, logics_pai, destinatarios=None):
        """
        Método principal para enviar notificação de incidente.
        Retorna True se o email foi enviado com sucesso.
        """
        try:
            logger.info(f"Iniciando envio de email para incidente {logics_pai}")

            # Criar a mensagem de email
            msg = self._criar_email_incidente(dados_incidente, logics_pai, destinatarios)

            # Enviar o email
            sucesso = self._enviar_email_smtp(msg)

            if sucesso:
                logger.info(f"Email para incidente {logics_pai} enviado com sucesso")
                print(f"✅ Email enviado com sucesso!")
            else:
                logger.warning(f"Falha ao enviar email para incidente {logics_pai}")
                print(f"❌ Falha ao enviar email")

            return sucesso

        except Exception as e:
            logger.error(f"Erro no processo de envio de email: {e}")
            print(f"❌ Erro ao enviar email: {e}")
            return False

    def enviar_notificacao_atualizacao(self, dados_incidente, logics_pai, destinatarios=None):
        """
        Método específico para enviar notificação de ATUALIZAÇÃO de incidente.
        Retorna True se o email foi enviado com sucesso.
        """
        try:
            logger.info(f"Iniciando envio de email de ATUALIZAÇÃO para incidente {logics_pai}")

            # Criar a mensagem de email com título específico
            msg = self._criar_email_atualizacao(dados_incidente, logics_pai, destinatarios)

            # Enviar o email
            sucesso = self._enviar_email_smtp(msg)

            if sucesso:
                logger.info(f"Email para incidente {logics_pai} enviado com sucesso")
                print(f"✅ Email enviado com sucesso!")
            else:
                logger.warning(f"Falha ao enviar email de ATUALIZAÇÃO para incidente {logics_pai}")
                print(f"❌ Falha ao enviar email de ATUALIZAÇÃO")

            return sucesso

        except Exception as e:
            logger.error(f"Erro no processo de envio de email de ATUALIZAÇÃO: {e}")
            print(f"❌ Erro ao enviar email de ATUALIZAÇÃO: {e}")
            return False

    def _criar_email_incidente(self, dados_incidente, logics_pai, destinatarios=None):
        """
        Cria a mensagem de email com os dados do incidente.

        Args:
            dados_incidente: Dicionário com dados do incidente
            logics_pai: Número do incidente LOGICS
            destinatarios: Dicionário com listas 'TO' e 'CC' (opcional)
        """
        assunto = f"Comunicado de Incidente - {logics_pai}"

        # Corpo do email em HTML e texto simples
        corpo_html = self._gerar_corpo_email_html(dados_incidente, logics_pai, 'cadastro')
        corpo_texto = self._gerar_corpo_email_texto(dados_incidente, logics_pai)

        # Criar mensagem multipart
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto

        # 🔧 IMPORTANTE: Para "Send on behalf", usar apenas a caixa compartilhada no From
        # O Exchange/Office 365 adicionará automaticamente "on behalf of"
        shared_mailbox = self.config.get('sender_email', 'system.incon@dhl.com')
        msg['From'] = shared_mailbox

        # Adicionar cabeçalho Sender opcional (pode ajudar em alguns servidores)
        auth_user = self.config.get('auth_user', 'tiago.moreirap@dhl.com')
        msg['Sender'] = auth_user

        # Se não fornecido, busca destinatários
        if not destinatarios:
            destinatarios = self.obter_destinatarios('CADASTRO')

        # Configura destinatários TO e CC
        if destinatarios['TO']:
            msg['To'] = ", ".join(destinatarios['TO'])

        if destinatarios['CC']:
            msg['Cc'] = ", ".join(destinatarios['CC'])

        # Adicionar versão texto
        parte_texto = MIMEText(corpo_texto, 'plain', 'utf-8')
        msg.attach(parte_texto)

        # Adicionar versão HTML
        parte_html = MIMEText(corpo_html, 'html', 'utf-8')
        msg.attach(parte_html)

        return msg

    def _criar_email_atualizacao(self, dados_incidente, logics_pai, destinatarios=None):
        """
        Cria a mensagem de email de ATUALIZAÇÃO com os dados do incidente.

        Args:
            dados_incidente: Dicionário com dados do incidente
            logics_pai: Número do incidente LOGICS
            destinatarios: Dicionário com listas 'TO' e 'CC' (opcional)
        """
        assunto = f"ATUALIZAÇÃO de Incidente - {logics_pai}"

        # Corpo do email em HTML e texto simples
        corpo_html = self._gerar_corpo_email_html(dados_incidente, logics_pai, 'atualizacao')
        corpo_texto = self._gerar_corpo_email_atualizacao(dados_incidente, logics_pai)

        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto

        # 🔧 IMPORTANTE: Para "Send on behalf", usar apenas a caixa compartilhada no From
        shared_mailbox = self.config.get('sender_email', 'system.incon@dhl.com')
        msg['From'] = shared_mailbox

        # Adicionar cabeçalho Sender
        auth_user = self.config.get('auth_user', 'tiago.moreirap@dhl.com')
        msg['Sender'] = auth_user

        # Se não fornecido, busca destinatários
        if not destinatarios:
            destinatarios = self.obter_destinatarios('ATUALIZACAO')

        # Configura destinatários TO e CC
        if destinatarios['TO']:
            msg['To'] = ", ".join(destinatarios['TO'])

        if destinatarios['CC']:
            msg['Cc'] = ", ".join(destinatarios['CC'])

        # Adicionar versão texto
        parte_texto = MIMEText(corpo_texto, 'plain', 'utf-8')
        msg.attach(parte_texto)

        # Adicionar versão HTML
        parte_html = MIMEText(corpo_html, 'html', 'utf-8')
        msg.attach(parte_html)

        return msg

    def _gerar_corpo_email_html(self, dados_incidente, logics_pai, tipo='cadastro'):
        """
        Gera o corpo do email em HTML com design moderno e cores DHL.

        Args:
            dados_incidente: Dicionário com os dados do incidente.
            logics_pai: Número do incidente LOGICS.
            tipo: 'cadastro' ou 'atualizacao'.

        Returns:
            String com o HTML do email.
        """

        # Título baseado no tipo
        if tipo == 'cadastro':
            titulo = "COMUNICADO DE INCIDENTE"
            subtitulo = "⚠️ INCIDENTE REGISTRADO NO SISTEMA"
        else:
            titulo = "ATUALIZAÇÃO DE INCIDENTE"
            subtitulo = "⚠️ INCIDENTE ATUALIZADO NO SISTEMA"

        # Data e hora
        data_hora = dados_incidente.get('data_hora_registro', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

        # Início do HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{titulo} - {logics_pai}</title>
            <style>
                /* Estilos globais */
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
                }}
                /* Cabeçalho com cores DHL */
                .header {{
                    background-color: #333333;
                    color: #D40511; /* Vermelho DHL */
                    padding: 20px;
                    text-align: center;
                    border-bottom: 5px solid #D40511;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    color: #ffffff;
                }}
                .header h2 {{
                    margin: 10px 0 0;
                    font-size: 18px;
                    font-weight: normal;
                    color: #ffffff;
                }}
                /* Corpo do email */
                .content {{
                    padding: 30px;
                }}
                .section {{
                    margin-bottom: 25px;
                    border-left: 4px solid #FFCC00;
                    padding-left: 15px;
                }}
                .section h3 {{
                    color: #D40511;
                    margin-top: 0;
                    font-size: 18px;
                    display: flex;
                    align-items: center;
                }}
                .section h3::before {{
                    content: '';
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    margin-right: 10px;
                    background-color: #FFCC00;
                    border-radius: 50%;
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                    gap: 15px;
                }}
                .info-item {{
                    display: flex;
                    align-items: baseline;
                }}
                .info-item strong {{
                    display: inline;
                    min-width: 180px;
                    margin-right: 8px;
                }}
                .info-item span {{
                    flex: 1;
                }}
                /* Tabela de clientes */
                .clientes-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                    background-color: #ffffff;
                    border-radius: 6px;
                    overflow: hidden; /* garante cantos arredondados */
                }}

                /* Cabeçalho */
                .clientes-table th {{
                    background-color: #333333; /* escuro, elegante */
                    color: #ffffff;
                    padding: 12px 14px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: 600;
                    border: 1px solid #444444;
                    white-space: nowrap;
                }}

                /* Células */
                .clientes-table td {{
                    padding: 10px 14px;
                    font-size: 13px;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                }}

                /* Zebra striping (melhora leitura) */
                .clientes-table tbody tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}

                /* Hover sutil */
                .clientes-table tbody tr:hover {{
                    background-color: #f1f1f1;
                }}

                /* Valores monetários alinhados à direita */
                .clientes-table td:nth-child(3),
                .clientes-table td:nth-child(4),
                .clientes-table td:nth-child(5) {{
                    text-align: right;
                    font-weight: 500;
                }}

                /* Destaque sutil para valor perdido */
                .clientes-table td:nth-child(5) {{
                    color: #D40511; /* vermelho DHL */
                    font-weight: 600;
                }}
                .totais {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 20px;
                    border-left: 4px solid #D40511;
                }}
                .totais h4 {{
                    color: #D40511;
                    margin-top: 0;
                }}
                /* Descrição */
                .descricao {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    white-space: pre-line;
                    font-size: 14px;
                }}
                /* Rodapé */
                .footer {{
                    background-color: #333333;
                    color: #ffffff;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                }}
                .footer a {{
                    color: #FFCC00;
                    text-decoration: none;
                }}
                /* Responsividade */
                @media (max-width: 600px) {{
                    .info-grid {{
                        grid-template-columns: 1fr;
                    }}
                    .content {{
                        padding: 15px;
                    }}
                    .info-item strong {{
                        min-width: 140px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{titulo} - SISTEMA INCON</h1>
                    <h2>{subtitulo}</h2>
                </div>
                <div class="content">
                    <!-- Identificação -->
                    <div class="section">
                        <h3>IDENTIFICAÇÃO</h3>
                        <div class="info-grid">
                            <div class="info-item">
                                <strong>Incidente LOGICS:</strong>
                                <span>{logics_pai}</span>
                            </div>
                            <div class="info-item">
                                <strong>Data/Hora do Registro:</strong>
                                <span>{data_hora}</span>
                            </div>
                            <div class="info-item">
                                <strong>Usuário Responsável:</strong>
                                <span>{self._formatar_valor(dados_incidente.get('usuario_responsavel'))}</span>
                            </div>
                        </div>
                    </div>
        """

        # Informações do Incidente
        html += """
                    <div class="section">
                        <h3>INFORMAÇÕES DO INCIDENTE</h3>
                        <div class="info-grid">
        """
        campos_incidente = [
            ('Nº Viagem BENNER', 'N_BENNER'),
            ('Nº SM', 'N_SM'),
            ('Nº Ocorrência', 'OCORRENCIA'),
            ('Tipo de Incidente', 'TIPO_INCIDENTE'),
            ('Data do Incidente', 'DATA_INCIDENTE'),
            ('Hora do Incidente', 'HORA_INCIDENTE'),
            ('Período do Dia', 'PERIODO_INCIDENTE'),
        ]
        for label, key in campos_incidente:
            html += f"""
                            <div class="info-item">
                                <strong>{label}:</strong>
                                <span>{self._formatar_valor(dados_incidente.get(key))}</span>
                            </div>
            """
        html += """
                        </div>
                    </div>
        """

        # Localização
        html += """
                    <div class="section">
                        <h3>LOCALIZAÇÃO</h3>
                        <div class="info-grid">
        """
        campos_localizacao = [
            ('Região', 'REGIAO_INCIDENTE'),
            ('Estado', 'ESTADO_INCIDENTE'),
            ('Cidade', 'CIDADE_INCIDENTE'),
            ('Local (Rua/Rodovia)', 'END_INCIDENTE'),
            ('Estrada/Urbana', 'ESTRADA_URBANA'),
        ]
        for label, key in campos_localizacao:
            html += f"""
                            <div class="info-item">
                                <strong>{label}:</strong>
                                <span>{self._formatar_valor(dados_incidente.get(key))}</span>
                            </div>
            """

        # Coordenadas (tratamento especial)
        lat = self._formatar_valor(dados_incidente.get('LATITUDE'))
        lon = self._formatar_valor(dados_incidente.get('LONGITUDE'))
        html += f"""
                            <div class="info-item">
                                <strong>Coordenadas:</strong>
                                <span>Lat {lat}, Long {lon}</span>
                            </div>
        """

        html += """
                        </div>
                    </div>
        """

        # Dados de Transporte
        html += """
                    <div class="section">
                        <h3>DADOS DE TRANSPORTE</h3>
                        <div class="info-grid">
        """
        campos_transporte = [
            ('Transportador', 'TRANSPORTADOR_INCIDENTES'),
            ('Fase Transporte', 'TRANSPORTE'),
            ('Placa Cavalo', 'PLACA_CAVALO'),
            ('Placa Baú', 'PLACA_BAU'),
            ('CPF Motorista', 'CPF_MOTORISTA'),
            ('Rastreado Por', 'RASTREADO_POR'),
            ('Tracking Cell', 'TRACKING_CELL'),
        ]
        for label, key in campos_transporte:
            html += f"""
                            <div class="info-item">
                                <strong>{label}:</strong>
                                <span>{self._formatar_valor(dados_incidente.get(key))}</span>
                            </div>
            """
        html += """
                        </div>
                    </div>
        """

        # Detalhes Operacionais
        html += """
                    <div class="section">
                        <h3>DETALHES OPERACIONAIS</h3>
                        <div class="info-grid">
        """
        campos_operacionais = [
            ('Falha RM', 'FALHA_RM'),
            ('Local Caminhão', 'END_CAMINHAO'),
            ('Local Carga', 'END_CARGA'),
            ('Origem', 'ORIGEM'),
            ('Destino', 'DESTINO'),
        ]
        for label, key in campos_operacionais:
            html += f"""
                            <div class="info-item">
                                <strong>{label}:</strong>
                                <span>{self._formatar_valor(dados_incidente.get(key))}</span>
                            </div>
            """
        html += """
                        </div>
                    </div>
        """

        # Clientes e Valores (se houver)
        if dados_incidente.get('clientes'):
            html += """
                    <div class="section">
                        <h3>CLIENTES E VALORES ENVOLVIDOS</h3>
                        <table class="clientes-table">
                            <thead>
                                <tr>
                                    <th>Cliente</th>
                                    <th>Setor</th>
                                    <th>Valor Carga</th>
                                    <th>Valor Recuperado</th>
                                    <th>Valor Perdido</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            total_carga = 0
            total_recuperado = 0
            total_perdido = 0

            for cliente in dados_incidente['clientes']:
                valor_carga = float(cliente.get('VALOR_CARGA_BENNER', 0))
                valor_recuperado = float(cliente.get('VALOR_RECUPERADO', 0))
                valor_perdido = float(cliente.get('VALOR_PERDIDO', 0))

                total_carga += valor_carga
                total_recuperado += valor_recuperado
                total_perdido += valor_perdido

                html += f"""
                                <tr>
                                    <td>{self._formatar_valor(cliente.get('CLIENTE_INCON'))}</td>
                                    <td>{self._formatar_valor(cliente.get('SETOR'))}</td>
                                    <td>R$ {valor_carga:,.2f}</td>
                                    <td>R$ {valor_recuperado:,.2f}</td>
                                    <td>R$ {valor_perdido:,.2f}</td>
                                </tr>
                """

            html += f"""
                            </tbody>
                        </table>
                        <div class="totais">
                            <h4>TOTAIS</h4>
                            <div class="info-grid">
                                <div class="info-item">
                                    <strong>Valor Total Carga:</strong>
                                    <span>R$ {total_carga:,.2f}</span>
                                </div>
                                <div class="info-item">
                                    <strong>Valor Total Recuperado:</strong>
                                    <span>R$ {total_recuperado:,.2f}</span>
                                </div>
                                <div class="info-item">
                                    <strong>Valor Total Perdido:</strong>
                                    <span>R$ {total_perdido:,.2f}</span>
                                </div>
                            </div>
                        </div>
                    </div>
            """

        # Descrição
        descricao = self._formatar_valor(dados_incidente.get('DESCRICAO_INCIDENTE'))
        html += f"""
                    <div class="section">
                        <h3>DESCRIÇÃO DO INCIDENTE</h3>
                        <div class="descricao">{descricao}</div>
                    </div>
                </div>
                <div class="footer">
                    <p>Email gerado automaticamente pelo <strong>Sistema INCON</strong></p>
                    <p>Para mais informações, acesse o sistema de gestão de incidentes.</p>
                    <p>DHL Supply Chain &copy; {datetime.now().year} - Todos os direitos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _gerar_corpo_email_texto(self, dados_incidente, logics_pai):
        """
        Gera o corpo do email em texto simples (fallback para clientes de email que não suportam HTML).
        """
        data_hora_registro = dados_incidente.get('data_hora_registro',
                                                 datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

        texto = f"""
{'=' * 60}
COMUNICADO DE INCIDENTE - SISTEMA INCON
{'=' * 60}

⚠️ INCIDENTE REGISTRADO NO SISTEMA

IDENTIFICAÇÃO:
{'-' * 40}
Incidente LOGICS: {logics_pai}
Data/Hora do Registro: {data_hora_registro}
Usuário Responsável: {self._formatar_valor(dados_incidente.get('usuario_responsavel'))}

📋 INFORMAÇÕES DO INCIDENTE:
{'-' * 40}
• Nº Viagem BENNER: {self._formatar_valor(dados_incidente.get('N_BENNER'))}
• Nº SM: {self._formatar_valor(dados_incidente.get('N_SM'))}
• Nº Ocorrência: {self._formatar_valor(dados_incidente.get('OCORRENCIA'))}
• Tipo de Incidente: {self._formatar_valor(dados_incidente.get('TIPO_INCIDENTE'))}
• Data do Incidente: {self._formatar_valor(dados_incidente.get('DATA_INCIDENTE'))}
• Hora do Incidente: {self._formatar_valor(dados_incidente.get('HORA_INCIDENTE'))}
• Período do Dia: {self._formatar_valor(dados_incidente.get('PERIODO_INCIDENTE'))}

📍 LOCALIZAÇÃO:
{'-' * 40}
• Região: {self._formatar_valor(dados_incidente.get('REGIAO_INCIDENTE'))}
• Estado: {self._formatar_valor(dados_incidente.get('ESTADO_INCIDENTE'))}
• Cidade: {self._formatar_valor(dados_incidente.get('CIDADE_INCIDENTE'))}
• Local (Rua/Rodovia): {self._formatar_valor(dados_incidente.get('END_INCIDENTE'))}
• Estrada/Urbana: {self._formatar_valor(dados_incidente.get('ESTRADA_URBANA'))}
• Coordenadas: Lat {self._formatar_valor(dados_incidente.get('LATITUDE'))}, Long {self._formatar_valor(dados_incidente.get('LONGITUDE'))}

🚚 DADOS DE TRANSPORTE:
{'-' * 40}
• Transportador: {self._formatar_valor(dados_incidente.get('TRANSPORTADOR_INCIDENTES'))}
• Fase Transporte: {self._formatar_valor(dados_incidente.get('TRANSPORTE'))}
• Placa Cavalo: {self._formatar_valor(dados_incidente.get('PLACA_CAVALO'))}
• Placa Baú: {self._formatar_valor(dados_incidente.get('PLACA_BAU'))}
• CPF Motorista: {self._formatar_valor(dados_incidente.get('CPF_MOTORISTA'))}
• Rastreado Por: {self._formatar_valor(dados_incidente.get('RASTREADO_POR'))}
• Tracking Cell: {self._formatar_valor(dados_incidente.get('TRACKING_CELL'))}

⚠️ DETALHES OPERACIONAIS:
{'-' * 40}
• Falha RM: {self._formatar_valor(dados_incidente.get('FALHA_RM'))}
• Local Caminhão: {self._formatar_valor(dados_incidente.get('END_CAMINHAO'))}
• Local Carga: {self._formatar_valor(dados_incidente.get('END_CARGA'))}
• Origem: {self._formatar_valor(dados_incidente.get('ORIGEM'))}
• Destino: {self._formatar_valor(dados_incidente.get('DESTINO'))}
"""

        # Adicionar clientes e valores
        if dados_incidente.get('clientes'):
            texto += f"\n💼 CLIENTES E VALORES ENVOLVIDOS:\n{'-' * 40}\n"

            total_carga = 0
            total_recuperado = 0
            total_perdido = 0

            for i, cliente in enumerate(dados_incidente['clientes'], 1):
                valor_carga = float(cliente.get('VALOR_CARGA_BENNER', 0))
                valor_recuperado = float(cliente.get('VALOR_RECUPERADO', 0))
                valor_perdido = float(cliente.get('VALOR_PERDIDO', 0))

                texto += f"\n{i}. {self._formatar_valor(cliente.get('CLIENTE_INCON'))}\n"
                texto += f"   Setor: {self._formatar_valor(cliente.get('SETOR'))}\n"
                texto += f"   Valor Carga: R$ {valor_carga:,.2f}\n"
                texto += f"   Valor Recuperado: R$ {valor_recuperado:,.2f}\n"
                texto += f"   Valor Perdido: R$ {valor_perdido:,.2f}\n"

                total_carga += valor_carga
                total_recuperado += valor_recuperado
                total_perdido += valor_perdido

            texto += f"\nTOTAIS:\n"
            texto += f"• Valor Total Carga: R$ {total_carga:,.2f}\n"
            texto += f"• Valor Total Recuperado: R$ {total_recuperado:,.2f}\n"
            texto += f"• Valor Total Perdido: R$ {total_perdido:,.2f}\n"

        # Adicionar descrição
        texto += f"\n📝 DESCRIÇÃO DO INCIDENTE:\n{'-' * 40}\n"
        texto += self._formatar_valor(dados_incidente.get('DESCRICAO_INCIDENTE')) + "\n"

        texto += f"\n{'=' * 60}\n"
        texto += "Email gerado automaticamente pelo Sistema INCON\n"
        texto += "Para mais informações, acesse o sistema de gestão de incidentes.\n"
        texto += f"{'=' * 60}\n"

        return texto

    def _gerar_corpo_email_atualizacao(self, dados_incidente, logics_pai):
        """
        Gera o corpo do email de ATUALIZAÇÃO em texto simples.
        """
        data_hora_registro = dados_incidente.get('data_hora_registro',
                                                 datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

        texto = f"""
{'=' * 60}
ATUALIZAÇÃO DE INCIDENTE - SISTEMA INCON
{'=' * 60}

⚠️ INCIDENTE ATUALIZADO NO SISTEMA

IDENTIFICAÇÃO:
{'-' * 40}
Incidente LOGICS: {logics_pai}
Data/Hora da Atualização: {data_hora_registro}
Usuário Responsável: {self._formatar_valor(dados_incidente.get('usuario_responsavel'))}

📋 INFORMAÇÕES DO INCIDENTE:
{'-' * 40}
• Nº Viagem BENNER: {self._formatar_valor(dados_incidente.get('N_BENNER'))}
• Nº SM: {self._formatar_valor(dados_incidente.get('N_SM'))}
• Nº Ocorrência: {self._formatar_valor(dados_incidente.get('OCORRENCIA'))}
• Tipo de Incidente: {self._formatar_valor(dados_incidente.get('TIPO_INCIDENTE'))}
• Data do Incidente: {self._formatar_valor(dados_incidente.get('DATA_INCIDENTE'))}
• Hora do Incidente: {self._formatar_valor(dados_incidente.get('HORA_INCIDENTE'))}
• Período do Dia: {self._formatar_valor(dados_incidente.get('PERIODO_INCIDENTE'))}

📍 LOCALIZAÇÃO:
{'-' * 40}
• Região: {self._formatar_valor(dados_incidente.get('REGIAO_INCIDENTE'))}
• Estado: {self._formatar_valor(dados_incidente.get('ESTADO_INCIDENTE'))}
• Cidade: {self._formatar_valor(dados_incidente.get('CIDADE_INCIDENTE'))}
• Local (Rua/Rodovia): {self._formatar_valor(dados_incidente.get('END_INCIDENTE'))}
• Estrada/Urbana: {self._formatar_valor(dados_incidente.get('ESTRADA_URBANA'))}
• Coordenadas: Lat {self._formatar_valor(dados_incidente.get('LATITUDE'))}, Long {self._formatar_valor(dados_incidente.get('LONGITUDE'))}

🚚 DADOS DE TRANSPORTE:
{'-' * 40}
• Transportador: {self._formatar_valor(dados_incidente.get('TRANSPORTADOR_INCIDENTES'))}
• Fase Transporte: {self._formatar_valor(dados_incidente.get('TRANSPORTE'))}
• Placa Cavalo: {self._formatar_valor(dados_incidente.get('PLACA_CAVALO'))}
• Placa Baú: {self._formatar_valor(dados_incidente.get('PLACA_BAU'))}
• CPF Motorista: {self._formatar_valor(dados_incidente.get('CPF_MOTORISTA'))}
• Rastreado Por: {self._formatar_valor(dados_incidente.get('RASTREADO_POR'))}
• Tracking Cell: {self._formatar_valor(dados_incidente.get('TRACKING_CELL'))}

⚠️ DETALHES OPERACIONAIS:
{'-' * 40}
• Falha RM: {self._formatar_valor(dados_incidente.get('FALHA_RM'))}
• Local Caminhão: {self._formatar_valor(dados_incidente.get('END_CAMINHAO'))}
• Local Carga: {self._formatar_valor(dados_incidente.get('END_CARGA'))}
• Origem: {self._formatar_valor(dados_incidente.get('ORIGEM'))}
• Destino: {self._formatar_valor(dados_incidente.get('DESTINO'))}
"""

        # Adicionar clientes e valores
        if dados_incidente.get('clientes'):
            texto += f"\n💼 CLIENTES E VALORES ENVOLVIDOS:\n{'-' * 40}\n"

            total_carga = 0
            total_recuperado = 0
            total_perdido = 0

            for i, cliente in enumerate(dados_incidente['clientes'], 1):
                valor_carga = float(cliente.get('VALOR_CARGA_BENNER', 0))
                valor_recuperado = float(cliente.get('VALOR_RECUPERADO', 0))
                valor_perdido = float(cliente.get('VALOR_PERDIDO', 0))

                texto += f"\n{i}. {self._formatar_valor(cliente.get('CLIENTE_INCON'))}\n"
                texto += f"   Setor: {self._formatar_valor(cliente.get('SETOR'))}\n"
                texto += f"   Valor Carga: R$ {valor_carga:,.2f}\n"
                texto += f"   Valor Recuperado: R$ {valor_recuperado:,.2f}\n"
                texto += f"   Valor Perdido: R$ {valor_perdido:,.2f}\n"

                total_carga += valor_carga
                total_recuperado += valor_recuperado
                total_perdido += valor_perdido

            texto += f"\nTOTAIS:\n"
            texto += f"• Valor Total Carga: R$ {total_carga:,.2f}\n"
            texto += f"• Valor Total Recuperado: R$ {total_recuperado:,.2f}\n"
            texto += f"• Valor Total Perdido: R$ {total_perdido:,.2f}\n"

        # Adicionar descrição
        texto += f"\n📝 DESCRIÇÃO DO INCIDENTE:\n{'-' * 40}\n"
        texto += self._formatar_valor(dados_incidente.get('DESCRICAO_INCIDENTE')) + "\n"

        texto += f"\n{'=' * 60}\n"
        texto += "Email gerado automaticamente pelo Sistema INCON\n"
        texto += "Para mais informações, acesse o sistema de gestão de incidentes.\n"
        texto += f"{'=' * 60}\n"

        return texto

    def _enviar_email_smtp(self, msg):
        server = None
        try:
            host = self.config.get('smtp_server', 'smtp.dhl.com')
            port = self.config.get('smtp_port', 25)
            login_user = self.config.get('auth_user', 'tiago.moreirap@dhl.com')
            senha = self.config.get('sender_password', 'Security302416*')
            shared_mailbox = self.config.get('sender_email', 'system.incon@dhl.com')
            use_tls = self.config.get('use_tls', True)

            print(f"📡 Conectando a {host}:{port}...")
            server = smtplib.SMTP(host, port, timeout=30)
            server.ehlo()

            if use_tls:
                print("🔒 Iniciando TLS...")
                server.starttls()
                server.ehlo()

            print(f"🔐 Autenticando como: {login_user}")
            server.login(login_user, senha)
            print("✅ Autenticação bem-sucedida")

            todos_destinatarios = []
            if msg.get('To'):
                todos_destinatarios.extend([e.strip() for e in str(msg['To']).split(',') if e.strip()])
            if msg.get('Cc'):
                todos_destinatarios.extend([e.strip() for e in str(msg['Cc']).split(',') if e.strip()])
            todos_destinatarios = list(set(todos_destinatarios))

            # 🔧 AJUSTE CRÍTICO PARA "SEND ON BEHALF"
            # Com a permissão "Send on behalf", precisamos:
            # 1. Usar o usuário autenticado no envelope SMTP (from_addr)
            # 2. Manter a caixa compartilhada no cabeçalho From da mensagem
            # O Exchange/Office 365 se encarrega de mostrar "enviado em nome de"

            print(f"📤 Enviando em nome de: {shared_mailbox}")
            print(f"🔧 Usuário envelope SMTP: {login_user}")
            print(f"👤 Destinatários: {len(todos_destinatarios)} email(s)")

            # DEBUG: Mostrar detalhes do email
            print(f"📧 From no cabeçalho: {msg['From']}")
            print(f"👤 Sender no cabeçalho: {msg['Sender']}")

            # Enviar usando sendmail para controle total
            server.sendmail(
                from_addr=login_user,  # IMPORTANTE: Usar login_user no envelope
                to_addrs=todos_destinatarios,
                msg=msg.as_string()
            )

            print("✅ Email enviado com sucesso!")

            return True

        except Exception as e:
            print(f"❌ Erro no envio: {e}")

            # Tentativa alternativa se o erro persistir
            print("🔄 Tentando abordagem alternativa...")
            try:
                if server:
                    # Alternativa: Usar formato explícito "on behalf of" no cabeçalho
                    original_from = msg['From']
                    auth_user = self.config.get('auth_user', 'tiago.moreirap@dhl.com')
                    msg.replace_header('From', f'{auth_user} on behalf of {original_from}')

                    print(f"🔄 Usando formato alternativo: {msg['From']}")

                    server.sendmail(
                        from_addr=auth_user,
                        to_addrs=todos_destinatarios,
                        msg=msg.as_string()
                    )
                    print("✅ Email enviado com sucesso (formato alternativo)!")
                    return True
            except Exception as e2:
                print(f"❌ Falha também na abordagem alternativa: {e2}")

            return False
        finally:
            if server:
                try:
                    server.quit()
                    print("✅ Conexão encerrada")
                except:
                    try:
                        server.close()
                    except:
                        pass

    def testar_conexao(self):
        """
        Testa a conexão com o servidor SMTP.
        """
        try:
            print(f"🔧 Testando conexão com {self.config['smtp_server']}:{self.config['smtp_port']}...")

            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'], timeout=30)
            server.ehlo()

            if self.config.get('use_tls', True):
                server.starttls()
                server.ehlo()

            if self.config['sender_password']:
                server.login(self.config['auth_user'], self.config['sender_password'])

            server.quit()

            print("✅ Conexão testada com sucesso!")
            return True, "Conexão SMTP testada com sucesso!"

        except Exception as e:
            error_msg = f"Falha na conexão: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def _obter_credenciais_banco(self):
        """
        Obtém as credenciais do banco de dados.
        """
        try:
            # Tente importar do mesmo módulo que o TelaCadastroSinistros
            from Brasil.utils.db_credentials import get_db_credentials
            return get_db_credentials()
        except ImportError:
            # Fallback para configuração local (ajuste conforme seu ambiente)
            return {
                'user': 'user_sinistros',
                'password': 'password',
                'dsn': 'dsn_sinistros'
            }

    def obter_destinatarios(self, tipo_notificacao):
        """
        Obtém os destinatários ativos para um tipo de notificação específico.

        Args:
            tipo_notificacao: 'CADASTRO' ou 'ATUALIZACAO'

        Returns:
            Dicionário com listas de emails para 'TO' e 'CC'
        """
        destinatarios = {'TO': [], 'CC': []}

        try:
            creds = self._obter_credenciais_banco()

            with oracledb.connect(**creds) as connection:
                with connection.cursor() as cursor:
                    # Busca emails ativos para o tipo especificado ou 'AMBOS'
                    query = """
                        SELECT EMAIL, TIPO_DESTINATARIO 
                        FROM DESTINATARIOS_EMAIL_INCIDENTES 
                        WHERE ATIVO = 'S' 
                        AND (TIPO_NOTIFICACAO = :tipo OR TIPO_NOTIFICACAO = 'AMBOS')
                        ORDER BY TIPO_DESTINATARIO, ID
                    """
                    cursor.execute(query, {'tipo': tipo_notificacao})
                    resultados = cursor.fetchall()

                    for email, tipo_dest in resultados:
                        if tipo_dest in ['TO', 'CC']:
                            destinatarios[tipo_dest].append(email)

                    logger.info(
                        f"Encontrados {len(destinatarios['TO'])} TO e {len(destinatarios['CC'])} CC para {tipo_notificacao}")

        except Exception as e:
            logger.error(f"Erro ao buscar destinatários: {e}")
            # Fallback para o destinatário padrão do config
            destinatarios['TO'] = [self.config['default_recipient']]

        return destinatarios

# Funções de teste
def testar_envio_email():
    """Função de teste rápido."""
    print("🧪 Teste rápido do EmailManager")

    manager = EmailManager()

    dados_teste = {
        'N_BENNER': 'TESTE/123456-99',
        'N_SM': 'SM99999',
        'OCORRENCIA': 'OC_TESTE',
        'TIPO_INCIDENTE': 'Teste',
        'DATA_INCIDENTE': datetime.now().strftime('%d-%m-%Y'),
        'HORA_INCIDENTE': '12:00',
        'DESCRICAO_INCIDENTE': 'Email de teste do sistema InCON',
        'data_hora_registro': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'usuario_responsavel': 'tiago.moreirap@dhl.com',
        'clientes': [{
            'CLIENTE_INCON': 'Cliente Teste',
            'VALOR_CARGA_BENNER': 1000.00,
            'VALOR_RECUPERADO': 500.00,
            'VALOR_PERDIDO': 500.00,
            'SETOR': 'Teste'
        }]
    }

    # Para manter o teste funcionando sem mudar a assinatura
    destinatarios_teste = manager.obter_destinatarios('CADASTRO')
    sucesso = manager.enviar_notificacao_incidente(dados_teste, 'TESTE_001', destinatarios_teste)

    if sucesso:
        print("✅✅✅ Teste concluído com SUCESSO! ✅✅✅")
    else:
        print("❌❌❌ Teste FALHOU ❌❌❌")

    return sucesso

def testar_destinatarios():
    """Testa a função de busca de destinatários."""
    print("\n🧪 Testando busca de destinatários...")

    manager = EmailManager()

    # Teste destinatários de CADASTRO
    dest_cadastro = manager.obter_destinatarios('CADASTRO')
    print(f"Destinatários CADASTRO:")
    print(f"  TO: {dest_cadastro['TO']}")
    print(f"  CC: {dest_cadastro['CC']}")

    # Teste destinatários de ATUALIZAÇÃO
    dest_atualizacao = manager.obter_destinatarios('ATUALIZACAO')
    print(f"\nDestinatários ATUALIZACAO:")
    print(f"  TO: {dest_atualizacao['TO']}")
    print(f"  CC: {dest_atualizacao['CC']}")

def testar_envio_simples():
    """Teste mais simples para verificar apenas a configuração de email."""
    print("🧪 Teste SIMPLES do EmailManager")

    manager = EmailManager()

    # Teste de conexão primeiro
    sucesso, mensagem = manager.testar_conexao()
    if not sucesso:
        print(f"❌ Falha na conexão: {mensagem}")
        return False

    # Dados mínimos para teste
    dados_teste = {
        'N_BENNER': 'TESTE/123456-99',
        'DESCRICAO_INCIDENTE': 'Teste de envio com permissão Send on Behalf',
        'data_hora_registro': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'usuario_responsavel': 'tiago.moreirap@dhl.com'
    }

    # Destinatário de teste (apenas para você)
    destinatarios_teste = {
        'TO': ['tiago.moreirap@dhl.com'],
        'CC': []
    }

    print(f"📧 Testando envio de: {manager.config['sender_email']}")
    print(f"🔐 Autenticando como: {manager.config['auth_user']}")
    print(f"👤 Enviando para: {destinatarios_teste['TO']}")

    sucesso = manager.enviar_notificacao_incidente(
        dados_teste,
        'TESTE_SENDBEHALF',
        destinatarios_teste
    )

    if sucesso:
        print("✅✅✅ Teste concluído! Verifique sua caixa de entrada. ✅✅✅")
    else:
        print("❌❌❌ Teste FALHOU ❌❌❌")

    return sucesso

# Configuração JSON recomendada (up_email_config_dhl.json)
"""
{
    "smtp_server": "smtp.dhl.com",
    "smtp_port": 25,
    "sender_email": "system.incon@dhl.com",
    "auth_user": "tiago.moreirap@dhl.com",
    "sender_password": "Security302416*",
    "default_recipient": "tiago.moreirap@dhl.com",
    "use_tls": true,
    "use_ssl": false
}
"""

if __name__ == "__main__":
    # Primeiro testa os destinatários
    testar_destinatarios()

    # Opções de teste
    print("\n🔧 Opções de teste:")
    print("1. Teste de conexão")
    print("2. Teste simples de envio")
    print("3. Teste completo de envio")

    opcao = input("\nEscolha uma opção (1-3) ou pressione Enter para sair: ")

    if opcao == "1":
        manager = EmailManager()
        sucesso, mensagem = manager.testar_conexao()
    elif opcao == "2":
        testar_envio_simples()
    elif opcao == "3":
        testar_envio_email()
    else:
        print("Encerrando...")