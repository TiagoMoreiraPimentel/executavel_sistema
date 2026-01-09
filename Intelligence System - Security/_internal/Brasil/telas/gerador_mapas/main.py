import sys
import os
import webbrowser
import traceback
from PyQt5.QtWidgets import QWidget, QMessageBox # Importa componentes do seu sistema

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
        # Deixamos a janela invisível pois usaremos os popups e seletores que você já criou
        self.setWindowTitle("Gerador de Mapas")

    def show(self):
        """
        Sobrescreve o show() para executar o seu fluxo de mapeamento
        mantendo o formato que você utiliza no sistema principal.
        """
        print("=" * 45)
        print("   SISTEMA DE MAPEAMENTO OPERACIONAL DINÂMICO")
        print("=" * 45 + "\n")

        # 1. SELEÇÃO DO ARQUIVO
        print("1. Selecionando arquivo de dados...")
        excel_path = FileSelector.select_excel()

        if not excel_path or not os.path.exists(excel_path):
            QMessageBox.warning(self, "Cancelado", "Nenhum arquivo Excel selecionado.")
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
                print("   ✗ Operação cancelada: Cores não definidas.")
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
            else:
                QMessageBox.information(self, "Aviso", "O mapa não foi salvo.")

        except Exception as e:
            error_msg = f"Erro crítico: {e}"
            print(error_msg)
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", error_msg)

# Mantém compatibilidade caso queira rodar o arquivo sozinho
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    tela = GeradorMapaTela()
    tela.show()
    sys.exit(app.exec_())