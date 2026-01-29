"""
map_components.py

Componentes do mapa: marcadores, popups, controles.
"""
import folium
from folium.features import DivIcon
from folium.plugins import MeasureControl
from typing import Dict
from ui_helpers import html_escape

class MapMarkerFactory:
    @staticmethod
    def create_vehicle_marker(row: Dict, idx: int, icon_color: str, vehicle_name: str) -> folium.Marker:
        data_hora_list = row['Data/Hora'] if isinstance(row['Data/Hora'], list) else [row['Data/Hora']]
        data_hora_obj = data_hora_list[0]
        hora_res = data_hora_obj.strftime('%H:%M')
        data_res = data_hora_obj.strftime('%d/%m %H:%M')

        nome_raw = str(row.get('NOME_PESSOA', '')).strip()
        tem_nome = nome_raw and nome_raw.lower() not in ['nan', 'n/i', 'none', 'null', '']
        nome_pessoa = nome_raw if tem_nome else "N/I"

        marker_html = f'''
            <div class="marker-circle" 
                 data-idx="{idx + 1}" 
                 data-eventos="{html_escape(','.join(set(map(str, row['Evento']))).lower())}"
                 data-ignicao="{str(row['Ignição']).lower()}"
                 data-veiculo="{vehicle_name.lower()}"
                 data-originalcolor="{icon_color}"
                 data-hasname="{"true" if tem_nome else "false"}"
                 style="background-color: {icon_color} !important; display: flex; justify-content: center; align-items: center; 
                        color: white; font-weight: bold; font-size: 10px; border: 2px solid white; 
                        box-shadow: 0 0 4px rgba(0,0,0,0.6); white-space: nowrap; width: 22px; height: 22px; border-radius: 50%;">
                <span class="m-num">{idx + 1}</span>
                <span class="m-hora" style="display:none;">{hora_res}</span>
                <span class="m-data-hora" style="display:none;">{data_res}</span>
                <span class="m-nome" style="display:none;">{html_escape(nome_pessoa)}</span>
            </div>
        '''
        return folium.map.Marker(
            location=[row['Latitude'], row['Longitude']],
            icon=DivIcon(icon_size=(250, 22), icon_anchor=(11, 11), html=marker_html),
            popup=folium.Popup(f"Ponto #{idx+1} - {nome_pessoa}", max_width=300)
        )

class MapControls:
    @staticmethod
    def add_measure_control(mapa: folium.Map): MeasureControl(position='topright').add_to(mapa)
    @staticmethod
    def add_layer_control(mapa: folium.Map, collapsed: bool = False): folium.LayerControl(collapsed=collapsed).add_to(mapa)