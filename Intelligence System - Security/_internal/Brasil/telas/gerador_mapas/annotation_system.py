"""
Sistema de anotações arrastáveis para o mapa.
"""
import folium
from ui_helpers import html_escape


class AnnotationSystem:
    """Sistema de anotações arrastáveis."""

    def __init__(self, map_name: str):
        """
        Inicializa sistema de anotações.

        Args:
            map_name: Nome do mapa Folium
        """
        self.map_name = map_name

    def get_annotation_js(self) -> str:
        """
        Retorna JavaScript do sistema de anotações.

        Returns:
            JavaScript das anotações
        """
        js = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function () {{
            var map = window.{self.map_name};
            var anotacoes = [];

            function salvarAnotacoes() {{
                var dados = anotacoes.map(item => ({{ 
                    texto: item.texto,
                    origem: item.origem,
                    deslocamento: item.marker.getLatLng()
                }}));
                localStorage.setItem('anotacoesMapa', JSON.stringify(dados));
            }}

            function carregarAnotacoes() {{
                var dados = JSON.parse(localStorage.getItem('anotacoesMapa') || '[]');
                dados.forEach(item => {{
                    adicionarAnotacao(item.origem.lat, item.origem.lng, item.texto, item.deslocamento);
                }});
            }}

            function adicionarAnotacao(lat, lng, nota, posicaoFinal=null) {{
                var anotacaoIcon = L.divIcon({{
                    className: 'custom-note',
                    html: `
                        <div style="
                            background-color: rgba(255,255,200,0.95);
                            border: 1px solid #aaa;
                            padding: 6px 10px;
                            border-radius: 6px;
                            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                            font-family: Arial;
                            font-size: 13px;
                            font-weight: bold;
                            max-width: 200px;
                            cursor: pointer;
                            user-select: none;
                        ">
                            📝 <span class="texto-nota">${{nota}}</span>
                            <br><small style="color: red; cursor: pointer;" class="remover-nota">[remover]</small>
                        </div>
                    `,
                    iconSize: [150, 40],
                    iconAnchor: [75, 20]
                }});

                var finalLat = posicaoFinal ? posicaoFinal.lat : lat + 0.0007;
                var finalLng = posicaoFinal ? posicaoFinal.lng : lng + 0.0007;

                var marcadorNota = L.marker([finalLat, finalLng], {{icon: anotacaoIcon, draggable: true}}).addTo(map);
                var linha = L.polyline([[lat, lng], marcadorNota.getLatLng()], {{color: 'black', weight: 2}}).addTo(map);

                marcadorNota.on('drag', function() {{
                    linha.setLatLngs([[lat, lng], marcadorNota.getLatLng()]);
                    salvarAnotacoes();
                }});

                marcadorNota.on('click', function(e) {{
                    var spanTexto = e.target.getElement().querySelector('.texto-nota');
                    var novoTexto = prompt("Editar nota:", spanTexto.textContent);
                    if (novoTexto !== null && novoTexto.trim() !== "") {{
                        spanTexto.textContent = novoTexto;
                        var anotacao = anotacoes.find(obj => obj.marker === marcadorNota);
                        if (anotacao) {{
                            anotacao.texto = novoTexto;
                        }}
                        salvarAnotacoes();
                    }}
                }});

                marcadorNota.getElement().querySelector('.remover-nota').addEventListener('click', function(ev) {{
                    ev.stopPropagation();
                    map.removeLayer(marcadorNota);
                    map.removeLayer(linha);
                    anotacoes = anotacoes.filter(obj => obj.marker !== marcadorNota);
                    salvarAnotacoes();
                }});

                var item = {{marker: marcadorNota, linha: linha, texto: nota, origem: {{lat: lat, lng: lng}}}};
                anotacoes.push(item);
                salvarAnotacoes();
            }}

            map.on('click', function(e) {{
                var nota = prompt("Digite a nota para este local:");
                if (nota) {{
                    adicionarAnotacao(e.latlng.lat, e.latlng.lng, nota);
                }}
            }});

            carregarAnotacoes();
        }});
        </script>
        """

        return js