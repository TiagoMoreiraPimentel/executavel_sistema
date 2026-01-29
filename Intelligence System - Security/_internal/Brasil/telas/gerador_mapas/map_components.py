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
        # Formato para o marcador (ex: 25/12 14:30)
        data_hora_marcador = data_hora_obj.strftime('%d/%m %H:%M')
        # Formato completo para o Popup
        data_hora_popup = data_hora_obj.strftime('%d/%m/%Y %H:%M:%S')

        nome_raw = str(row.get('NOME_PESSOA', '')).strip()
        tem_nome = nome_raw and nome_raw.lower() not in ['nan', 'n/i', 'none', 'null', '']
        nome_pessoa = nome_raw if tem_nome else "Não Informado"

        # Eventos
        eventos = row.get('Evento', [])
        eventos_html = "".join(
            [f"<li>{html_escape(str(e))}</li>" for e in (eventos if isinstance(eventos, list) else [eventos])])

        # HTML do Popup (Organizado em Tabela)
        popup_html = f'''
            <div style="font-family: sans-serif; width: 260px; font-size: 12px;">
                <div style="background-color: {icon_color}; color: white; padding: 5px; border-radius: 4px 4px 0 0; font-weight: bold; text-align: center; margin-bottom: 8px;">
                    PONTO #{idx + 1} - {html_escape(vehicle_name)}
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 3px; border-bottom: 1px solid #eee;"><b>Responsável:</b></td><td style="padding: 3px; border-bottom: 1px solid #eee;">{html_escape(nome_pessoa)}</td></tr>
                    <tr><td style="padding: 3px; border-bottom: 1px solid #eee;"><b>Data/Hora:</b></td><td style="padding: 3px; border-bottom: 1px solid #eee;">{data_hora_popup}</td></tr>
                    <tr><td style="padding: 3px; border-bottom: 1px solid #eee;"><b>Ignição:</b></td><td style="padding: 3px; border-bottom: 1px solid #eee;">{html_escape(str(row['Ignição']))}</td></tr>
                    <tr><td style="padding: 3px; border-bottom: 1px solid #eee;"><b>Coordenadas:</b></td><td style="padding: 3px; border-bottom: 1px solid #eee;">{row['Latitude']:.5f}, {row['Longitude']:.5f}</td></tr>
                </table>
                <div style="margin-top: 8px; border-top: 1px solid #ccc; padding-top: 5px;">
                    <b style="color: #444;">Lista de Eventos:</b>
                    <ul style="margin: 5px 0; padding-left: 20px; color: #555; font-size: 11px;">
                        {eventos_html}
                    </ul>
                </div>
            </div>
        '''

        marker_html = f'''
            <div class="marker-circle" 
                 data-idx="{idx + 1}" 
                 data-eventos="{html_escape(','.join(set(map(str, eventos if isinstance(eventos, list) else [eventos]))).lower())}"
                 data-veiculo="{vehicle_name.lower()}"
                 data-originalcolor="{icon_color}"
                 data-hasname="{"true" if tem_nome else "false"}"
                 style="background-color: {icon_color} !important; display: flex; justify-content: center; align-items: center; 
                        color: white; font-weight: bold; font-size: 10px; border: 2px solid white; 
                        box-shadow: 0 0 4px rgba(0,0,0,0.6); white-space: nowrap; width: 22px; height: 22px; border-radius: 50%; transition: all 0.2s;">
                <span class="m-num">{idx + 1}</span>
                <span class="m-hora" style="display:none;">{hora_res}</span>
                <span class="m-data-hora" style="display:none;">{data_hora_marcador}</span>
                <span class="m-nome" style="display:none;">{html_escape(nome_pessoa)}</span>
            </div>
        '''

        return folium.map.Marker(
            location=[row['Latitude'], row['Longitude']],
            icon=DivIcon(icon_size=(250, 22), icon_anchor=(11, 11), html=marker_html),
            popup=folium.Popup(popup_html, max_width=300)
        )

class MapControls:
    @staticmethod
    def add_measure_control(mapa: folium.Map): MeasureControl(position='topright').add_to(mapa)
    @staticmethod
    def add_layer_control(mapa: folium.Map, collapsed: bool = False): folium.LayerControl(collapsed=collapsed).add_to(mapa)