#color_picker_ui.py

import tkinter as tk
from tkinter import colorchooser
from tkinter import ttk


class ColorPickerUI:
    def __init__(self, tipos_encontrados):
        self.root = tk.Tk()
        self.root.title("Configuração de Cores - Mapa de Calor")
        self.root.state('zoomed')
        self.root.geometry("600x700")
        self.root.configure(bg='#f5f5f5')
        self.root.attributes("-topmost", True)

        self.tipos = sorted(tipos_encontrados)  # Ordena alfabeticamente
        self.resultado_cores = {}

        # Paleta de cores aprimorada
        self.cores_default = [
            "#2563eb", "#dc2626", "#16a34a", "#9333ea",
            "#ea580c", "#0891b2", "#ca8a04", "#db2777",
            "#0d9488", "#4f46e5", "#f59e0b", "#8b5cf6"
        ]

        self._criar_interface()

    def _criar_interface(self):
        # Cabeçalho
        header = tk.Frame(self.root, bg='#1e293b', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🎨 Configuração de Cores",
            font=("Segoe UI", 18, "bold"),
            bg='#1e293b',
            fg='white'
        ).pack(pady=8)

        tk.Label(
            header,
            text=f"Defina cores para {len(self.tipos)} categorias encontradas",
            font=("Segoe UI", 10),
            bg='#1e293b',
            fg='#94a3b8'
        ).pack()

        # Container principal com scroll
        main_container = tk.Frame(self.root, bg='#f5f5f5')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Canvas + Scrollbar
        canvas = tk.Canvas(main_container, bg='#f5f5f5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f5f5')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Barra de ações rápidas
        actions_frame = tk.Frame(scrollable_frame, bg='#ffffff', relief='solid', borderwidth=1)
        actions_frame.pack(fill='x', pady=(0, 15), padx=5)

        tk.Label(
            actions_frame,
            text="Ações Rápidas:",
            font=("Segoe UI", 9, "bold"),
            bg='#ffffff',
            fg='#475569'
        ).pack(side='left', padx=10, pady=8)

        tk.Button(
            actions_frame,
            text="🔄 Resetar Cores",
            command=self._resetar_cores,
            bg='#f1f5f9',
            fg='#475569',
            font=("Segoe UI", 9),
            relief='flat',
            cursor='hand2',
            padx=10,
            pady=5
        ).pack(side='left', padx=5)

        tk.Button(
            actions_frame,
            text="🎲 Cores Aleatórias",
            command=self._cores_aleatorias,
            bg='#f1f5f9',
            fg='#475569',
            font=("Segoe UI", 9),
            relief='flat',
            cursor='hand2',
            padx=10,
            pady=5
        ).pack(side='left', padx=5)

        # Lista de categorias
        self.botoes_cor = {}
        self.labels_hex = {}

        for i, tipo in enumerate(self.tipos):
            cor_inicial = self.cores_default[i % len(self.cores_default)]
            self.resultado_cores[tipo] = cor_inicial

            # Card para cada categoria
            card = tk.Frame(scrollable_frame, bg='#ffffff', relief='solid', borderwidth=1)
            card.pack(fill='x', pady=5, padx=5)

            # Container interno
            inner = tk.Frame(card, bg='#ffffff')
            inner.pack(fill='x', padx=15, pady=12)

            # Nome da categoria
            tk.Label(
                inner,
                text=tipo,
                font=("Segoe UI", 11),
                bg='#ffffff',
                fg='#1e293b',
                anchor='w',
                width=25
            ).pack(side='left')

            # Container para cor
            cor_container = tk.Frame(inner, bg='#ffffff')
            cor_container.pack(side='right')

            # Label com código hex
            lbl_hex = tk.Label(
                cor_container,
                text=cor_inicial,
                font=("Consolas", 9),
                bg='#f8fafc',
                fg='#64748b',
                width=10,
                relief='flat',
                padx=8,
                pady=4
            )
            lbl_hex.pack(side='right', padx=(10, 0))
            self.labels_hex[tipo] = lbl_hex

            # Botão de amostra de cor (maior e mais visível)
            btn_cor = tk.Button(
                cor_container,
                bg=cor_inicial,
                width=8,
                height=2,
                relief='solid',
                borderwidth=2,
                cursor='hand2',
                command=lambda t=tipo: self._escolher_cor(t)
            )
            btn_cor.pack(side='right')
            self.botoes_cor[tipo] = btn_cor

            # Efeito hover
            btn_cor.bind('<Enter>', lambda e, b=btn_cor: b.config(relief='raised'))
            btn_cor.bind('<Leave>', lambda e, b=btn_cor: b.config(relief='solid'))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Rodapé com botão de ação
        footer = tk.Frame(self.root, bg='#f5f5f5', height=80)
        footer.pack(fill='x', padx=20, pady=(0, 20))
        footer.pack_propagate(False)

        btn_gerar = tk.Button(
            footer,
            text="✓ Gerar Mapa de Calor",
            command=self.root.destroy,
            bg='#16a34a',
            fg='white',
            font=("Segoe UI", 12, "bold"),
            relief='flat',
            cursor='hand2',
            height=2
        )
        btn_gerar.pack(fill='x', pady=10)

        # Efeito hover no botão principal
        btn_gerar.bind('<Enter>', lambda e: btn_gerar.config(bg='#15803d'))
        btn_gerar.bind('<Leave>', lambda e: btn_gerar.config(bg='#16a34a'))

        # Atalhos de teclado
        self.root.bind('<Return>', lambda e: self.root.destroy())
        self.root.bind('<Escape>', lambda e: self.root.destroy())

        # Scroll com mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _escolher_cor(self, tipo):
        cor_atual = self.resultado_cores[tipo]
        resultado = colorchooser.askcolor(
            initialcolor=cor_atual,
            title=f"Escolher cor para '{tipo}'"
        )

        if resultado[1]:
            nova_cor = resultado[1]
            self.resultado_cores[tipo] = nova_cor
            self.botoes_cor[tipo].config(bg=nova_cor)
            self.labels_hex[tipo].config(text=nova_cor)

    def _resetar_cores(self):
        """Volta às cores padrão"""
        for i, tipo in enumerate(self.tipos):
            cor = self.cores_default[i % len(self.cores_default)]
            self.resultado_cores[tipo] = cor
            self.botoes_cor[tipo].config(bg=cor)
            self.labels_hex[tipo].config(text=cor)

    def _cores_aleatorias(self):
        """Gera cores aleatórias para todas as categorias"""
        import random
        for tipo in self.tipos:
            cor = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            self.resultado_cores[tipo] = cor
            self.botoes_cor[tipo].config(bg=cor)
            self.labels_hex[tipo].config(text=cor)

    def get_colors(self):
        self.root.mainloop()
        return self.resultado_cores


# Exemplo de uso
if __name__ == "__main__":
    tipos_teste = ["Residencial", "Comercial", "Industrial", "Área Verde", "Institucional"]
    picker = ColorPickerUI(tipos_teste)
    cores = picker.get_colors()
    print("Cores selecionadas:", cores)