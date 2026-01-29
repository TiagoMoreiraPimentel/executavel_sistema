"""
Parsers para dados de Excel e arquivos KMZ/KML - Versão Categorias (Tipo).
"""
import zipfile
import xml.etree.ElementTree as ET
import re
import pandas as pd
from decimal import Decimal
from typing import Optional, Tuple, List, Dict
from ui_helpers import normalize_money, format_brl, normalize_string, html_escape


class KMZParser:
    """Parser para arquivos KMZ e KML."""

    NS = {'kml': 'http://www.opengis.net/kml/2.2', 'gx': 'http://www.google.com/kml/ext/2.2'}
    SAMPLE_EVERY = 10

    def __init__(self):
        self.pontos_info = []
        self.linhas = []

    def parse(self, caminho: str) -> Tuple[List[Dict], List[Tuple]]:
        if caminho.lower().endswith('.kml'):
            with open(caminho, 'rb') as f:
                return self._parse_kml_bytes(f.read())
        else:
            with zipfile.ZipFile(caminho, 'r') as z:
                kml_nome = next((n for n in z.namelist() if n.lower().endswith('.kml')), None)
                if not kml_nome:
                    raise RuntimeError('KMZ não contém .kml')
                return self._parse_kml_bytes(z.read(kml_nome))

    def _parse_kml_bytes(self, kml_bytes: bytes) -> Tuple[List[Dict], List[Tuple]]:
        root = ET.fromstring(kml_bytes)
        pontos_info = []
        linhas = []

        for pm in root.findall('.//kml:Placemark', self.NS):
            coords_el = pm.find('.//kml:Point/kml:coordinates', self.NS)
            if coords_el is None or not (coords_el.text or '').strip():
                continue

            coords = self._parse_coordinates_block(coords_el.text)
            if not coords: continue

            lat, lon = coords[0]
            name = self._first_text(pm, 'kml:name') or ''
            address = self._first_text(pm, 'kml:address') or ''

            valor_raw = self._extract_valor_from_extendeddata(pm)
            if not valor_raw:
                valor_raw = self._extract_valor_from_description(pm)

            valor_fmt = format_brl(valor_raw) if valor_raw else None

            pontos_info.append({
                'lat': lat, 'lon': lon,
                'name': name, 'address': address,
                'valor_raw': valor_raw, 'valor_fmt': valor_fmt
            })

        for el in root.findall('.//kml:LineString/kml:coordinates', self.NS):
            linhas += self._parse_coordinates_block(el.text)

        return pontos_info, linhas

    def _first_text(self, node, xpath: str) -> str:
        el = node.find(xpath, self.NS)
        return (el.text or '').strip() if el is not None and el.text else ''

    def _parse_coordinates_block(self, texto: str) -> List[Tuple]:
        coords = []
        if not texto: return coords
        for tok in texto.strip().replace('\n', ' ').split():
            partes = tok.split(',')
            if len(partes) >= 2:
                try:
                    coords.append((float(partes[1]), float(partes[0])))
                except: pass
        return coords

    def _extract_valor_from_extendeddata(self, pm: ET.Element) -> Optional[Decimal]:
        for data in pm.findall('.//kml:ExtendedData/kml:Data', self.NS):
            name = (data.get('name') or '').strip().lower()
            value_el = data.find('kml:value', self.NS)
            raw = (value_el.text or '').strip() if value_el is not None and value_el.text else ''
            if raw and 'valor' in name:
                norm = normalize_money(raw)
                if norm is not None: return norm
        return None

    def _extract_valor_from_description(self, pm: ET.Element) -> Optional[Decimal]:
        desc = self._first_text(pm, 'kml:description')
        if not desc: return None
        m = re.search(r'VALOR.*?(\d[\d\s.,]*)', desc, flags=re.I)
        return normalize_money(m.group(1)) if m else None


class ExcelParser:
    """Parser para arquivos Excel com dados de trajeto."""

    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.df = None
        self.df_grouped = None

    def parse(self) -> pd.DataFrame:
        """Carrega o Excel e unifica Tipo/Veículo e NOME_PESSOA."""
        self.df = pd.read_excel(self.excel_path)

        # 1. Datas e Limpeza
        self.df['Data/Hora'] = pd.to_datetime(self.df['Data/Hora'], dayfirst=True, errors='coerce')
        self.df = self.df.dropna(subset=['Data/Hora', 'Latitude', 'Longitude'])
        self.df = self.df.sort_values('Data/Hora')

        # 2. Tratamento do campo NOME_PESSOA
        if 'NOME_PESSOA' not in self.df.columns:
            self.df['NOME_PESSOA'] = ""
        else:
            self.df['NOME_PESSOA'] = self.df['NOME_PESSOA'].fillna("").astype(str).str.strip()

        # 3. Unificar Categoria (Tipo ou Veículo)
        if 'Tipo' in self.df.columns:
            self.df['Tipo'] = self.df['Tipo'].astype(str).str.strip()
        elif 'Veículo' in self.df.columns:
            self.df = self.df.rename(columns={'Veículo': 'Tipo'})
            self.df['Tipo'] = self.df['Tipo'].astype(str).str.strip()
        else:
            self.df['Tipo'] = 'Geral'

        # 4. Agrupar os dados (Mantendo o NOME_PESSOA vivo)
        self.df_grouped = self.df.groupby(['Latitude', 'Longitude', 'Tipo'], sort=False).agg({
            'Data/Hora': list,
            'Evento': list,
            'Ignição': 'last',
            'Observações': list,
            'NOME_PESSOA': 'first' # PEGA O NOME PARA O MARCADOR
        }).reset_index()

        # 5. Ordenação
        self.df_grouped['Data_Inicial'] = self.df_grouped['Data/Hora'].apply(lambda x: min(x) if x else None)
        self.df_grouped = self.df_grouped.sort_values('Data_Inicial').reset_index(drop=True)

        return self.df_grouped

    def get_unique_events(self) -> List[str]:
        """Retorna lista de eventos únicos encontrados."""
        eventos = set()
        for sublist in self.df_grouped['Evento']:
            eventos.update(sublist)
        return sorted([str(e) for e in eventos if e])

    def get_unique_types(self) -> List[str]:
        """Retorna lista de Tipos/Veículos únicos."""
        return sorted(self.df_grouped['Tipo'].unique().tolist())

    def get_center_location(self) -> List[float]:
        """Retorna a média das coordenadas para centralizar o mapa."""
        if self.df.empty: return [0.0, 0.0]
        return [self.df['Latitude'].mean(), self.df['Longitude'].mean()]