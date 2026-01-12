import sys
import os
import webbrowser
import traceback
import shutil
from PyQt5.QtWidgets import QWidget, QMessageBox

# Ajuste de path para encontrar os arquivos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from file_selector import FileSelector
from data_parsers import ExcelParser
from map_builder import MapBuilder
from color_picker_ui import ColorPickerUI


class GeradorMapaTela(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Gerador de Mapas")

    def download_template(self):
        """
        Gerencia o download do arquivo de modelo Excel e
        retorna True se o processo deve ser encerrado.
        """
        # Caminho absoluto do template baseado na estrutura fornecida
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mapa.xlsx")

        if not os.path.exists(template_path):
            QMessageBox.warning(self, "Erro", f"Arquivo de modelo não encontrado em:\n{template_path}")
            return False

        # Abre seletor para o usuário escolher onde salvar
        dest_path = FileSelector.save_file_dest("modelo_mapa_operacional.xlsx")

        if dest_path:
            try:
                shutil.copy2(template_path, dest_path)
                QMessageBox.information(self, "Download Concluído",
                                        "O modelo foi salvo com sucesso.\nO programa será encerrado.")
                return True  # Indica que o download foi feito e deve encerrar
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao copiar modelo: {e}")

        return True  # Encerra mesmo se cancelar o 'Salvar Como', conforme sua solicitação

    def show(self):
        print("=" * 45)
        print("   SISTEMA DE MAPEAMENTO OPERACIONAL DINÂMICO")
        print("=" * 45 + "\n")

        # 0. PERGUNTA INICIAL: DOWNLOAD OU GERAR MAPA
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Início - Gerador de Mapas")
        msg_box.setText("Como deseja prosseguir?")
        btn_download = msg_box.addButton("Baixar Template", QMessageBox.ActionRole)
        btn_gerar = msg_box.addButton("Gerar Mapa", QMessageBox.AcceptRole)
        btn_cancelar = msg_box.addButton("Cancelar", QMessageBox.RejectRole)

        msg_box.exec_()

        if msg_box.clickedButton() == btn_download:
            self.download_template()
            return  # ENCERRA O PROCESSO AQUI

        elif msg_box.clickedButton() == btn_cancelar:
            return

        # 1. SELEÇÃO DO ARQUIVO (Continua apenas se escolheu 'Gerar Mapa')
        print("1. Selecionando arquivo de dados...")
        excel_path = FileSelector.select_excel()

        if not excel_path or not os.path.exists(excel_path):
            return

        try:
            # Lógica do Parser
            excel_parser = ExcelParser(excel_path)
            df_grouped = excel_parser.parse()
            tipos_encontrados = excel_parser.get_unique_types()
            eventos_unicos = excel_parser.get_unique_events()

            print(f"   ✓ Arquivo carregado: {os.path.basename(excel_path)}")

            # 2. DEFINIÇÃO DE CORES
            print("\n2. Configurando paleta de cores...")
            ui_cores = ColorPickerUI(tipos_encontrados)
            mapeamento_cores = ui_cores.get_colors()

            if not mapeamento_cores:
                return

            # 3. CONSTRUÇÃO DO MAPA
            print("\n3. Gerando inteligência geográfica...")
            center = excel_parser.get_center_location()
            map_builder = MapBuilder(center)
            map_builder.add_vehicle_data(df_grouped, mapeamento_cores)
            map_builder.add_filter_system(eventos_unicos, tipos_encontrados)
            mapa_final = map_builder.finalize()

            # 4. SALVAMENTO
            print("\n4. Finalizando exportação...")
            nome_sugerido = f"Mapa_{os.path.splitext(os.path.basename(excel_path))[0]}.html"
            output_path = FileSelector.save_file_dest(nome_sugerido)

            if output_path:
                mapa_final.save(output_path)
                print(f"✅ SUCESSO! Mapa salvo em: {output_path}")
                webbrowser.open('file://' + os.path.realpath(output_path))

        except Exception as e:
            error_msg = f"Erro crítico: {e}"
            print(error_msg)
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", error_msg)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    tela = GeradorMapaTela()
    tela.show()
    sys.exit(app.exec_())