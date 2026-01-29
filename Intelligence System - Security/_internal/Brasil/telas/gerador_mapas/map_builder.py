"""
map_builder.py

Construtor principal do mapa - Versão com Cores Dinâmicas e Correção de Erros.
"""
import folium
from typing import List, Dict
from map_components import MapMarkerFactory, MapControls
from filter_manager import FilterManager
from annotation_system import AnnotationSystem
from ui_helpers import get_vehicle_color, get_vehicle_marker_color


class MapBuilder:
    def __init__(self, center_location: List[float], zoom_start: int = 12):
        self.mapa = folium.Map(location=center_location, zoom_start=zoom_start)
        self.total_markers = 0
        self.map_name = self.mapa.get_name()
        self.category_groups = {}
        self.mapeamento_cores = {}
        self.map_controls = MapControls()
        self.filter_manager = FilterManager()
        self.annotation_system = AnnotationSystem(self.map_name)
        self.map_controls.add_measure_control(self.mapa)

    def add_vehicle_data(self, df_grouped, mapeamento_cores: dict) -> None:
        """Adiciona os dados ao mapa usando as cores definidas pela UI."""
        self.mapeamento_cores = mapeamento_cores
        max_p = 0

        # Agrupamos por tipo para criar as camadas
        for tipo, group in df_grouped.groupby('Tipo'):
            group_sorted = group.sort_values('Data_Inicial')

            if tipo not in self.category_groups:
                # CORREÇÃO AQUI: Chaves simples para o dicionário
                self.category_groups[tipo] = {
                    'group': folium.FeatureGroup(name=f'Categoria: {tipo}'),
                    'color': get_vehicle_color(tipo, self.mapeamento_cores),
                    'df': group_sorted
                }

            # Adiciona os marcadores
            for i, (_, row) in enumerate(group_sorted.iterrows()):
                icon_c = get_vehicle_marker_color(tipo, i, len(group_sorted), self.mapeamento_cores)
                marker = MapMarkerFactory.create_vehicle_marker(row, i, icon_c, tipo)
                self.category_groups[tipo]['group'].add_child(marker)

            max_p = max(max_p, len(group_sorted))

        self.total_markers = max_p

    def add_filter_system(self, evs: List[str], cats: List[str]) -> None:
        html = self.filter_manager.build_filter_html(evs, cats, "", self.total_markers, self.mapeamento_cores)
        self.mapa.get_root().html.add_child(folium.Element(html))
        js = self.filter_manager.build_filter_js(self.map_name, [], self.total_markers)
        self.mapa.get_root().html.add_child(folium.Element(js))

    def finalize(self) -> folium.Map:
        """Desenha trajetos segmento por segmento com lógica de NOME_PESSOA."""
        for tipo, data in self.category_groups.items():
            df = data['df']

            # Desenha linha apenas se houver mais de um ponto
            if len(df) > 1:
                for i in range(len(df) - 1):
                    p1, p2 = df.iloc[i], df.iloc[i + 1]

                    # Verifica se deve esconder a linha (se houver nome em p1 ou p2)
                    n1 = str(p1.get('NOME_PESSOA', '')).lower().strip()
                    n2 = str(p2.get('NOME_PESSOA', '')).lower().strip()

                    # Define o que é um nome "inválido"
                    invalidos = ['', 'nan', 'n/i', 'none', 'null']
                    tem_n = (n1 not in invalidos) or (n2 not in invalidos)

                    line = folium.PolyLine(
                        locations=[(p1['Latitude'], p1['Longitude']), (p2['Latitude'], p2['Longitude'])],
                        color=data['color'],
                        weight=2,
                        opacity=0.0 if tem_n else 0.8,
                        tooltip=f"Trajeto: {tipo}"
                    )

                    # Metadados para o JS
                    line.options['isTrajeto'] = True
                    line.options['vehicleType'] = tipo.lower()
                    line.options['hasName'] = tem_n

                    line.add_to(data['group'])

            data['group'].add_to(self.mapa)

        # Injetar scripts finais
        self.mapa.get_root().html.add_child(folium.Element(self.annotation_system.get_annotation_js()))
        self.map_controls.add_layer_control(self.mapa)
        return self.mapa