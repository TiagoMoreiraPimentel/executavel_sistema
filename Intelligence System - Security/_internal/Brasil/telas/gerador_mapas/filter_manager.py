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

        # Garantir que eventos_unicos seja uma lista de strings
        eventos_options = ""
        if eventos_unicos:
            for ev in sorted(eventos_unicos):
                eventos_options += f'<option value="{html_escape(str(ev).lower())}">{html_escape(str(ev))}</option>'

        return f'''
        <style>
            /* CSS para ocultação completa */
            .marker-hidden {{
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                pointer-events: none !important;
            }}
            .marker-faded {{
                opacity: 0.15 !important;
                pointer-events: none !important;
            }}
            /* DESTAQUE AMARELO CORRETO - apenas borda circular */
            .marker-yellow .marker-circle {{
                box-shadow: 
                    0 0 0 3px yellow,
                    0 0 0 5px rgba(255, 255, 0, 0.5),
                    inset 0 0 0 2px white !important;
                z-index: 1000 !important;
                border: 2px solid black !important;
                animation: pulse-yellow 1.5s infinite alternate !important;
            }}

            @keyframes pulse-yellow {{
                0% {{ box-shadow: 0 0 0 3px yellow, 0 0 0 5px rgba(255, 255, 0, 0.3); }}
                100% {{ box-shadow: 0 0 0 4px yellow, 0 0 0 7px rgba(255, 255, 0, 0.1); }}
            }}

            /* Estilo para desativar transições de tile layers que interferem */
            .leaflet-tile-loaded {{
                transition: none !important;
                animation: none !important;
            }}

            /* Garantir que marcadores ocultos não interfiram */
            .leaflet-marker-icon.marker-hidden {{
                transform: none !important;
                transition: none !important;
            }}

            /* Estilo para marcador quando volta para número */
            .marker-circle[data-isplaying="numero"] {{
                width: 22px !important;
                height: 22px !important;
                border-radius: 50% !important;
                font-size: 10px !important;
                padding: 0 !important;
                min-width: auto !important;
            }}

            /* Estilo para o marcador de localização */
            .location-marker {{
                background-color: #ff0000 !important;
                border: 2px solid white !important;
                box-shadow: 0 0 10px rgba(255,0,0,0.7) !important;
                animation: pulse-red 2s infinite !important;
                z-index: 2000 !important;
            }}

            @keyframes pulse-red {{
                0% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }}
                70% {{ transform: scale(1.1); box-shadow: 0 0 0 10px rgba(255, 0, 0, 0); }}
                100% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }}
            }}
        </style>

        <div id="filters-box" style="position: fixed; top: 20px; left: 20px; z-index: 9999; background: white; 
            padding: 15px; border: 1px solid #999; box-shadow: 0 4px 15px rgba(0,0,0,0.3); font-family: sans-serif; font-size: 13px; width: 320px; border-radius: 8px; max-height: 90vh; overflow-y: auto;">

            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; border-bottom: 2px solid #eee; padding-bottom: 5px; position: sticky; top: 0; background: white; z-index: 1;">
                <b style="font-size: 14px; color: #333;">PAINEL DE FILTROS</b>
                <button id="toggleFilters" style="cursor:pointer; border:none; background:none; font-size:18px; font-weight:bold;">–</button>
            </div>

            <div id="filters-content">
                <div style="margin-bottom: 12px; background: #e8f4fd; padding: 8px; border-radius: 4px; border: 1px solid #b6e0ff;">
                    <b style="color: #0066cc;">📍 Buscar por Coordenadas</b><br>
                    <div style="margin-top:5px;">
                        <div style="display:flex; align-items:center; margin-bottom:5px;">
                            <span style="font-size: 11px; width: 60px;">Latitude:</span>
                            <input type="text" id="searchLat" placeholder="Ex: -23.550650" style="width: calc(100% - 65px); padding: 3px; font-size: 11px;" value="">
                        </div>
                        <div style="display:flex; align-items:center; margin-bottom:8px;">
                            <span style="font-size: 11px; width: 60px;">Longitude:</span>
                            <input type="text" id="searchLon" placeholder="Ex: -46.633382" style="width: calc(100% - 65px); padding: 3px; font-size: 11px;" value="">
                        </div>
                        <div style="display: flex; gap: 5px;">
                            <button onclick="window.searchCoordinates()" style="cursor:pointer; background:#0066cc; color:white; border:none; border-radius:3px; padding: 5px 10px; font-size: 11px; flex: 1;">Buscar</button>
                            <button onclick="window.clearSearchMarker()" style="cursor:pointer; background:#666; color:white; border:none; border-radius:3px; padding: 5px 10px; font-size: 11px; flex: 1;">Limpar</button>
                        </div>
                        <div id="coordStatus" style="font-size: 10px; margin-top: 5px; color: #666; min-height: 14px;"></div>
                    </div>
                </div>

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
                            <option value="ligada">Ligada (L)</option>
                            <option value="desligada">Desligada (D)</option>
                        </select>
                    </div>
                    <div style="flex: 1;">
                        <b>Evento</b><br>
                        <select id="eventoFiltro" onchange="window.filterMarkers()" style="width: 100%; padding: 3px; margin-top:5px;">
                            <option value="">-- Todos --</option>
                            {eventos_options}
                        </select>
                    </div>
                </div>

                <div style="margin-bottom: 12px; background: #f0f8ff; padding: 8px; border-radius: 4px; border: 1px solid #d1e7ff;">
                    <b>Labels dos Marcadores</b><br>
                    <div style="display: flex; flex-direction: column; gap: 5px; margin-top: 5px;">
                        <label style="display: flex; align-items: center; cursor: pointer; font-size: 11px;">
                            <input type="radio" name="labelType" value="numero" checked onchange="window.toggleLabelType('numero')"> 
                            <span style="margin-left: 5px;">🔢 Número</span>
                        </label>
                        <label style="display: flex; align-items: center; cursor: pointer; font-size: 11px;">
                            <input type="radio" name="labelType" value="hora" onchange="window.toggleLabelType('hora')"> 
                            <span style="margin-left: 5px;">🕒 Hora (HH:MM)</span>
                        </label>
                        <label style="display: flex; align-items: center; cursor: pointer; font-size: 11px;">
                            <input type="radio" name="labelType" value="datahora" onchange="window.toggleLabelType('datahora')"> 
                            <span style="margin-left: 5px;">📅 Data/Hora (DD/MM HH:MM)</span>
                        </label>
                        <label style="display: flex; align-items: center; cursor: pointer; font-size: 11px;">
                            <input type="radio" name="labelType" value="nome" onchange="window.toggleLabelType('nome')"> 
                            <span style="margin-left: 5px;">👤 Nome do Motorista</span>
                        </label>
                    </div>
                </div>

                <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;">
                    <label style="display:block; cursor:pointer; margin-bottom:2px;">
                        <input type="checkbox" id="showPolyline" checked onchange="window.toggleTrajeto()"> <b>Mostrar trajeto</b>
                    </label>

                    <label style="display:block; cursor:pointer; margin-bottom:2px; color: #d94111; font-weight: bold;">
                        <input type="checkbox" id="hideNonMatch" onchange="window.filterMarkers()"> <b>OCULTAR PONTOS FORA DO FILTRO</b>
                    </label>
                </div>

                <button onclick="window.resetAllFilters()" style="width:100%; margin-top: 10px; margin-bottom: 5px; padding: 8px; background: #dc3545; border: none; color: white; cursor:pointer; border-radius: 4px; font-weight: bold;">
                    Resetar Tudo
                </button>
            </div>
        </div>
        '''

    def build_filter_js(self, map_name: str, marker_coords: List[List[float]], total_markers: int) -> str:
        return f'''
        <script>
        // Variável global para armazenar estado dos filtros
        window.currentFilters = {{
            startIdx: 1,
            endIdx: {total_markers},
            eventoFiltro: '',
            veiculoFiltro: '',
            ignicaoFiltro: '',
            labelType: 'numero',
            showPolyline: true,
            hideNonMatch: false,
            useDegrade: true,
            lineWeight: 2
        }};

        // Controlador de reaplicação de filtros
        window.filterReapplied = false;
        window.layerChangeInProgress = false;

        // Variável para o marcador de busca
        window.searchMarker = null;

        window.adjustBrightness = function(hex, factor) {{
            hex = hex.replace('#', '');
            var r = parseInt(hex.substring(0, 2), 16), g = parseInt(hex.substring(2, 4), 16), b = parseInt(hex.substring(4, 6), 16);
            var nr = Math.round(r + (255 - r) * (1 - factor)), ng = Math.round(g + (255 - g) * (1 - factor)), nb = Math.round(b + (255 - b) * (1 - factor));
            return '#' + ((1 << 24) + (nr << 16) + (ng << 8) + nb).toString(16).slice(1);
        }};

        // Função para normalizar ignição (suporta L/D e texto)
        window.normalizeIgnicao = function(value) {{
            if (!value) return '';
            value = value.toLowerCase().trim();
            if (value === 'l' || value === 'ligada' || value === 'on') return 'ligada';
            if (value === 'd' || value === 'desligada' || value === 'off') return 'desligada';
            return value;
        }};

        // Função para buscar por coordenadas
        window.searchCoordinates = function() {{
            var latInput = document.getElementById('searchLat').value.trim();
            var lonInput = document.getElementById('searchLon').value.trim();
            var statusDiv = document.getElementById('coordStatus');

            // Substituir vírgula por ponto
            latInput = latInput.replace(',', '.');
            lonInput = lonInput.replace(',', '.');

            // Validar coordenadas
            var lat = parseFloat(latInput);
            var lon = parseFloat(lonInput);

            if (isNaN(lat) || isNaN(lon)) {{
                statusDiv.innerHTML = '<span style="color: #dc3545;">❌ Coordenadas inválidas</span>';
                return;
            }}

            if (lat < -90 || lat > 90) {{
                statusDiv.innerHTML = '<span style="color: #dc3545;">❌ Latitude deve estar entre -90 e 90</span>';
                return;
            }}

            if (lon < -180 || lon > 180) {{
                statusDiv.innerHTML = '<span style="color: #dc3545;">❌ Longitude deve estar entre -180 e 180</span>';
                return;
            }}

            // Limpar marcador anterior se existir
            if (window.searchMarker) {{
                window.{map_name}.removeLayer(window.searchMarker);
                window.searchMarker = null;
            }}

            // Criar marcador vermelho
            var redIcon = L.divIcon({{
                className: 'location-marker',
                html: '<div style="background-color: #ff0000; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px rgba(255,0,0,0.7); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">📍</div>',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            }});

            window.searchMarker = L.marker([lat, lon], {{icon: redIcon}}).addTo(window.{map_name});

            // Adicionar popup com as coordenadas
            window.searchMarker.bindPopup(
                '<div style="font-family: Arial; font-size: 12px; padding: 5px;"><b>📍 Localização Buscada</b><br>' +
                'Latitude: ' + lat.toFixed(6) + '<br>' +
                'Longitude: ' + lon.toFixed(6) + '<br>' +
                '<button onclick="window.copyCoordinates()" style="margin-top: 5px; padding: 3px 8px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 10px;">Copiar Coordenadas</button></div>'
            ).openPopup();

            // Centralizar mapa na localização com zoom 15
            window.{map_name}.setView([lat, lon], 15);

            // Atualizar status
            statusDiv.innerHTML = '<span style="color: #28a745;">✅ Localização encontrada: ' + lat.toFixed(6) + ', ' + lon.toFixed(6) + '</span>';

            // Adicionar evento para copiar coordenadas
            window.copyCoordinates = function() {{
                var coords = lat.toFixed(6) + ', ' + lon.toFixed(6);
                navigator.clipboard.writeText(coords).then(function() {{
                    var popup = window.searchMarker.getPopup();
                    popup.setContent(
                        '<div style="font-family: Arial; font-size: 12px; padding: 5px;"><b>📍 Localização Buscada</b><br>' +
                        'Latitude: ' + lat.toFixed(6) + '<br>' +
                        'Longitude: ' + lon.toFixed(6) + '<br>' +
                        '<span style="color: #28a745; font-weight: bold;">✓ Coordenadas copiadas!</span></div>'
                    );
                    setTimeout(function() {{
                        popup.setContent(
                            '<div style="font-family: Arial; font-size: 12px; padding: 5px;"><b>📍 Localização Buscada</b><br>' +
                            'Latitude: ' + lat.toFixed(6) + '<br>' +
                            'Longitude: ' + lon.toFixed(6) + '<br>' +
                            '<button onclick="window.copyCoordinates()" style="margin-top: 5px; padding: 3px 8px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 10px;">Copiar Coordenadas</button></div>'
                        );
                    }}, 2000);
                }});
            }};
        }};

        // Função para limpar o marcador de busca
        window.clearSearchMarker = function() {{
            if (window.searchMarker) {{
                window.{map_name}.removeLayer(window.searchMarker);
                window.searchMarker = null;
            }}
            document.getElementById('searchLat').value = '';
            document.getElementById('searchLon').value = '';
            document.getElementById('coordStatus').innerHTML = '';
        }};

        // Função FORÇADA para reaplicar filtros imediatamente
        window.forceReapplyFilters = function() {{
            if (window.layerChangeInProgress) return;

            window.layerChangeInProgress = true;

            // Salvar estado atual
            window.saveFilterState();

            // Reaplicar IMEDIATAMENTE
            setTimeout(function() {{
                window.restoreFilterState();

                // Reaplicar todas as configurações
                window.refreshAllColors();
                window.filterMarkers();
                window.toggleLabelType(window.currentFilters.labelType);
                window.toggleTrajeto();

                // Atualizar peso da linha
                var lineWeight = document.getElementById('lineWeight');
                if (lineWeight) {{
                    window.updateLineWeight(lineWeight.value);
                }}

                window.layerChangeInProgress = false;
            }}, 10);
        }};

        // Função para observar mudanças no mapa e reaplicar filtros IMEDIATAMENTE
        window.setupMapLayerObserver = function() {{
            // Observar mudanças no controle de camadas
            var layerControl = document.querySelector('.leaflet-control-layers');
            if (layerControl) {{
                var observer = new MutationObserver(function(mutations) {{
                    if (!window.layerChangeInProgress) {{
                        window.forceReapplyFilters();
                    }}
                }});

                observer.observe(layerControl, {{ 
                    attributes: true, 
                    childList: true, 
                    subtree: true 
                }});
            }}

            // Observar o container do mapa para qualquer reconstrução
            var mapContainer = document.querySelector('.leaflet-container');
            if (mapContainer) {{
                var mapObserver = new MutationObserver(function(mutations) {{
                    mutations.forEach(function(mutation) {{
                        if (mutation.type === 'childList' && !window.filterReapplied) {{
                            window.forceReapplyFilters();
                        }}
                    }});
                }});

                mapObserver.observe(mapContainer, {{ 
                    childList: true, 
                    subtree: true 
                }});
            }}

            // Observar especificamente o painel de marcadores
            var checkMarkerPane = setInterval(function() {{
                var markerPane = document.querySelector('.leaflet-marker-pane');
                if (markerPane) {{
                    clearInterval(checkMarkerPane);

                    var markerObserver = new MutationObserver(function(mutations) {{
                        mutations.forEach(function(mutation) {{
                            if (mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0) {{
                                if (!window.filterReapplied) {{
                                    window.forceReapplyFilters();
                                }}
                            }}
                        }});
                    }});

                    markerObserver.observe(markerPane, {{ 
                        childList: true, 
                        subtree: true 
                    }});
                }}
            }}, 300);
        }};

        // Função para salvar estado atual dos filtros
        window.saveFilterState = function() {{
            var startIdx = document.getElementById('startIdx');
            var endIdx = document.getElementById('endIdx');
            var eventoFiltro = document.getElementById('eventoFiltro');
            var veiculoFiltro = document.getElementById('veiculoFiltro');
            var ignicaoFiltro = document.getElementById('ignicaoFiltro');
            var showPolyline = document.getElementById('showPolyline');
            var hideNonMatch = document.getElementById('hideNonMatch');
            var useDegrade = document.getElementById('useDegrade');
            var lineWeight = document.getElementById('lineWeight');

            if (startIdx && endIdx && eventoFiltro && veiculoFiltro && ignicaoFiltro && 
                showPolyline && hideNonMatch && useDegrade && lineWeight) {{

                window.currentFilters = {{
                    startIdx: parseInt(startIdx.value) || 1,
                    endIdx: parseInt(endIdx.value) || {total_markers},
                    eventoFiltro: eventoFiltro.value,
                    veiculoFiltro: veiculoFiltro.value,
                    ignicaoFiltro: ignicaoFiltro.value,
                    labelType: document.querySelector('input[name="labelType"]:checked')?.value || 'numero',
                    showPolyline: showPolyline.checked,
                    hideNonMatch: hideNonMatch.checked,
                    useDegrade: useDegrade.checked,
                    lineWeight: parseInt(lineWeight.value)
                }};
            }}
        }};

        // Função para restaurar estado dos filtros
        window.restoreFilterState = function() {{
            var startIdx = document.getElementById('startIdx');
            var endIdx = document.getElementById('endIdx');
            var eventoFiltro = document.getElementById('eventoFiltro');
            var veiculoFiltro = document.getElementById('veiculoFiltro');
            var ignicaoFiltro = document.getElementById('ignicaoFiltro');
            var showPolyline = document.getElementById('showPolyline');
            var hideNonMatch = document.getElementById('hideNonMatch');
            var useDegrade = document.getElementById('useDegrade');
            var lineWeight = document.getElementById('lineWeight');

            if (startIdx && endIdx && eventoFiltro && veiculoFiltro && ignicaoFiltro && 
                showPolyline && hideNonMatch && useDegrade && lineWeight) {{

                startIdx.value = window.currentFilters.startIdx;
                endIdx.value = window.currentFilters.endIdx;
                eventoFiltro.value = window.currentFilters.eventoFiltro;
                veiculoFiltro.value = window.currentFilters.veiculoFiltro;
                ignicaoFiltro.value = window.currentFilters.ignicaoFiltro;

                var labelRadios = document.getElementsByName('labelType');
                for (var i = 0; i < labelRadios.length; i++) {{
                    if (labelRadios[i].value === window.currentFilters.labelType) {{
                        labelRadios[i].checked = true;
                        break;
                    }}
                }}

                showPolyline.checked = window.currentFilters.showPolyline;
                hideNonMatch.checked = window.currentFilters.hideNonMatch;
                useDegrade.checked = window.currentFilters.useDegrade;
                lineWeight.value = window.currentFilters.lineWeight;

                var valWeight = document.getElementById('valWeight');
                if (valWeight) {{
                    valWeight.textContent = window.currentFilters.lineWeight;
                }}
            }}
        }};

        window.updateTypeColor = function(tipo, novaCor) {{
            window.saveFilterState();
            var useDegrade = document.getElementById('useDegrade').checked;
            var pontosDoTipo = document.querySelectorAll('.marker-circle[data-veiculo="' + tipo.toLowerCase() + '"]');
            pontosDoTipo.forEach(function(el, i) {{
                var corFinal = novaCor;
                if (useDegrade) {{
                    var factor = (pontosDoTipo.length <= 1) ? 1.0 : 0.3 + (0.7 * (i / (pontosDoTipo.length - 1)));
                    corFinal = window.adjustBrightness(novaCor, factor);
                }}
                el.setAttribute('data-originalcolor', corFinal);
                // Só atualiza a cor se não estiver em destaque amarelo
                if (el.style.backgroundColor !== 'yellow') el.style.backgroundColor = corFinal;
            }});
            if(window.{map_name}) {{
                window.{map_name}.eachLayer(function(layer) {{
                    if (layer.options && layer.options.isTrajeto && layer.options.vehicleType === tipo.toLowerCase()) {{
                        layer.setStyle({{ color: novaCor }});
                    }}
                }});
            }}
            window.filterMarkers();
        }};

        window.refreshAllColors = function() {{
            window.saveFilterState();
            document.querySelectorAll('input[id^="color_picker_"]').forEach(p => {{
                var tipo = p.getAttribute('data-tipo');
                var cor = p.value;
                window.updateTypeColor(tipo, cor);
            }});
        }};

        window.updateLineWeight = function(val) {{
            window.saveFilterState();
            var valWeight = document.getElementById('valWeight');
            if (valWeight) valWeight.textContent = val;
            if (window.{map_name}) {{
                window.{map_name}.eachLayer(function(layer) {{
                    if (layer.options && layer.options.isTrajeto) layer.setStyle({{ weight: parseInt(val) }});
                }});
            }}
        }};

        window.selectTipo = function(tipo, elemento) {{
            window.saveFilterState();
            document.getElementById('veiculoFiltro').value = tipo;
            document.querySelectorAll('.legend-item').forEach(item => item.style.backgroundColor = 'transparent');
            if(elemento) elemento.style.backgroundColor = '#eef2ff';
            window.filterMarkers();
        }};

        window.toggleTrajeto = function() {{
            window.saveFilterState();
            var show = document.getElementById('showPolyline').checked;
            var weight = document.getElementById('lineWeight').value;
            if (window.{map_name}) {{
                window.{map_name}.eachLayer(function(layer) {{
                    if (layer.options && layer.options.isTrajeto) {{
                        layer.setStyle({{ opacity: show ? 0.8 : 0, weight: show ? parseInt(weight) : 0 }});
                    }}
                }});
            }}
        }};

        window.filterMarkers = function() {{
            window.saveFilterState();
            var start = parseInt(document.getElementById('startIdx').value) || 1;
            var end = parseInt(document.getElementById('endIdx').value) || {total_markers};
            var evSel = document.getElementById('eventoFiltro').value.toLowerCase();
            var veSel = document.getElementById('veiculoFiltro').value.toLowerCase();
            var igSel = document.getElementById('ignicaoFiltro').value.toLowerCase();
            var hide = document.getElementById('hideNonMatch').checked;

            var filtrosAtivos = (evSel !== '' || veSel !== '' || igSel !== '');

            document.querySelectorAll('.marker-circle').forEach(function(el) {{
                var idx = parseInt(el.getAttribute('data-idx'));
                var eventosStr = el.getAttribute('data-eventos') || '';
                var mEv = !evSel || eventosStr.toLowerCase().includes(evSel);
                var mVe = !veSel || el.getAttribute('data-veiculo').toLowerCase() === veSel;

                // CORREÇÃO DO FILTRO DE IGNIÇÃO
                var ignicaoAttr = el.getAttribute('data-ignicao') || '';
                var ignicaoNormalizada = window.normalizeIgnicao(ignicaoAttr);
                var mIg = !igSel || ignicaoNormalizada === igSel;

                var inRange = (idx >= start && idx <= end);
                var isMatch = mEv && mVe && mIg;

                // VISIBILIDADE: Se hide tá on, precisa de range E match. Se hide tá off, só range.
                var shouldBeVisible = hide ? (inRange && isMatch) : inRange;

                var container = el.closest('.leaflet-marker-icon');

                if (shouldBeVisible) {{
                    // REMOVE TODAS AS CLASSES DE OCULTAÇÃO
                    if (container) {{
                        container.classList.remove('marker-hidden', 'marker-faded');
                        container.style.display = 'block';
                        container.style.opacity = '1';
                        container.style.visibility = 'visible';
                    }}
                    el.style.display = 'flex';

                    // DESTAQUE AMARELO CORRIGIDO - apenas background amarelo
                    if (filtrosAtivos && isMatch) {{
                        el.style.backgroundColor = 'yellow';
                        el.style.color = 'black';
                        el.style.fontWeight = 'bold';
                        if (container) {{
                            container.classList.add('marker-yellow');
                            container.style.zIndex = "1000";
                        }}
                    }} else {{
                        el.style.backgroundColor = el.getAttribute('data-originalcolor');
                        el.style.color = 'white';
                        el.style.fontWeight = 'normal';
                        if (container) {{
                            container.classList.remove('marker-yellow');
                            container.style.zIndex = "1";
                        }}
                    }}
                }} else {{
                    // OCULTAÇÃO COMPLETA
                    if (container) {{
                        container.classList.add('marker-hidden');
                        container.style.display = 'none';
                        container.style.visibility = 'hidden';
                        container.style.opacity = '0';
                    }}
                    el.style.display = 'none';
                }}
            }});

            // Ajusta linhas também se necessário
            if (window.{map_name}) {{
                window.{map_name}.eachLayer(function(layer) {{
                    if (layer.options && layer.options.isTrajeto && hide) {{
                        // Verificar se há marcadores visíveis para este trajeto
                        var tipo = layer.options.vehicleType;
                        var markersVisiveis = document.querySelectorAll('.marker-circle[data-veiculo="' + tipo + '"]:not([style*="display: none"])');
                        if (markersVisiveis.length === 0) {{
                            layer.setStyle({{ opacity: 0, weight: 0 }});
                        }} else {{
                            var weight = document.getElementById('lineWeight').value;
                            layer.setStyle({{ opacity: 0.8, weight: parseInt(weight) }});
                        }}
                    }}
                }});
            }}
        }};

        window.toggleLabelType = function(labelType) {{
            window.saveFilterState();
            var selectedType = labelType || document.querySelector('input[name="labelType"]:checked')?.value || 'numero';

            // Atualizar radios
            var radios = document.getElementsByName('labelType');
            for (var i = 0; i < radios.length; i++) {{
                radios[i].checked = (radios[i].value === selectedType);
            }}

            document.querySelectorAll('.marker-circle').forEach(function(el) {{
                var spanNum = el.querySelector('.m-num');
                var spanHora = el.querySelector('.m-hora');
                var spanDataHora = el.querySelector('.m-data-hora');
                var spanNome = el.querySelector('.m-nome');

                // Esconder todos primeiro
                if (spanNum) spanNum.style.display = 'none';
                if (spanHora) spanHora.style.display = 'none';
                if (spanDataHora) spanDataHora.style.display = 'none';
                if (spanNome) spanNome.style.display = 'none';

                // Resetar completamente o estilo do marcador para o padrão
                el.style.width = '22px';
                el.style.height = '22px';
                el.style.borderRadius = '50%';
                el.style.fontSize = '10px';
                el.style.padding = '0';
                el.style.minWidth = '';
                el.setAttribute('data-isplaying', selectedType);

                // Mostrar apenas o selecionado e ajustar estilo
                switch(selectedType) {{
                    case 'hora':
                        if (spanHora) {{
                            spanHora.style.display = 'block';
                            el.style.width = '38px';
                            el.style.borderRadius = '6px';
                            el.style.height = '18px';
                            el.style.fontSize = '9px';
                        }}
                        break;
                    case 'datahora':
                        if (spanDataHora) {{
                            spanDataHora.style.display = 'block';
                            el.style.width = '85px';
                            el.style.borderRadius = '6px';
                            el.style.height = '18px';
                            el.style.fontSize = '8px';
                        }}
                        break;
                    case 'nome':
                        if (spanNome && el.getAttribute('data-hasname') === 'true') {{
                            spanNome.style.display = 'block';
                            el.style.width = 'auto';
                            el.style.minWidth = 'auto';
                            el.style.padding = '0 10px';
                            el.style.borderRadius = '4px';
                            el.style.height = '20px';
                            el.style.fontSize = '9px';
                            el.style.whiteSpace = 'nowrap';
                            el.style.overflow = 'visible';
                        }} else {{
                            // Se não tem nome, mostra número
                            if (spanNum) {{
                                spanNum.style.display = 'block';
                                el.style.width = '22px';
                                el.style.height = '22px';
                                el.style.borderRadius = '50%';
                                el.style.fontSize = '10px';
                            }}
                        }}
                        break;
                    default: // numero
                        if (spanNum) {{
                            spanNum.style.display = 'block';
                            // Garantir tamanho e fonte padrão
                            el.style.width = '22px';
                            el.style.height = '22px';
                            el.style.borderRadius = '50%';
                            el.style.fontSize = '10px';
                            el.style.padding = '0';
                            el.style.minWidth = '';
                        }}
                        break;
                }}
            }});
        }};

        window.resetAllFilters = function() {{
            window.currentFilters = {{
                startIdx: 1,
                endIdx: {total_markers},
                eventoFiltro: '',
                veiculoFiltro: '',
                ignicaoFiltro: '',
                labelType: 'numero',
                showPolyline: true,
                hideNonMatch: false,
                useDegrade: true,
                lineWeight: 2
            }};

            window.restoreFilterState();
            window.updateLineWeight(2);
            window.toggleTrajeto();
            window.toggleLabelType('numero');
            window.refreshAllColors();
            window.filterMarkers();

            // Resetar seleção de tipo na legenda
            document.querySelectorAll('.legend-item').forEach(item => {{
                item.style.backgroundColor = 'transparent';
            }});

            // Limpar marcador de busca
            window.clearSearchMarker();
        }};

        document.addEventListener('DOMContentLoaded', function() {{
            // Configurar botão de toggle
            var btn = document.getElementById('toggleFilters');
            if(btn) btn.onclick = function() {{
                var c = document.getElementById('filters-content');
                c.style.display = (c.style.display === 'none') ? '' : 'none';
                this.textContent = (c.style.display === 'none') ? '+' : '–';
            }};

            // Configurar observer para camadas do mapa
            window.setupMapLayerObserver();

            // Inicializar filtros após um breve delay
            setTimeout(function() {{
                window.restoreFilterState();
                window.filterMarkers();
                window.toggleLabelType();

                // Adicionar evento de Enter nos campos de busca
                document.getElementById('searchLat').addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') window.searchCoordinates();
                }});
                document.getElementById('searchLon').addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') window.searchCoordinates();
                }});
            }}, 500);
        }});
        </script>
        '''