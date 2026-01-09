from typing import List, Dict
from ui_helpers import html_escape, get_vehicle_color


class FilterManager:
    def __init__(self):
        self.filters = {}

    def build_filter_html(self, eventos_unicos: List[str],
                          veiculos_unicos: List[str],
                          kmz_cliente_opts: str = "",
                          total_markers: int = 0,
                          mapeamento_cores: Dict[str, str] = None) -> str:
        # Legenda com Seletor de Cores
        legenda_html = '<div id="legenda-container" style="margin-top:8px; max-height: 150px; overflow-y: auto; border: 1px solid #f0f0f0; padding: 5px; background: #fafafa; border-radius: 4px;">'
        for v in veiculos_unicos:
            # Usa a cor vinda do mapeamento se existir, senão usa a padrão
            cor_padrao = mapeamento_cores.get(v, get_vehicle_color(v)) if mapeamento_cores else get_vehicle_color(v)
            v_id = v.lower().replace(" ", "_")
            legenda_html += f'''
                <div class="legend-item" style="display: flex; align-items: center; margin-bottom: 5px; padding: 2px 4px; border-radius: 3px;">
                    <input type="color" 
                           id="color_picker_{v_id}" 
                           value="{cor_padrao}" 
                           data-tipo="{v.lower()}"
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

                <div style="margin-bottom: 12px;">
                    <b>Legenda / Filtro de Tipo</b>
                    {legenda_html}
                    <button onclick="window.selectTipo('', null)" style="font-size: 10px; margin-top: 5px; cursor: pointer; background: none; border: 1px solid #ccc; border-radius: 3px; padding: 2px 5px;">Limpar Seleção</button>
                    <input type="hidden" id="veiculoFiltro" value="">
                </div>

                <div style="margin-bottom: 12px; background: #f9f9f9; padding: 8px; border-radius: 4px; border: 1px solid #eee;">
                    <b>Ajustes de Visualização</b>
                    <label style="display:flex; align-items:center; cursor:pointer; margin-top:5px; font-size: 11px;">
                        <input type="checkbox" id="useDegrade" checked onchange="window.refreshAllColors()"> Ativar Degradê (Fading)
                    </label>
                    <div style="margin-top:8px;">
                        <span style="font-size: 11px;">Espessura da Linha: <b id="valWeight">2</b>px</span>
                        <input type="range" id="lineWeight" min="1" max="10" value="2" oninput="window.updateLineWeight(this.value)" style="width:100%; cursor:pointer;">
                    </div>
                </div>

                <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                    <div style="flex: 1;">
                        <b>Ignição</b><br>
                        <select id="ignicaoFiltro" onchange="window.filterMarkers()" style="width: 100%; padding: 3px; margin-top:5px;">
                            <option value="">-- Todas --</option>
                            <option value="l">Ligada (L)</option>
                            <option value="d">Desligada (D)</option>
                        </select>
                    </div>
                    <div style="flex: 1;">
                        <b>Evento</b><br>
                        <select id="eventoFiltro" onchange="window.filterMarkers()" style="width: 100%; padding: 3px; margin-top:5px;">
                            <option value="">-- Todos --</option>
                            {''.join(f'<option value="{html_escape(ev.lower())}">{html_escape(ev)}</option>' for ev in eventos_unicos)}
                        </select>
                    </div>
                </div>

                <label style="display:block; cursor:pointer; margin-bottom:6px;">
                    <input type="checkbox" id="showPolyline" checked onchange="window.toggleTrajeto()"> <b>Mostrar trajeto</b>
                </label>

                <label style="display:block; cursor:pointer; margin-bottom:6px; color: #d35400;">
                    <input type="checkbox" id="checkShowHora" onchange="window.toggleLabelType()"> <b>🕒 Mostrar Hora (HH:MM)</b>
                </label>

                <label style="display:block; cursor:pointer;">
                    <input type="checkbox" id="hideNonMatch" onchange="window.filterMarkers()"> Ocultar pontos não filtrados
                </label>

                <button onclick="window.resetAllFilters()" style="width:100%; margin-top: 15px; padding: 8px; background: #dc3545; border: none; color: white; cursor:pointer; border-radius: 4px; font-weight: bold;">
                    Resetar Tudo
                </button>
            </div>
        </div>
        '''

    def build_filter_js(self, map_name: str, marker_coords: List[List[float]], total_markers: int) -> str:
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
                if (layer.options && layer.options.isTrajeto) layer.setStyle({{ weight: parseInt(val) }});
            }});
        }};

        window.selectTipo = function(tipo, elemento) {{
            document.getElementById('veiculoFiltro').value = tipo;
            document.querySelectorAll('.legend-item').forEach(item => item.style.backgroundColor = 'transparent');
            if(elemento) elemento.style.backgroundColor = '#eef2ff';
            window.filterMarkers();
        }};

        window.toggleTrajeto = function() {{
            var show = document.getElementById('showPolyline').checked;
            var weight = document.getElementById('lineWeight').value;
            window.{map_name}.eachLayer(function(layer) {{
                if (layer.options && layer.options.isTrajeto) {{
                    layer.setStyle({{ opacity: show ? 0.8 : 0, weight: show ? parseInt(weight) : 0 }});
                }}
            }});
        }};

        window.filterMarkers = function() {{
            var start = parseInt(document.getElementById('startIdx').value) || 1;
            var end = parseInt(document.getElementById('endIdx').value) || {total_markers};
            var evSel = document.getElementById('eventoFiltro').value.toLowerCase();
            var veSel = document.getElementById('veiculoFiltro').value.toLowerCase();
            var igSel = document.getElementById('ignicaoFiltro').value.toLowerCase();
            var hide = document.getElementById('hideNonMatch').checked;

            var filtrosAtivos = (evSel !== '' || veSel !== '' || igSel !== '');

            document.querySelectorAll('.marker-circle').forEach(function(el) {{
                var idx = parseInt(el.getAttribute('data-idx'));
                var mEv = !evSel || el.getAttribute('data-eventos').toLowerCase().includes(evSel);
                var mVe = !veSel || el.getAttribute('data-veiculo').toLowerCase() === veSel;
                var mIg = !igSel || el.getAttribute('data-ignicao').toLowerCase() === igSel;

                var inRange = (idx >= start && idx <= end);
                var isMatch = mEv && mVe && mIg;

                // VISIBILIDADE: Se hide tá on, precisa de range E match. Se hide tá off, só range.
                var shouldBeVisible = hide ? (inRange && isMatch) : inRange;

                var container = el.closest('.leaflet-marker-icon');

                if (shouldBeVisible) {{
                    el.style.display = 'flex';
                    if (container) {{
                        container.style.display = 'block';
                        container.style.opacity = '1';
                    }}

                    if (filtrosAtivos && isMatch) {{
                        el.style.backgroundColor = 'yellow';
                        el.style.color = 'black';
                        el.style.fontWeight = 'bold';
                        if (container) container.style.zIndex = "1000";
                    }} else {{
                        el.style.backgroundColor = el.getAttribute('data-originalcolor');
                        el.style.color = 'white';
                        el.style.fontWeight = 'normal';
                        if (container) container.style.zIndex = "1";
                    }}
                }} else {{
                    el.style.display = 'none';
                    if (container) {{
                        container.style.display = 'none';
                    }}
                }}
            }});
        }};

        window.toggleLabelType = function() {{
            var showHora = document.getElementById('checkShowHora').checked;
            document.querySelectorAll('.marker-circle').forEach(function(el) {{
                var spanNum = el.querySelector('.m-num'), spanHora = el.querySelector('.m-hora');
                if (showHora) {{
                    spanNum.style.display = 'none'; spanHora.style.display = 'block';
                    el.style.width = '38px'; el.style.borderRadius = '6px'; el.style.height = '18px';
                }} else {{
                    spanNum.style.display = 'block'; spanHora.style.display = 'none';
                    el.style.width = '22px'; el.style.height = '22px'; el.style.borderRadius = '50%';
                }}
            }});
        }};

        window.resetAllFilters = function() {{
            document.getElementById('startIdx').value = 1;
            document.getElementById('endIdx').value = {total_markers};
            document.getElementById('eventoFiltro').value = '';
            document.getElementById('ignicaoFiltro').value = '';
            document.getElementById('veiculoFiltro').value = '';
            document.getElementById('showPolyline').checked = true;
            document.getElementById('hideNonMatch').checked = false;
            document.getElementById('useDegrade').checked = true;
            document.getElementById('checkShowHora').checked = false;
            document.getElementById('lineWeight').value = 2;

            document.querySelectorAll('.legend-item').forEach(item => {{
                item.style.backgroundColor = 'transparent';
            }});

            window.updateLineWeight(2);
            window.toggleTrajeto();
            window.toggleLabelType();
            window.refreshAllColors();
            window.filterMarkers();
        }};

        document.addEventListener('DOMContentLoaded', function() {{
            var btn = document.getElementById('toggleFilters');
            if(btn) btn.onclick = function() {{
                var c = document.getElementById('filters-content');
                c.style.display = (c.style.display === 'none') ? '' : 'none';
                this.textContent = (c.style.display === 'none') ? '+' : '–';
            }};
            window.filterMarkers();
        }});
        </script>
        '''