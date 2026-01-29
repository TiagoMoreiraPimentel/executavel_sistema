import folium


class CheckpointSystem:
    """Sistema de checkpoints disparado por Ctrl + Click com correção de transição de popups."""

    def __init__(self, map_name: str):
        self.map_name = map_name
        self.colors = [
            '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF',
            '#FFA500', '#800080', '#008000', '#800000', '#008080', '#000080'
        ]

    def get_checkpoint_js(self) -> str:
        return f'''
        <script>
        window.tempCheckpoints = [];
        window.checkpointColors = {self.colors};
        window.checkpointColorIndex = 0;

        window.getNextCheckpointColor = function() {{
            var color = window.checkpointColors[window.checkpointColorIndex];
            window.checkpointColorIndex = (window.checkpointColorIndex + 1) % window.checkpointColors.length;
            return color;
        }};

        window.createTempCheckpoint = function(lat, lng) {{
            var checkpointId = 'cp-' + Date.now();
            var checkpointColor = window.getNextCheckpointColor();
            var checkpointNumber = window.tempCheckpoints.length + 1;
            var initialName = "PT " + checkpointNumber;

            var getIconHtml = function(name, color) {{
                return `
                    <div style="background-color: ${{color}}; 
                                display: inline-flex; justify-content: center; align-items: center; 
                                color: white; font-weight: bold; font-size: 11px; border: 2px solid white; 
                                box-shadow: 0 2px 4px rgba(0,0,0,0.3); min-width: 24px; height: 24px; 
                                padding: 0 6px; border-radius: 12px; white-space: nowrap; cursor: move;">
                        ${{name}}
                    </div>`;
            }};

            var marker = L.marker([lat, lng], {{ 
                draggable: true,
                icon: L.divIcon({{
                    className: 'custom-cp-marker',
                    html: getIconHtml(initialName, checkpointColor),
                    iconSize: null,
                    iconAnchor: [12, 12]
                }})
            }}).addTo(window.{self.map_name});

            var cpData = {{
                id: checkpointId,
                marker: marker,
                name: initialName,
                description: '',
                color: checkpointColor
            }};

            window.tempCheckpoints.push(cpData);

            // Função para alternar o conteúdo do popup sem fechar bruscamente
            window.setPopupContent = function(id, content) {{
                var cp = window.tempCheckpoints.find(c => c.id === id);
                if(cp) {{
                    cp.marker.unbindPopup();
                    cp.marker.bindPopup(content, {{ closeOnClick: false }}).openPopup();
                }}
            }};

            window.showViewPopup = function(id) {{
                var cp = window.tempCheckpoints.find(c => c.id === id);
                if(!cp) return;
                var content = `
                <div style="font-family: sans-serif; min-width: 200px;">
                    <div style="background: ${{cp.color}}; color: white; padding: 6px; margin: -14px -20px 10px -20px; text-align: center; font-weight: bold; border-radius: 4px 4px 0 0;">
                        ${{cp.name}}
                    </div>
                    <div style="font-size: 12px; color: #333; margin-bottom: 10px; line-height: 1.4; max-height: 100px; overflow-y: auto; padding-top: 5px;">
                        ${{cp.description || '<i>Sem descrição...</i>'}}
                    </div>
                    <div style="border-top: 1px solid #eee; padding-top: 8px; display: flex; gap: 5px;">
                        <button onclick="L.DomEvent.stopPropagation(event); window.showEditPopup('${{id}}')" 
                                style="flex: 1; background: #2196F3; color: white; border: none; padding: 6px; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: bold;">✏️ Editar</button>
                        <button onclick="L.DomEvent.stopPropagation(event); window.deleteCheckpoint('${{id}}')" 
                                style="flex: 1; background: #dc3545; color: white; border: none; padding: 6px; border-radius: 3px; cursor: pointer; font-size: 11px;">🗑️ Excluir</button>
                    </div>
                </div>`;
                window.setPopupContent(id, content);
            }};

            window.showEditPopup = function(id) {{
                var cp = window.tempCheckpoints.find(c => c.id === id);
                if(!cp) return;
                var content = `
                <div style="font-family: sans-serif; min-width: 200px;">
                    <div style="background: #444; color: white; padding: 6px; margin: -14px -20px 10px -20px; text-align: center; font-weight: bold;">
                        Configurações
                    </div>
                    <label style="font-size: 11px;"><b>Texto do Marcador:</b></label>
                    <input type="text" id="edit-name-${{id}}" value="${{cp.name}}" maxlength="12" style="width: 100%; margin-bottom: 8px; box-sizing: border-box; padding: 4px;">

                    <label style="font-size: 11px;"><b>Cor:</b></label>
                    <input type="color" id="edit-color-${{id}}" value="${{cp.color}}" style="width: 100%; height: 25px; margin-bottom: 8px; border: 1px solid #ccc; cursor: pointer; padding: 0;">

                    <label style="font-size: 11px;"><b>Descrição:</b></label>
                    <textarea id="edit-desc-${{id}}" style="width: 100%; height: 50px; resize: none; box-sizing: border-box; padding: 4px;">${{cp.description}}</textarea>

                    <button onclick="L.DomEvent.stopPropagation(event); window.saveChanges('${{id}}')" 
                            style="width: 100%; margin-top: 10px; background: #28a745; color: white; border: none; padding: 8px; border-radius: 3px; cursor: pointer; font-weight: bold;">💾 Salvar</button>
                </div>`;
                window.setPopupContent(id, content);
            }};

            window.saveChanges = function(id) {{
                var cp = window.tempCheckpoints.find(c => c.id === id);
                if(cp) {{
                    cp.name = document.getElementById('edit-name-' + id).value || "Ponto";
                    cp.color = document.getElementById('edit-color-' + id).value;
                    cp.description = document.getElementById('edit-desc-' + id).value;

                    cp.marker.setIcon(L.divIcon({{
                        className: 'custom-cp-marker',
                        html: getIconHtml(cp.name, cp.color),
                        iconSize: null,
                        iconAnchor: [12, 12]
                    }}));

                    window.showViewPopup(id);
                }}
            }};

            window.deleteCheckpoint = function(id) {{
                var idx = window.tempCheckpoints.findIndex(c => c.id === id);
                if(idx !== -1) {{
                    window.{self.map_name}.removeLayer(window.tempCheckpoints[idx].marker);
                    window.tempCheckpoints.splice(idx, 1);
                }}
            }};

            // Inicia edição
            window.showEditPopup(checkpointId);

            marker.on('click', function(e) {{
                L.DomEvent.stopPropagation(e);
                window.showViewPopup(checkpointId);
            }});
        }};

        window.initCheckpointSystem = function() {{
            window.{self.map_name}.on('click', function(e) {{
                if (e.originalEvent.ctrlKey) {{
                    if (!e.originalEvent.target.closest('.leaflet-marker-icon') && 
                        !e.originalEvent.target.closest('.leaflet-popup')) {{
                        window.createTempCheckpoint(e.latlng.lat, e.latlng.lng);
                    }}
                }}
            }});
        }};

        setTimeout(window.initCheckpointSystem, 500);
        </script>
        '''

    def add_to_map(self, mapa: folium.Map) -> None:
        mapa.get_root().html.add_child(folium.Element(self.get_checkpoint_js()))