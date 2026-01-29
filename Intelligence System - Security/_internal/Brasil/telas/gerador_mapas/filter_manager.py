# filter_manager.py

from typing import List, Dict
from ui_helpers import html_escape, get_vehicle_color


class FilterManager:
    def __init__(self):
        self.filters = {}

    def build_filter_html(self, eventos_unicos: List[str], veiculos_unicos: List[str],
                          kmz_cliente_opts: str = "", total_markers: int = 0,
                          mapeamento_cores: Dict[str, str] = None) -> str:
        """Constrói o HTML do painel de filtros lateral."""
        legenda_html = '<div id="legenda-container" style="margin-top:8px; max-height: 150px; overflow-y: auto; border: 1px solid #f0f0f0; padding: 5px; background: #fafafa; border-radius: 4px;">'
        for v in veiculos_unicos:
            cor_padrao = mapeamento_cores.get(v, get_vehicle_color(v)) if mapeamento_cores else get_vehicle_color(v)
            v_id = v.lower().replace(" ", "_")
            legenda_html += f'''
                <div class="legend-item" style="display: flex; align-items: center; margin-bottom: 5px; padding: 2px 4px; border-radius: 3px;">
                    <input type="color" id="color_picker_{v_id}" value="{cor_padrao}" data-tipo="{v.lower()}"
                           onchange="window.updateTypeColor('{v.lower()}', this.value)"
                           style="width: 20px; height: 20px; border: none; padding: 0; cursor: pointer; margin-right: 10px; background: none; flex-shrink: 0;">
                    <span onclick="window.selectTipo('{v.lower()}', this.parentElement)" 
                          style="font-size: 11px; color: #333; cursor: pointer; flex-grow: 1; user-select: none;">
                        {html_escape(v)}
                    </span>
                </div>
            '''
        legenda_html += '</div>'

        return f'''
        <div id="filters-box" style="position: fixed; top: 20px; left: 20px; z-index: 9999; background: white; 
            padding: 15px; border: 1px solid #999; box-shadow: 0 4px 15px rgba(0,0,0,0.3); font-family: sans-serif; font-size: 13px; width: 320px; border-radius: 8px;">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; border-bottom: 2px solid #eee; padding-bottom: 5px;">
                <b style="font-size: 14px; color: #333;">PAINEL DE FILTROS</b>
                <button id="toggleFilters" style="cursor:pointer; border:none; background:none; font-size:18px; font-weight:bold;">–</button>
            </div>
            <div id="filters-content">
                <div style="margin-bottom: 12px;">
                    <b>Intervalo de Pontos</b><br>
                    <div style="display:flex; gap:5px; margin-top:5px;">
                        <input type="number" id="startIdx" value="1" style="width: 45%; padding: 3px;">
                        <input type="number" id="endIdx" value="{total_markers}" style="width: 45%; padding: 3px;">
                        <button onclick="window.filterMarkers()" style="cursor:pointer; background:#444; color:white; border:none; border-radius:3px; padding: 0 8px;">OK</button>
                    </div>
                </div>
                <div style="margin-bottom: 12px;"><b>Legenda / Filtro de Tipo</b>{legenda_html}<input type="hidden" id="veiculoFiltro" value=""></div>
                <div style="margin-bottom: 12px; background: #f9f9f9; padding: 8px; border-radius: 4px; border: 1px solid #eee;">
                    <b>Ajustes de Visualização</b>
                    <label style="display:flex; align-items:center; cursor:pointer; margin-top:5px; font-size: 11px;">
                        <input type="checkbox" id="useDegrade" checked onchange="window.refreshAllColors()"> Ativar Degradê
                    </label>
                    <div style="margin-top:8px;">
                        <span style="font-size: 11px;">Espessura da Linha: <b id="valWeight">2</b>px</span>
                        <input type="range" id="lineWeight" min="1" max="10" value="2" oninput="window.updateLineWeight(this.value)" style="width:100%; cursor:pointer;">
                    </div>
                </div>
                <div style="margin-bottom: 12px; background: #fff4e6; padding: 8px; border-radius: 4px; border: 1px solid #ffe8cc;">
                    <b>Visualização no Checkpoint</b>
                    <label style="display:block; cursor:pointer; margin-top:5px; color: #d35400;"><input type="checkbox" id="checkShowHora" onchange="window.toggleLabelType('hora')"> <b>🕒 Hora</b></label>
                    <label style="display:block; cursor:pointer; margin-top:5px; color: #2980b9;"><input type="checkbox" id="checkShowDataHora" onchange="window.toggleLabelType('datahora')"> <b>📅 Data e Hora</b></label>
                    <label style="display:block; cursor:pointer; margin-top:5px; color: #27ae60;"><input type="checkbox" id="checkShowNome" onchange="window.toggleLabelType('nome')"> <b>👤 Nome</b></label>
                </div>
                <label style="display:block; cursor:pointer; margin-bottom:6px;"><input type="checkbox" id="showPolyline" checked onchange="window.toggleTrajeto()"> <b>Mostrar trajeto</b></label>
                <label style="display:block; cursor:pointer;"><input type="checkbox" id="hideNonMatch" onchange="window.filterMarkers()"> Ocultar não filtrados</label>
                <button onclick="window.resetAllFilters()" style="width:100%; margin-top: 15px; padding: 8px; background: #dc3545; border: none; color: white; cursor:pointer; border-radius: 4px; font-weight: bold;">Resetar Tudo</button>
            </div>
        </div>
        '''

    def build_filter_js(self, map_name: str, marker_coords: List[List[float]], total_markers: int) -> str:
        """Injeta a lógica JavaScript para interatividade em tempo real."""
        return f'''
        <script>
        window.adjustBrightness = function(hex, factor) {{
            hex = hex.replace('#', '');
            var r = parseInt(hex.substring(0, 2), 16), g = parseInt(hex.substring(2, 4), 16), b = parseInt(hex.substring(4, 6), 16);
            var nr = Math.round(r + (255 - r) * (1 - factor)), ng = Math.round(g + (255 - g) * (1 - factor)), nb = Math.round(b + (255 - b) * (1 - factor));
            return '#' + ((1 << 24) + (nr << 16) + (ng << 8) + nb).toString(16).slice(1);
        }};

        window.updateTypeColor = function(tipo, novaCor) {{
            var useDegrade = document.getElementById('useDegrade').checked;
            var pontosDoTipo = document.querySelectorAll('.marker-circle[data-veiculo="' + tipo.toLowerCase() + '"]');
            pontosDoTipo.forEach(function(el, i) {{
                var corFinal = novaCor;
                if (useDegrade) {{
                    var factor = (pontosDoTipo.length <= 1) ? 1.0 : 0.3 + (0.7 * (i / (pontosDoTipo.length - 1)));
                    corFinal = window.adjustBrightness(novaCor, factor);
                }}
                el.setAttribute('data-originalcolor', corFinal);
                if (el.style.backgroundColor !== 'yellow') el.style.backgroundColor = corFinal;
            }});
            if(window.{map_name}) {{
                window.{map_name}.eachLayer(function(layer) {{
                    if (layer.options && layer.options.isTrajeto && layer.options.vehicleType === tipo.toLowerCase()) {{
                        layer.setStyle({{ color: novaCor }});
                    }}
                }});
            }}
        }};

        window.refreshAllColors = function() {{
            document.querySelectorAll('input[id^="color_picker_"]').forEach(p => window.updateTypeColor(p.getAttribute('data-tipo'), p.value));
        }};

        window.updateLineWeight = function(val) {{
            document.getElementById('valWeight').textContent = val;
            window.{map_name}.eachLayer(function(layer) {{
                if (layer.options && layer.options.isTrajeto) {{
                   var currentOpacity = (layer.options.hasName) ? 0 : (document.getElementById('showPolyline').checked ? 0.8 : 0);
                   layer.setStyle({{ weight: parseInt(val), opacity: currentOpacity }});
                }}
            }});
        }};

        window.toggleTrajeto = function() {{
            var show = document.getElementById('showPolyline').checked;
            var weight = document.getElementById('lineWeight').value;
            window.{map_name}.eachLayer(function(layer) {{
                if (layer.options && layer.options.isTrajeto) {{
                    var op = (show && !layer.options.hasName) ? 0.8 : 0;
                    layer.setStyle({{ opacity: op, weight: parseInt(weight) }});
                }}
            }});
        }};

        window.toggleLabelType = function(origem) {{
            var checkHora = document.getElementById('checkShowHora');
            var checkDataHora = document.getElementById('checkShowDataHora');
            var checkNome = document.getElementById('checkShowNome');

            if (origem === 'hora' && checkHora.checked) {{ checkDataHora.checked = false; checkNome.checked = false; }}
            if (origem === 'datahora' && checkDataHora.checked) {{ checkHora.checked = false; checkNome.checked = false; }}
            if (origem === 'nome' && checkNome.checked) {{ checkHora.checked = false; checkDataHora.checked = false; }}

            document.querySelectorAll('.marker-circle').forEach(function(el) {{
                var sNum = el.querySelector('.m-num'), 
                    sHora = el.querySelector('.m-hora'), 
                    sDH = el.querySelector('.m-data-hora'), 
                    sNome = el.querySelector('.m-nome');

                var hasNameValue = el.getAttribute('data-hasname') === 'true';
                var corOriginal = el.getAttribute('data-originalcolor');

                sNum.style.display = 'none'; sHora.style.display = 'none'; 
                sDH.style.display = 'none'; sNome.style.display = 'none';

                if (checkNome.checked && hasNameValue) {{
                    sNome.style.display = 'block';
                    el.style.width = 'auto'; 
                    el.style.minWidth = '50px';
                    el.style.padding = '0 8px';
                    el.style.borderRadius = '4px';
                    el.style.height = '18px';
                }} else if (checkDataHora.checked) {{
                    sDH.style.display = 'block';
                    el.style.width = '110px';
                    el.style.borderRadius = '4px';
                    el.style.height = '18px';
                    el.style.padding = '0';
                }} else if (checkHora.checked) {{
                    sHora.style.display = 'block';
                    el.style.width = '38px';
                    el.style.borderRadius = '6px';
                    el.style.height = '18px';
                    el.style.padding = '0';
                }} else {{
                    sNum.style.display = 'block';
                    el.style.width = '22px';
                    el.style.height = '22px';
                    el.style.borderRadius = '50%';
                    el.style.padding = '0';
                }}

                if (el.style.backgroundColor !== 'yellow') {{
                    el.style.backgroundColor = corOriginal;
                }}
            }});
        }};

        window.filterMarkers = function() {{
            var start = parseInt(document.getElementById('startIdx').value) || 1;
            var end = parseInt(document.getElementById('endIdx').value) || {total_markers};
            var evSel = document.getElementById('eventoFiltro') ? document.getElementById('eventoFiltro').value.toLowerCase() : '';
            var veSel = document.getElementById('veiculoFiltro').value.toLowerCase();
            var igSel = document.getElementById('ignicaoFiltro') ? document.getElementById('ignicaoFiltro').value.toLowerCase() : '';
            var hide = document.getElementById('hideNonMatch').checked;

            var filtrosAtivos = (evSel !== '' || veSel !== '' || igSel !== '');

            document.querySelectorAll('.marker-circle').forEach(function(el) {{
                var idx = parseInt(el.getAttribute('data-idx'));
                var mEv = !evSel || (el.getAttribute('data-eventos') && el.getAttribute('data-eventos').toLowerCase().includes(evSel));
                var mVe = !veSel || el.getAttribute('data-veiculo').toLowerCase() === veSel;
                var mIg = !igSel || (el.getAttribute('data-ignicao') && el.getAttribute('data-ignicao').toLowerCase() === igSel);

                var shouldBeVisible = hide ? (idx >= start && idx <= end && mEv && mVe && mIg) : (idx >= start && idx <= end);
                var container = el.closest('.leaflet-marker-icon');
                if (container) container.style.display = shouldBeVisible ? 'block' : 'none';

                if (shouldBeVisible && filtrosAtivos && mEv && mVe && mIg) {{
                    el.style.backgroundColor = 'yellow'; el.style.color = 'black';
                }} else {{
                    el.style.backgroundColor = el.getAttribute('data-originalcolor'); el.style.color = 'white';
                }}
            }});
        }};

        window.resetAllFilters = function() {{
            document.getElementById('startIdx').value = 1;
            document.getElementById('endIdx').value = {total_markers};
            document.getElementById('veiculoFiltro').value = '';
            document.getElementById('checkShowHora').checked = false;
            document.getElementById('checkShowDataHora').checked = false;
            document.getElementById('checkShowNome').checked = false;
            document.getElementById('hideNonMatch').checked = false;
            document.getElementById('showPolyline').checked = true;
            document.getElementById('lineWeight').value = 2;
            document.getElementById('valWeight').textContent = "2";

            document.querySelectorAll('.legend-item').forEach(item => item.style.backgroundColor = 'transparent');
            window.toggleLabelType();
            window.filterMarkers();
            window.toggleTrajeto();
            window.refreshAllColors();
        }};

        document.addEventListener('DOMContentLoaded', function() {{
            if(window.{map_name}) {{
                window.{map_name}.on('overlayadd', function() {{
                    setTimeout(function() {{ 
                        window.refreshAllColors(); 
                        window.filterMarkers(); 
                        window.toggleLabelType(); 
                        window.toggleTrajeto(); 
                    }}, 100);
                }});
            }}
            document.getElementById('toggleFilters').onclick = function() {{
                var c = document.getElementById('filters-content');
                c.style.display = (c.style.display === 'none') ? '' : 'none';
                this.textContent = (c.style.display === 'none') ? '+' : '–';
            }};
        }});
        </script>
        '''