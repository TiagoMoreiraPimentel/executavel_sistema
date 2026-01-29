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
        Cria marcador com suporte para Número, Hora, Data/Hora e Nome.
        """
        # Extrair dados do primeiro horário do grupo
        data_hora = row['Data/Hora'][0] if isinstance(row['Data/Hora'], list) else row['Data/Hora']
        hora_resumida = data_hora.strftime('%H:%M')
        data_hora_completa = data_hora.strftime('%d/%m %H:%M')

        lat, lon = row['Latitude'], row['Longitude']
        eventos = row['Evento']
        horas = row['Data/Hora']

        # Tratamento do nome do motorista
        nome_pessoa = str(row.get('NOME_PESSOA', '')).strip()
        invalidos = ['nan', 'n/i', 'none', 'null', '', '0']
        tem_nome_valido = nome_pessoa and nome_pessoa.lower() not in invalidos
        if not tem_nome_valido:
            nome_pessoa = "N/I"

        # CORREÇÃO DA IGNIÇÃO: suporta L/D e texto
        ign_raw = str(row.get('Ignição', '')).strip().upper()
        if ign_raw == 'L':
            ign_display = 'Ligada'
            ign_filter = 'ligada'
        elif ign_raw == 'D':
            ign_display = 'Desligada'
            ign_filter = 'desligada'
        else:
            ign_lower = ign_raw.lower()
            if 'ligada' in ign_lower or 'on' in ign_lower:
                ign_display = ign_raw
                ign_filter = 'ligada'
            elif 'desligada' in ign_lower or 'off' in ign_lower:
                ign_display = ign_raw
                ign_filter = 'desligada'
            else:
                ign_display = ign_raw
                ign_filter = ign_lower

        descricoes = row.get('Observações', [])

        # Processar histórico e observações para o Popup
        desc_itens = []
        for h, d in zip(horas, descricoes):
            if is_nonempty_desc(d):
                linha = f"{h.strftime('%d/%m/%Y %H:%M:%S')} — {html_escape(str(d))}"
                desc_itens.append(linha)

        descricao_section = ""
        if desc_itens:
            descricao_html = "".join(
                f"<li style='margin-bottom:2px; padding: 2px 0;'>{item}</li>" for item in desc_itens)
            descricao_section = f'''
            <div style="margin-top:8px; border-top: 1px solid #eee; padding-top: 8px;">
                <b>Observações:</b>
                <div style="max-height: 150px; overflow-y: auto; padding: 5px; background: #f9f9f9; border-radius: 4px; margin-top: 5px;">
                    <ul style="padding-left: 15px; margin: 5px 0; font-size: 11px;">{descricao_html}</ul>
                </div>
            </div>
            '''

        # CORREÇÃO: Mostrar data e hora completa nos eventos
        eventos_html = ""
        if eventos and horas:
            eventos_list = []
            for h, e in zip(horas, eventos):
                # Mostrar data e hora completa no formato DD/MM/YYYY HH:MM:SS
                timestamp = h.strftime('%d/%m/%Y %H:%M:%S')
                eventos_list.append(
                    f"<li style='margin-bottom: 3px; padding: 2px 0; border-bottom: 1px dotted #eee;'><span style='color: #007bff; font-weight: bold;'>{timestamp}</span>: {html_escape(str(e))}</li>")
            eventos_html = "".join(eventos_list)

        # Popup com scroll vertical e horizontal
        popup_content = f"""
        <div style="
            font-family: Arial, sans-serif; 
            font-size: 12px; 
            width: 340px; 
            max-height: 450px; 
            overflow: auto; 
            color: #333;
            padding-right: 5px;
            box-sizing: border-box;
        ">
            <div style="
                background-color: {icon_color}; 
                color: white; 
                padding: 8px; 
                border-radius: 4px 4px 0 0; 
                font-weight: bold; 
                text-align: center; 
                margin-bottom: 10px;
                position: sticky;
                top: 0;
                z-index: 10;
            ">
                Ponto #{idx + 1} - {html_escape(vehicle_name)}
            </div>

            <div style="padding: 0 5px;">
                <table style="width: 100%; margin-bottom: 10px; border-collapse: collapse; min-width: 320px;">
                    <tr><td style="color: #666; width: 90px; padding: 3px 0; vertical-align: top;"><b>Motorista:</b></td><td style="padding: 3px 0; word-break: break-word;">{html_escape(nome_pessoa)}</td></tr>
                    <tr><td style="color: #666; padding: 3px 0; vertical-align: top;"><b>Ignição:</b></td><td style="padding: 3px 0;">{html_escape(ign_display)}</td></tr>
                    <tr><td style="color: #666; padding: 3px 0; vertical-align: top;"><b>Data/Hora:</b></td><td style="padding: 3px 0; white-space: nowrap;">{data_hora.strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
                    <tr><td style="color: #666; padding: 3px 0; vertical-align: top;"><b>Coordenadas:</b></td><td style="padding: 3px 0; font-size: 11px; font-family: monospace; white-space: nowrap;">{lat:.6f}, {lon:.6f}</td></tr>
                </table>

                <div style="
                    max-height: 200px; 
                    overflow-y: auto; 
                    overflow-x: auto;
                    padding: 8px; 
                    background: #f9f9f9; 
                    border-radius: 4px; 
                    border: 1px solid #eee; 
                    margin-top: 10px;
                    min-width: 320px;
                ">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #555; font-size: 11px; position: sticky; top: 0; background: #f9f9f9; padding: 2px 0;">
                        Histórico de Eventos:
                    </div>
                    <ul style="
                        padding-left: 15px; 
                        margin: 0; 
                        list-style: none; 
                        font-size: 11px; 
                        min-width: 300px;
                    ">
                        {eventos_html}
                    </ul>
                </div>

                {descricao_section}
            </div>
        </div>
        """

        # Dados para filtros
        evento_lista_str = ','.join(set(map(str, eventos))).replace("'", "").replace('"', "")

        # HTML do Marcador - Tamanho padrão para número (22px circular)
        # CORREÇÃO: Removido o truncamento do nome
        marker_html = f'''
            <div class="marker-circle" 
                 id="marker-{idx + 1}"
                 data-idx="{idx + 1}" 
                 data-eventos="{evento_lista_str.lower()}"
                 data-ignicao="{ign_filter}"
                 data-veiculo="{vehicle_name.lower()}"
                 data-originalcolor="{icon_color}"
                 data-hasname="{"true" if tem_nome_valido else "false"}"
                 data-isplaying="numero"
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
                    cursor: pointer;
                    width: 22px; 
                    height: 22px; 
                    border-radius: 50%;
                    padding: 0 !important;
                    min-width: auto !important;
                    box-sizing: border-box;
                 "
                 onclick="if(window.selectMarker) window.selectMarker({idx + 1})">
                <span class="m-num">{idx + 1}</span>
                <span class="m-hora" style="display:none;">{hora_resumida}</span>
                <span class="m-data-hora" style="display:none;">{data_hora_completa}</span>
                <span class="m-nome" style="display:none;">{html_escape(nome_pessoa)}</span>
            </div>
        '''

        marker = folium.map.Marker(
            location=[lat, lon],
            icon=DivIcon(
                icon_size=(250, 22),
                icon_anchor=(11, 11),
                html=marker_html
            ),
            popup=folium.Popup(popup_content, max_width=400)
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
            popup=folium.Popup(f"<b>Checkpoint:</b> {html_escape(nome)}", max_width=200)
        )
        return marker


class MapControls:
    @staticmethod
    def add_measure_control(mapa: folium.Map) -> None:
        MeasureControl(position='topright').add_to(mapa)

    @staticmethod
    def add_layer_control(mapa: folium.Map, collapsed: bool = False) -> None:
        folium.LayerControl(collapsed=collapsed).add_to(mapa)