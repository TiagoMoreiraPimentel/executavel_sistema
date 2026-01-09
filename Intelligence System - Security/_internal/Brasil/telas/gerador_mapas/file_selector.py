import tkinter as tk
from tkinter import filedialog
import os
from typing import Optional

class FileSelector:
    @staticmethod
    def select_excel() -> Optional[str]:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo Excel",
            filetypes=[("Arquivos Excel", "*.xlsx *.xls")]
        )
        root.destroy()
        return file_path if file_path else None

    @staticmethod
    def save_file_dest(sugestao_nome: str) -> Optional[str]:
        """Abre janela para o usuário escolher onde salvar o arquivo final."""
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.asksaveasfilename(
            title="Onde deseja salvar o mapa?",
            initialfile=sugestao_nome,
            defaultextension=".html",
            filetypes=[("Arquivo HTML", "*.html")]
        )
        root.destroy()
        return path if path else None