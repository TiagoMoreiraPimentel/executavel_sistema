"""
Construtor principal do mapa - Versão com Cores Dinâmicas e Correção de Erros.
"""
import folium
from typing import List, Dict, Optional
from map_components import MapMarkerFactory, MapControls
from filter_manager import FilterManager
from annotation_system import AnnotationSystem
from ui_helpers import (
    html_escape,
    get_vehicle_color,
    get_vehicle_marker_color
)

class MapBuilder:
    def __init__(self, center_location: List[float], zoom_start: int = 12):
        self.mapa = folium.Map(location=center_location, zoom_start=zoom_start)
        self.marker_coords = []
        self.marker_colors = []
        self.total_markers = 0
        self.map_name = self.mapa.get_name()

        self.category_groups = {}
        self.mapeamento_cores = {}

        # Componentes
        self.map_controls = MapControls()
        self.filter_manager = FilterManager()
        self.annotation_system = AnnotationSystem(self.map_name)

        # Adicionar controles básicos
        self.map_controls.add_measure_control(self.mapa)

    def add_vehicle_data(self, df_grouped, mapeamento_cores: dict) -> None:
        """Adiciona os dados ao mapa usando as cores definidas pela UI."""
        self.mapeamento_cores = mapeamento_cores
        max_points = 0

        for tipo_nome, group in df_grouped.groupby('Tipo'):
            if tipo_nome not in self.category_groups:
                # Busca a cor definida na interface
                base_color = get_vehicle_color(tipo_nome, self.mapeamento_cores)

                self.category_groups[tipo_nome] = {
                    'group': folium.FeatureGroup(name=f'Categoria: {tipo_nome}'),
                    'color': base_color,
                    'coords': []
                }

            group_sorted = group.sort_values('Data_Inicial')

            for i, (_, row) in enumerate(group_sorted.iterrows()):
                lat, lon = row['Latitude'], row['Longitude']

                # Gera o degradê baseado na cor escolhida
                icon_color = get_vehicle_marker_color(tipo_nome, i, len(group_sorted), self.mapeamento_cores)

                marker = MapMarkerFactory.create_vehicle_marker(row, i, icon_color, tipo_nome)
                self.category_groups[tipo_nome]['group'].add_child(marker)
                self.category_groups[tipo_nome]['coords'].append([lat, lon])

                self.marker_coords.append([lat, lon])
                self.marker_colors.append(icon_color)

            if len(group_sorted) > max_points:
                max_points = len(group_sorted)

        self.total_markers = max_points

    def add_filter_system(self, eventos_unicos: List[str],
                         categorias_unicas: List[str]) -> None:
        """Adiciona sistema de filtros injetando as cores iniciais da interface."""
        # 1. HTML do Filtro
        filter_html = self.filter_manager.build_filter_html(
            eventos_unicos,
            categorias_unicas,
            "",
            self.total_markers,
            self.mapeamento_cores
        )
        self.mapa.get_root().html.add_child(folium.Element(filter_html))

        # 2. JS do Filtro (ADICIONAR ESTA LINHA)
        filter_js = self.filter_manager.build_filter_js(self.map_name, [], self.total_markers)
        self.mapa.get_root().html.add_child(folium.Element(filter_js))

    def finalize(self) -> folium.Map:
        """Desenha trajetos e finaliza as camadas."""
        for tipo_nome, data in self.category_groups.items():
            coords = data['coords']

            if len(coords) > 1:
                # Criamos a linha do trajeto (2px conforme solicitado)
                line = folium.PolyLine(
                    locations=coords,
                    color=data['color'],
                    weight=2,
                    opacity=0.8,
                    tooltip=f"Trajeto: {tipo_nome}"
                )

                # Metadados para o seletor de cores JS no navegador
                line.options['isTrajeto'] = True
                line.options['vehicleType'] = tipo_nome.lower()
                line.add_to(data['group'])

            data['group'].add_to(self.mapa)

        # CORREÇÃO DO ERRO:
        # Injetar o JavaScript de anotações diretamente
        annotation_js = self.annotation_system.get_annotation_js()
        self.mapa.get_root().html.add_child(folium.Element(annotation_js))

        # Adicionar controle de camadas
        self.map_controls.add_layer_control(self.mapa, collapsed=False)
        return self.mapa