"""
Componentes do mapa: marcadores, popups, controles.
"""
import folium
from folium.features import DivIcon
from folium.plugins import MeasureControl
from typing import Dict, List, Tuple, Optional
from ui_helpers import html_escape, is_nonempty_desc


class MapMarkerFactory:
    """Fábrica de marcadores para o mapa."""

    @staticmethod
    def create_vehicle_marker(row: Dict, idx: int, icon_color: str, vehicle_name: str) -> folium.Marker:
        """
        Cria marcador compacto que alterna entre Número e Hora (HH:MM).
        """
        # Extrair apenas HH:MM do primeiro horário do grupo
        data_hora = row['Data/Hora'][0] if isinstance(row['Data/Hora'], list) else row['Data/Hora']
        hora_resumida = data_hora.strftime('%H:%M')

        lat, lon = row['Latitude'], row['Longitude']
        eventos = row['Evento']
        horas = row['Data/Hora']
        ignicao = str(row['Ignição']).upper()
        descricoes = row['Observações']

        # Processar histórico e observações para o Popup
        desc_itens = []
        for h, d in zip(horas, descricoes):
            if is_nonempty_desc(d):
                linha = f"{h.strftime('%d/%m/%Y %H:%M:%S')} — {html_escape(str(d))}"
                desc_itens.append(linha)

        descricao_section = ""
        if desc_itens:
            descricao_html = "".join(f"<li style='margin-bottom:2px;'>{item}</li>" for item in desc_itens)
            descricao_section = f"<div style='margin-top:8px;'><b>Obs:</b><ul style='padding-left:15px; margin:5px 0;'>{descricao_html}</ul></div><hr style='margin:5px 0;'>"

        popup_content = f"""
        <div style="font-family: Arial; font-size: 12px; width: 280px;">
            <h4 style="margin:0; color: {icon_color}">Ponto #{idx + 1}</h4>
            <hr style="margin: 5px 0;">
            <b>Veículo:</b> {html_escape(vehicle_name)} | <b>Ignição:</b> {ignicao}<br>
            <b>Lat/Lon:</b> {lat:.6f}, {lon:.6f}
            <hr style="margin: 5px 0;">
            {descricao_section}
            <div style="max-height: 120px; overflow-y: auto;">
                <b>Eventos:</b>
                <ul style="padding-left: 15px; margin: 5px 0;">
                    {"".join(f"<li>{h.strftime('%H:%M:%S')}: {e}</li>" for h, e in zip(horas, eventos))}
                </ul>
            </div>
        </div>
        """

        # Dados para filtros
        evento_lista_str = ','.join(set(map(str, eventos))).replace("'", "").replace('"', "")

        # HTML do Marcador - Agora com as duas opções de texto dentro
        # Note que a largura e o border-radius agora são controlados pelo JS via classe
        marker_html = f'''
            <div class="marker-circle" 
                 id="marker-{idx + 1}"
                 data-idx="{idx + 1}" 
                 data-eventos="{evento_lista_str.lower()}"
                 data-ignicao="{ignicao.lower()}"
                 data-veiculo="{vehicle_name.lower()}"
                 data-originalcolor="{icon_color}"
                 style="
                    background-color: {icon_color} !important;
                    display: flex !important;
                    justify-content: center !important;
                    align-items: center !important;
                    color: white !important;
                    font-weight: bold !important;
                    font-size: 10px !important;
                    border: 2px solid white !important;
                    box-shadow: 0 0 4px rgba(0,0,0,0.6) !important;
                    white-space: nowrap !important;
                    transition: all 0.2s ease;
                    width: 22px; height: 22px; border-radius: 50%;
                 ">
                <span class="m-num">{idx + 1}</span>
                <span class="m-hora" style="display:none;">{hora_resumida}</span>
            </div>
        '''

        marker = folium.map.Marker(
            location=[lat, lon],
            icon=DivIcon(
                icon_size=(35, 22), # Aumentado para acomodar a versão "Hora"
                icon_anchor=(11, 11),
                html=marker_html
            ),
            popup=folium.Popup(popup_content, max_width=300)
        )

        return marker

    @staticmethod
    def create_kmz_marker(ponto_info: Dict, i: int, color: str) -> folium.Marker:
        """Marcador KMZ compacto."""
        from ui_helpers import normalize_string, html_escape
        lat, lon = ponto_info['lat'], ponto_info['lon']
        nome = (ponto_info.get('name') or f'CP {i}').strip()
        client_key = normalize_string(nome)

        marker = folium.map.Marker(
            location=[lat, lon],
            icon=DivIcon(
                icon_size=(20, 20),
                icon_anchor=(10, 10),
                html=f'''
                    <div class="kmz-checkpoint"
                         data-clientkey="{html_escape(client_key)}"
                         style="
                            background-color: {color} !important;
                            border-radius: 50% !important;
                            width: 20px !important; height: 20px !important;
                            display: flex !important;
                            justify-content: center !important;
                            align-items: center !important;
                            color: white !important;
                            font-size: 9px !important;
                            border: 1.5px solid white !important;
                         ">
                        {i}
                    </div>
                '''
            ),
            popup=folium.Popup(f"<b>Check:</b> {html_escape(nome)}", max_width=200)
        )
        return marker

class MapControls:
    @staticmethod
    def add_measure_control(mapa: folium.Map) -> None:
        MeasureControl(position='topright').add_to(mapa)

    @staticmethod
    def add_layer_control(mapa: folium.Map, collapsed: bool = False) -> None:
        folium.LayerControl(collapsed=collapsed).add_to(mapa)