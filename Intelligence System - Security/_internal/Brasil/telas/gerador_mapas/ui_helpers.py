"""
Utilitários para formatação, normalização e manipulação de strings.
"""
import re
import hashlib
from decimal import Decimal
from typing import Optional
import pandas as pd

# =================================================================
# DICIONÁRIO MESTRE DE TIPOS E CORES
# Para adicionar um novo tipo, basta inserir uma linha aqui.
# =================================================================
CONFIG_TIPOS = {
    "VEÍCULO 1":      "#0608C2",
    "VEÍCULO 2":      "#8F0606",
    "VEÍCULO 3":      "#1D5F96",
    "ISCA 1":         "#778504",
    "ISCA 2":         "#63065D",
    "ISCA 3":         "#2E7D32",
    "ESCOLTA":        "#C42DAC",
    "SENSOR":         "#FF8C00",
    "TRAVA_CILTRONC": "#469E92",
}

def html_escape(s: str) -> str:
    """
    Escapa caracteres especiais para HTML.

    Args:
        s: String a ser escapada

    Returns:
        String com caracteres escapados
    """
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def normalize_string(s: str) -> str:
    """
    Normaliza string removendo espaços extras e convertendo para minúsculas.

    Args:
        s: String a ser normalizada

    Returns:
        String normalizada
    """
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def is_nonempty_desc(x) -> bool:
    """
    Verifica se um valor é uma descrição não vazia.

    Args:
        x: Valor a ser verificado

    Returns:
        True se for uma descrição não vazia, False caso contrário
    """
    if x is None:
        return False

    # Verifica se é NaN/NaT
    try:
        if pd.isna(x):
            return False
    except Exception:
        pass

    s = str(x).strip()
    if not s or s.lower() in ('nan', 'nat'):
        return False
    return True


def format_brl(num) -> Optional[str]:
    """
    Formata valor (Decimal ou string) como 'R$ 1.234,56'.

    Args:
        num: Valor a ser formatado (Decimal ou string)

    Returns:
        String formatada ou None
    """
    if num is None:
        return None

    if isinstance(num, Decimal):
        v = num
    else:
        v = normalize_money(str(num))
        if v is None:
            return str(num)

    # Garante 2 casas e monta milhar com ponto, decimal com vírgula
    v = v.quantize(Decimal('0.01'))
    neg = '-' if v < 0 else ''
    s = f"{abs(v):.2f}"           # '1200.00'
    inteiro, dec = s.split('.')   # ('1200', '00')
    milhar = f"{int(inteiro):,}".replace(',', '.')  # '1.200'
    return f"{neg}R$ {milhar},{dec}"


def normalize_money(texto: str) -> Optional[Decimal]:
    """
    Converte strings monetárias para Decimal.

    Args:
        texto: String contendo valor monetário

    Returns:
        Decimal normalizado ou None
    """
    if not texto:
        return None

    # Remove símbolos não numéricos (mantém dígitos, vírgula, ponto e sinal)
    s = re.sub(r'[^\d,.\-]', '', texto).strip()
    if not s:
        return None

    last_dot = s.rfind('.')
    last_comma = s.rfind(',')

    if last_dot != -1 and last_comma != -1:
        # Dois separadores: o último é o decimal
        decimal_sep = '.' if last_dot > last_comma else ','
        thousands_sep = ',' if decimal_sep == '.' else '.'
        s = s.replace(thousands_sep, '')
        s = s.replace(decimal_sep, '.')
    else:
        # Só vírgula: decimal pt-BR
        if ',' in s and '.' not in s:
            s = s.replace(',', '.')
        # Só ponto: já é decimal; nenhum separador: inteiro

    # Valida padrão numérico final
    if not re.fullmatch(r'-?\d+(?:\.\d+)?', s):
        return None

    try:
        return Decimal(s)
    except Exception:
        return None

def get_vehicle_color(name: str, mapeamento_cores: dict = None) -> str:
    """Retorna a cor vinda do mapeamento dinâmico ou cinza por padrão."""
    if mapeamento_cores and name in mapeamento_cores:
        return mapeamento_cores[name]
    return "#808080"  # Cor neutra caso o tipo não tenha sido mapeado


def adjust_color_brightness(hex_color: str, factor: float) -> str:
    """
    Auxiliar para clarear ou escurecer uma cor hex.
    factor: 0.0 (mantém igual) a 1.0 (fica muito mais claro)
    """
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    # Mistura a cor com branco (255) baseado no fator
    new_rgb = [int(c + (255 - c) * (1 - factor)) for c in rgb]
    return '#{:02x}{:02x}{:02x}'.format(*new_rgb)


def get_vehicle_marker_color(name: str, index: int, total: int, mapeamento_cores: dict = None) -> str:
    """Calcula o degradê baseado na cor base fornecida pelo dicionário dinâmico."""
    base_color = get_vehicle_color(name, mapeamento_cores)
    # Lógica de brilho (degradê)
    factor = 0.3 + (0.7 * (index / (total - 1))) if total > 1 else 1.0
    return adjust_color_brightness(base_color, factor)

def extract_vehicle_from_name(nome: str) -> Optional[str]:
    """
    Extrai nome do veículo do nome do checkpoint.

    Args:
        nome: Nome do checkpoint

    Returns:
        Nome do veículo extraído ou None
    """
    import re

    patterns = [
        r've[ií]culo\s*(\d+)',
        r'v[ea]?\s*(\d+)',
        r'carro\s*(\d+)',
        r'vehicle\s*(\d+)',
        r'auto\s*(\d+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, nome, re.IGNORECASE)
        if match:
            return f"Veículo {match.group(1)}"

    return None