"""
Módulo para gerenciamento de emails de incidentes.
Autor: Sistema InCON
Versão: 1.1 - Adicionado suporte a emails de atualização
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
    Configurado para servidor SMTP da DHL.
    """

    def __init__(self, config_path=None):
        """
        Inicializa o gerenciador de emails.
        """
        if config_path is None:
            # ⚠️ NOVO: Caminhos relativos à raiz do projeto SINISTROS
            dhl_config_rel_path = os.path.join('Brasil', 'telas', 'registrar_incidentes', 'email_config_dhl.json')

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

    def _load_config(self, config_path):
        if config_path is None:
            return {
                "smtp_server": "smtp.dhl.com",
                "smtp_port": 25,
                "sender_email": "tiago.moreirap@dhl.com",
                "sender_password": "Security302416*",
                "default_recipient": "tiago.moreirap@dhl.com"
            }
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return {
                "smtp_server": "smtp.dhl.com",
                "smtp_port": 25,
                "sender_email": "tiago.moreirap@dhl.com",
                "sender_password": "Security302416*",
                "default_recipient": "tiago.moreirap@dhl.com"
            }

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
                print(f"✅ Email enviado com sucesso!")  # Mensagem genérica
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

        # Corpo do email em texto simples
        corpo_texto = self._gerar_corpo_email_texto(dados_incidente, logics_pai)

        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto
        msg['From'] = self.config['sender_email']

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

        # Corpo do email em texto simples
        corpo_texto = self._gerar_corpo_email_atualizacao(dados_incidente, logics_pai)

        # Criar mensagem
        msg = MIMEMultipart('alternative')
        msg['Subject'] = assunto
        msg['From'] = self.config['sender_email']

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

        return msg

    def _gerar_corpo_email_texto(self, dados_incidente, logics_pai):
        """
        Gera o corpo do email em formato texto simples.
        """
        data_hora_registro = dados_incidente.get('data_hora_registro',
                                                 datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

        # Função auxiliar para tratar valores nulos
        def formatar_valor(valor):
            if valor in [None, "", "N/A", "Selecione uma informação", "NÃO INFORMADO"]:
                return "NÃO INFORMADO"
            return valor

        texto = f"""
{'=' * 60}
COMUNICADO DE INCIDENTE - SISTEMA INCON
{'=' * 60}

⚠️  INCIDENTE REGISTRADO NO SISTEMA

IDENTIFICAÇÃO:
{'-' * 40}
Incidente LOGICS: {logics_pai}
Data/Hora do Registro: {data_hora_registro}
Usuário Responsável: {dados_incidente.get('usuario_responsavel', 'NÃO INFORMADO')}

📋 INFORMAÇÕES DO INCIDENTE:
{'-' * 40}
• Nº Viagem BENNER: {formatar_valor(dados_incidente.get('N_BENNER'))}
• Nº SM: {formatar_valor(dados_incidente.get('N_SM'))}
• Nº Ocorrência: {formatar_valor(dados_incidente.get('OCORRENCIA'))}
• Tipo de Incidente: {formatar_valor(dados_incidente.get('TIPO_INCIDENTE'))}
• Data do Incidente: {formatar_valor(dados_incidente.get('DATA_INCIDENTE'))}
• Hora do Incidente: {formatar_valor(dados_incidente.get('HORA_INCIDENTE'))}
• Período do Dia: {formatar_valor(dados_incidente.get('PERIODO_INCIDENTE'))}

📍 LOCALIZAÇÃO:
{'-' * 40}
• Região: {formatar_valor(dados_incidente.get('REGIAO_INCIDENTE'))}
• Estado: {formatar_valor(dados_incidente.get('ESTADO_INCIDENTE'))}
• Cidade: {formatar_valor(dados_incidente.get('CIDADE_INCIDENTE'))}
• Local (Rua/Rodovia): {formatar_valor(dados_incidente.get('END_INCIDENTE'))}
• Estrada/Urbana: {formatar_valor(dados_incidente.get('ESTRADA_URBANA'))}
• Coordenadas: Lat {formatar_valor(dados_incidente.get('LATITUDE'))}, Long {formatar_valor(dados_incidente.get('LONGITUDE'))}

🚚 DADOS DE TRANSPORTE:
{'-' * 40}
• Transportador: {formatar_valor(dados_incidente.get('TRANSPORTADOR_INCIDENTES'))}
• Fase Transporte: {formatar_valor(dados_incidente.get('TRANSPORTE'))}
• Placa Cavalo: {formatar_valor(dados_incidente.get('PLACA_CAVALO'))}
• Placa Baú: {formatar_valor(dados_incidente.get('PLACA_BAU'))}
• CPF Motorista: {formatar_valor(dados_incidente.get('CPF_MOTORISTA'))}
• Rastreado Por: {formatar_valor(dados_incidente.get('RASTREADO_POR'))}
• Tracking Cell: {formatar_valor(dados_incidente.get('TRACKING_CELL'))}

⚠️  DETALHES OPERACIONAIS:
{'-' * 40}
• Falha RM: {formatar_valor(dados_incidente.get('FALHA_RM'))}
• Local Caminhão: {formatar_valor(dados_incidente.get('END_CAMINHAO'))}
• Local Carga: {formatar_valor(dados_incidente.get('END_CARGA'))}
• Origem: {formatar_valor(dados_incidente.get('ORIGEM'))}
• Destino: {formatar_valor(dados_incidente.get('DESTINO'))}
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

                texto += f"\n{i}. {cliente.get('CLIENTE_INCON', 'NÃO INFORMADO')}\n"
                texto += f"   Setor: {cliente.get('SETOR', 'NÃO INFORMADO')}\n"
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
        descricao = formatar_valor(dados_incidente.get('DESCRICAO_INCIDENTE'))
        texto += descricao + "\n"

        texto += f"\n{'=' * 60}\n"
        texto += "Email gerado automaticamente pelo Sistema INCON\n"
        texto += "Para mais informações, acesse o sistema de gestão de incidentes.\n"
        texto += f"{'=' * 60}\n"

        return texto

    def _gerar_corpo_email_atualizacao(self, dados_incidente, logics_pai):
        """
        Gera o corpo do email de ATUALIZAÇÃO em formato texto simples.
        """
        data_hora_registro = dados_incidente.get('data_hora_registro',
                                                 datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

        # Função auxiliar para tratar valores nulos
        def formatar_valor(valor):
            if valor in [None, "", "N/A", "Selecione uma informação", "NÃO INFORMADO"]:
                return "NÃO INFORMADO"
            return valor

        texto = f"""
{'=' * 60}
ATUALIZAÇÃO DE INCIDENTE - SISTEMA INCON
{'=' * 60}

⚠️  INCIDENTE ATUALIZADO NO SISTEMA

IDENTIFICAÇÃO:
{'-' * 40}
Incidente LOGICS: {logics_pai}
Data/Hora da Atualização: {data_hora_registro}
Usuário Responsável: {dados_incidente.get('usuario_responsavel', 'NÃO INFORMADO')}

📋 INFORMAÇÕES DO INCIDENTE:
{'-' * 40}
• Nº Viagem BENNER: {formatar_valor(dados_incidente.get('N_BENNER'))}
• Nº SM: {formatar_valor(dados_incidente.get('N_SM'))}
• Nº Ocorrência: {formatar_valor(dados_incidente.get('OCORRENCIA'))}
• Tipo de Incidente: {formatar_valor(dados_incidente.get('TIPO_INCIDENTE'))}
• Data do Incidente: {formatar_valor(dados_incidente.get('DATA_INCIDENTE'))}
• Hora do Incidente: {formatar_valor(dados_incidente.get('HORA_INCIDENTE'))}
• Período do Dia: {formatar_valor(dados_incidente.get('PERIODO_INCIDENTE'))}

📍 LOCALIZAÇÃO:
{'-' * 40}
• Região: {formatar_valor(dados_incidente.get('REGIAO_INCIDENTE'))}
• Estado: {formatar_valor(dados_incidente.get('ESTADO_INCIDENTE'))}
• Cidade: {formatar_valor(dados_incidente.get('CIDADE_INCIDENTE'))}
• Local (Rua/Rodovia): {formatar_valor(dados_incidente.get('END_INCIDENTE'))}
• Estrada/Urbana: {formatar_valor(dados_incidente.get('ESTRADA_URBANA'))}
• Coordenadas: Lat {formatar_valor(dados_incidente.get('LATITUDE'))}, Long {formatar_valor(dados_incidente.get('LONGITUDE'))}

🚚 DADOS DE TRANSPORTE:
{'-' * 40}
• Transportador: {formatar_valor(dados_incidente.get('TRANSPORTADOR_INCIDENTES'))}
• Fase Transporte: {formatar_valor(dados_incidente.get('TRANSPORTE'))}
• Placa Cavalo: {formatar_valor(dados_incidente.get('PLACA_CAVALO'))}
• Placa Baú: {formatar_valor(dados_incidente.get('PLACA_BAU'))}
• CPF Motorista: {formatar_valor(dados_incidente.get('CPF_MOTORISTA'))}
• Rastreado Por: {formatar_valor(dados_incidente.get('RASTREADO_POR'))}
• Tracking Cell: {formatar_valor(dados_incidente.get('TRACKING_CELL'))}

⚠️  DETALHES OPERACIONAIS:
{'-' * 40}
• Falha RM: {formatar_valor(dados_incidente.get('FALHA_RM'))}
• Local Caminhão: {formatar_valor(dados_incidente.get('END_CAMINHAO'))}
• Local Carga: {formatar_valor(dados_incidente.get('END_CARGA'))}
• Origem: {formatar_valor(dados_incidente.get('ORIGEM'))}
• Destino: {formatar_valor(dados_incidente.get('DESTINO'))}
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

                texto += f"\n{i}. {cliente.get('CLIENTE_INCON', 'NÃO INFORMADO')}\n"
                texto += f"   Setor: {cliente.get('SETOR', 'NÃO INFORMADO')}\n"
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
        descricao = formatar_valor(dados_incidente.get('DESCRICAO_INCIDENTE'))
        texto += descricao + "\n"

        texto += f"\n{'=' * 60}\n"
        texto += "Email gerado automaticamente pelo Sistema INCON\n"
        texto += "Para mais informações, acesse o sistema de gestão de incidentes.\n"
        texto += f"{'=' * 60}\n"

        return texto

    def _enviar_email_smtp(self, msg):
        try:
            server = None
            print(f"📡 Conectando a {self.config['smtp_server']}:{self.config['smtp_port']}")
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'], timeout=30)
            server.ehlo()

            if self.config['smtp_port'] == 587:
                server.starttls()
                server.ehlo()

            if self.config['sender_password']:
                print(f"🔐 Autenticando como {self.config['sender_email']}...")
                server.login(self.config['sender_email'], self.config['sender_password'])
                print("✅ Autenticação bem-sucedida")

            todos_destinatarios = []
            if msg['To']:
                todos_destinatarios.extend([email.strip() for email in msg['To'].split(',')])
            if msg.get('Cc'):
                todos_destinatarios.extend([email.strip() for email in msg['Cc'].split(',')])

            todos_destinatarios = list(set(todos_destinatarios))
            server.send_message(msg, to_addrs=todos_destinatarios)
            print("✅ Email enviado")

            try:
                server.quit()
            except:
                server.close()
            return True

        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return False
        finally:
            if server:
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

            if self.config['smtp_port'] == 587:
                server.starttls()
                server.ehlo()

            if self.config['sender_password']:
                server.login(self.config['sender_email'], self.config['sender_password'])

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

# Função de conveniência
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
        'usuario_responsavel': 'TESTE',
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

# Adicione esta função antes do if __name__ == "__main__":
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

# Modifique o if __name__ == "__main__" para:
if __name__ == "__main__":
    # Primeiro testa os destinatários
    testar_destinatarios()

    # Depois testa o envio (opcional)
    resposta = input("\nDeseja testar o envio de email? (s/n): ")
    if resposta.lower() == 's':
        testar_envio_email()