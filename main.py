
import os
import random
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from pathlib import Path
import threading
import queue
import json

EXTENSOES_FOTOS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp",
    ".gif", ".tif", ".tiff", ".jfif", ".avif",
    ".heic", ".heif"
}

EXTENSOES_VIDEOS = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv",
    ".flv", ".webm", ".m4v", ".mpeg", ".mpg",
    ".3gp", ".mts", ".m2ts"
}

EXTENSOES = EXTENSOES_FOTOS | EXTENSOES_VIDEOS


class SorteadorFotos:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("Sorteador de Fotos")
        self.janela.geometry("720x540")
        self.janela.minsize(620, 500)
        self.janela.configure(bg="#f3f5fa")

        self.origem = tk.StringVar()
        self.destino = tk.StringVar()
        self.historico = None
        self.quantidade = tk.StringVar(value="100")
        self.status = tk.StringVar(value="Escolha a pasta que contém suas fotos.")
        self.total = tk.StringVar(value="Nenhuma pasta selecionada")

        self.eventos = queue.Queue()
        self.ocupado = False

        self.criar_interface()
        self.janela.after(100, self.verificar_eventos)

    def criar_interface(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("TFrame", background="#ffffff")
        estilo.configure(
            "Titulo.TLabel",
            font=("Segoe UI", 22, "bold"),
            background="#f3f5fa",
            foreground="#172033"
        )
        estilo.configure(
            "Texto.TLabel",
            font=("Segoe UI", 10),
            background="#f3f5fa",
            foreground="#596579"
        )
        estilo.configure(
            "Card.TLabel",
            font=("Segoe UI", 11, "bold"),
            background="#ffffff",
            foreground="#172033"
        )
        estilo.configure("TButton", padding=8, font=("Segoe UI", 10))
        estilo.configure("TEntry", padding=8)
        estilo.configure("Horizontal.TProgressbar", thickness=12)

        principal = tk.Frame(self.janela, bg="#f3f5fa", padx=25, pady=22)
        principal.pack(fill="both", expand=True, pady=(0, 65))

        ttk.Label(
            principal,
            text="Sorteador de Fotos",
            style="Titulo.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            principal,
            text="Sorteie a quantidade exata de imagens que você quiser.",
            style="Texto.TLabel"
        ).pack(anchor="w", pady=(4, 18))

        cartao = ttk.Frame(principal, padding=18, style="TFrame")
        cartao.pack(fill="both", expand=True, pady=(0, 0))

        ttk.Label(
            cartao,
            text="1. Pasta com as fotos originais",
            style="Card.TLabel"
        ).pack(anchor="w")

        linha = ttk.Frame(cartao, style="TFrame")
        linha.pack(fill="x", pady=(8, 4))

        ttk.Entry(linha, textvariable=self.origem).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(
            linha, text="Procurar", command=self.escolher_origem
        ).pack(side="left", padx=(8, 0))

        ttk.Label(
            cartao, textvariable=self.total, style="Card.TLabel"
        ).pack(anchor="w", pady=(0, 18))

        ttk.Label(
            cartao,
            text="2. Quantas fotos deseja sortear?",
            style="Card.TLabel"
        ).pack(anchor="w")

        ttk.Entry(
            cartao, textvariable=self.quantidade, width=18
        ).pack(anchor="w", pady=(8, 18))

        ttk.Label(
            cartao,
            text="3. Pasta para salvar as fotos sorteadas",
            style="Card.TLabel"
        ).pack(anchor="w")

        linha_destino = ttk.Frame(cartao, style="TFrame")
        linha_destino.pack(fill="x", pady=(8, 6))

        ttk.Entry(
            linha_destino, textvariable=self.destino
        ).pack(side="left", fill="x", expand=True)

        ttk.Button(
            linha_destino,
            text="Escolher",
            command=self.escolher_destino
        ).pack(side="left", padx=(8, 0))

        tk.Label(
            cartao,
            text="Os arquivos originais não serão alterados nem apagados.",
            bg="#ffffff",
            fg="#667085",
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(0, 15))

        self.barra = ttk.Progressbar(
            cartao, mode="determinate", maximum=100
        )
        self.barra.pack(fill="x", pady=(0, 8))

        tk.Label(
            cartao,
            textvariable=self.status,
            bg="#ffffff",
            fg="#596579",
            font=("Segoe UI", 9),
            wraplength=620
        ).pack(anchor="w")

        botoes = ttk.Frame(self.janela)
        botoes.pack(fill="x", side="bottom", padx=25, pady=15)

        self.botao_sortear = ttk.Button(
            botoes,
            text="SORTEAR E COPIAR FOTOS",
            command=self.sortear
        )
        self.botao_sortear.pack(side="left")

        ttk.Button(
            botoes,
            text="Limpar",
            command=self.limpar
        ).pack(side="left", padx=10)

    def escolher_origem(self):
        pasta = filedialog.askdirectory(
            title="Selecione a pasta das fotos ou vídeos"
        )

        if not pasta:
            return

        self.origem.set(pasta)

        nome_pasta = Path(pasta).name.lower()

        if "foto" in nome_pasta:
            nome_destino = "Fotos sorteadas"
        elif "video" in nome_pasta or "vídeo" in nome_pasta:
            nome_destino = "Vídeos sorteados"
        else:
            nome_destino = f"{Path(pasta).name} sorteados"

        self.destino.set(
            str(Path(pasta).parent / nome_destino)
        )

        self.contar_fotos()


    def escolher_destino(self):
        pasta = filedialog.askdirectory(
            title="Selecione a pasta de destino"
        )

        if pasta:
            self.destino.set(pasta)

    @staticmethod
    def encontrar_fotos(pasta):
        return [
            arquivo for arquivo in Path(pasta).iterdir()
            if arquivo.is_file()
            and arquivo.suffix.lower() in EXTENSOES
        ]

    def contar_fotos(self):
        try:
            fotos = self.encontrar_fotos(self.origem.get())
            self.total.set(f"{len(fotos)} imagem(ns) encontrada(s)")
        except (OSError, ValueError):
            self.total.set("Não foi possível ler essa pasta")

    def carregar_historico(self, arquivo):
        if not arquivo.exists():
            return set()

        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)

        return set(dados)

    def salvar_historico(self, arquivo, dados):
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(sorted(dados), f, ensure_ascii=False, indent=4)
    def sortear(self):
        if self.ocupado:
            return

        origem = self.origem.get().strip()
        destino = self.destino.get().strip()

        if not origem or not os.path.isdir(origem):
            messagebox.showerror(
                "Erro", "Selecione uma pasta de origem válida."
            )
            return

        if not destino:
            messagebox.showerror(
                "Erro", "Escolha a pasta de destino."
            )
            return

        try:
            quantidade = int(self.quantidade.get())
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Quantidade inválida",
                "Digite um número inteiro maior que zero."
            )
            return

        origem_real = os.path.normcase(os.path.abspath(origem))
        destino_real = os.path.normcase(os.path.abspath(destino))

        if origem_real == destino_real:
            messagebox.showerror(
                "Destino inválido",
                "A pasta de destino precisa ser diferente da original."
            )
            return

        try:
            if os.path.commonpath(
                [origem_real, destino_real]
            ) == origem_real:
                messagebox.showerror(
                    "Destino inválido",
                    "Escolha uma pasta de destino fora da pasta original."
                )
                return
        except ValueError:
            pass

        try:
            fotos = self.encontrar_fotos(origem)

            arquivo_historico = Path(destino) / "historico_sorteios.json"
            historico = self.carregar_historico(arquivo_historico)

            fotos_disponiveis = [
                foto for foto in fotos
                if str(foto.resolve()) not in historico
            ]

        except (OSError, ValueError, json.JSONDecodeError) as erro:
            messagebox.showerror("Erro", f"Não foi possível ler o histórico:\n{erro}")
            return

        if quantidade > len(fotos_disponiveis):
            messagebox.showwarning(
                "Fotos insuficientes",
                f"Você pediu {quantidade} fotos, mas restam apenas "
                f"{len(fotos_disponiveis)} fotos ainda não sorteadas."
            )
            return

        self.ocupado = True
        self.botao_sortear.configure(state="disabled")
        self.barra["value"] = 0
        self.status.set("Preparando o sorteio...")

        threading.Thread(
            target=self.copiar_fotos,
            args=(fotos_disponiveis, quantidade, destino, arquivo_historico),
            daemon=True
        ).start()


    def copiar_fotos(self, fotos, quantidade, destino, arquivo_historico):
        try:
            selecionadas = random.sample(fotos, quantidade)

            historico = self.carregar_historico(arquivo_historico)

            pasta_destino = Path(destino)
            pasta_destino.mkdir(parents=True, exist_ok=True)

            nome = datetime.now().strftime("Sorteio_%Y-%m-%d_%H-%M-%S")
            saida = pasta_destino / nome
            contador = 1

            while saida.exists():
                saida = pasta_destino / f"{nome}_{contador}"
                contador += 1

            saida.mkdir()

            for numero, foto in enumerate(selecionadas, start=1):
                shutil.copy2(foto, saida / foto.name)

                historico.add(str(foto.resolve()))
                self.salvar_historico(arquivo_historico, historico)

                self.eventos.put(
                    ("progresso", numero, quantidade, foto.name)
                )

            self.eventos.put(("concluido", str(saida), quantidade))

        except Exception as erro:
            self.eventos.put(("erro", str(erro)))


    def verificar_eventos(self):
        try:
            while True:
                evento = self.eventos.get_nowait()

                if evento[0] == "progresso":
                    _, numero, total, nome = evento
                    self.barra["value"] = numero * 100 / total
                    self.status.set(
                        f"Copiando {numero} de {total}: {nome}"
                    )

                elif evento[0] == "concluido":
                    _, pasta, total = evento
                    self.ocupado = False
                    self.botao_sortear.configure(state="normal")
                    self.barra["value"] = 100
                    self.status.set(
                        f"Concluído! {total} fotos copiadas."
                    )

                    messagebox.showinfo(
                        "Sorteio concluído",
                        f"Foram copiadas exatamente {total} fotos!\n\n"
                        f"Pasta criada:\n{pasta}\n\n"
                        "As fotos originais continuam intactas."
                    )

                elif evento[0] == "erro":
                    self.ocupado = False
                    self.botao_sortear.configure(state="normal")
                    self.status.set("Ocorreu um erro.")
                    messagebox.showerror("Erro ao copiar", evento[1])

        except queue.Empty:
            pass

        self.janela.after(100, self.verificar_eventos)

    def limpar(self):
        if self.ocupado:
            messagebox.showinfo(
                "Aguarde", "Espere o sorteio terminar primeiro."
            )
            return

        self.origem.set("")
        self.destino.set("")
        self.quantidade.set("100")
        self.total.set("Nenhuma pasta selecionada")
        self.status.set("Escolha a pasta que contém suas fotos.")
        self.barra["value"] = 0


if __name__ == "__main__":
    janela = tk.Tk()
    janela.state("zoomed")  # Abre maximizado no Windows
    app = SorteadorFotos(janela)
    janela.mainloop()