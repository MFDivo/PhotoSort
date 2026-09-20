import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, scrolledtext, ttk

from .config import LANGUAGE_ORDER, TRADUCOES
from .core import organizar


class TelaIdioma(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Language / Idioma")
        self.resizable(False, False)
        self._idioma_selecionado = None
        self._construir()
        self._centralizar(420, 340)

    def _centralizar(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry("{}x{}+{}+{}".format(w, h, x, y))

    def _construir(self):
        tk.Label(self, text="Select Language", font=("Helvetica", 15, "bold"), pady=10).pack(pady=(20, 4))
        tk.Label(self, text="Choose the interface language:", font=("Helvetica", 10), fg="#555555").pack(pady=(0, 16))

        frame = tk.Frame(self)
        frame.pack()

        cores = {
            "en": ("#1d4ed8", "white"),
            "es": ("#b91c1c", "white"),
            "ru": ("#15803d", "white"),
            "zh": ("#b45309", "white"),
        }

        for i, lang in enumerate(LANGUAGE_ORDER):
            tr = TRADUCOES[lang]
            bg, fg = cores[lang]
            btn = tk.Button(
                frame,
                text="[{}]  {}".format(tr["flag"], tr["lang_name"]),
                font=("Helvetica", 13),
                bg=bg,
                fg=fg,
                activebackground=bg,
                activeforeground=fg,
                relief="flat",
                padx=24,
                pady=10,
                cursor="hand2",
                width=20,
                command=lambda l=lang: self._selecionar(l),
            )
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=8)

    def _selecionar(self, lang):
        self._idioma_selecionado = lang
        self.destroy()

    def obter_idioma(self):
        self.mainloop()
        return self._idioma_selecionado


class App(tk.Tk):
    def __init__(self, idioma):
        super().__init__()
        self.t = TRADUCOES[idioma]
        self.title(self.t["app_title"])
        self.resizable(True, True)
        self.minsize(700, 580)
        self._fila_msgs = queue.Queue()
        self._fila_progresso = queue.Queue()
        self._construir_interface()
        self._centralizar(760, 620)

    def _centralizar(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry("{}x{}+{}+{}".format(w, h, x, y))

    def _construir_interface(self):
        t = self.t
        pad = {"padx": 12, "pady": 6}

        tk.Label(self, text=t["app_title"], font=("Helvetica", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=(16, 8))
        tk.Label(self, text=t["origin"]).grid(row=1, column=0, sticky="e", **pad)
        self._var_origem = tk.StringVar()
        tk.Entry(self, textvariable=self._var_origem, width=52).grid(row=1, column=1, sticky="ew", **pad)
        tk.Button(self, text=t["browse"], command=self._escolher_origem).grid(row=1, column=2, **pad)

        tk.Label(self, text=t["destination"]).grid(row=2, column=0, sticky="e", **pad)
        self._var_destino = tk.StringVar()
        tk.Entry(self, textvariable=self._var_destino, width=52).grid(row=2, column=1, sticky="ew", **pad)
        tk.Button(self, text=t["browse"], command=self._escolher_destino).grid(row=2, column=2, **pad)

        self._var_origem.trace_add("write", self._atualizar_destino_padrao)

        self._var_dry_run = tk.BooleanVar(value=True)
        tk.Checkbutton(self, text=t["dry_run"], variable=self._var_dry_run).grid(row=3, column=0, columnspan=3, sticky="w", padx=14, pady=(4, 0))

        self._var_copiar = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text=t["copy_instead"], variable=self._var_copiar).grid(row=4, column=0, columnspan=3, sticky="w", padx=14, pady=(0, 2))

        self._btn_organizar = tk.Button(
            self,
            text=t["organize"],
            font=("Helvetica", 13, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._iniciar_organizacao,
        )
        self._btn_organizar.grid(row=5, column=0, columnspan=3, pady=(10, 6))

        frame_prog = tk.Frame(self)
        frame_prog.grid(row=6, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 2))
        frame_prog.columnconfigure(0, weight=1)

        self._var_progresso = tk.DoubleVar(value=0)
        self._barra = ttk.Progressbar(frame_prog, variable=self._var_progresso, maximum=100, length=400)
        self._barra.grid(row=0, column=0, sticky="ew")

        self._label_progresso = tk.Label(frame_prog, text="0%  (0 / 0)  ETA: --:--:--", width=34)
        self._label_progresso.grid(row=0, column=1, padx=(8, 0))

        self._var_status = tk.StringVar(value=t["waiting"])
        tk.Label(self, textvariable=self._var_status, anchor="w", fg="#555555").grid(row=7, column=0, columnspan=3, sticky="ew", padx=14)

        tk.Label(self, text=t["log"], anchor="w").grid(row=8, column=0, columnspan=3, sticky="w", padx=14)

        self._log = scrolledtext.ScrolledText(self, height=14, state="disabled", wrap="word", font=("Courier", 10))
        self._log.grid(row=9, column=0, columnspan=3, sticky="nsew", padx=12, pady=(0, 12))

        self.columnconfigure(1, weight=1)
        self.rowconfigure(9, weight=1)

    def _escolher_origem(self):
        pasta = filedialog.askdirectory(title=self.t["select_origin"])
        if pasta:
            self._var_origem.set(pasta)

    def _escolher_destino(self):
        pasta = filedialog.askdirectory(title=self.t["select_dest"])
        if pasta:
            self._var_destino.set(pasta)

    def _atualizar_destino_padrao(self, *_):
        origem = self._var_origem.get().strip()
        if origem and not self._var_destino.get().strip():
            self._var_destino.set(origem.rstrip("/\\") + "_organizado")

    def _iniciar_organizacao(self):
        t = self.t
        origem = self._var_origem.get().strip()
        destino = self._var_destino.get().strip()

        if not origem:
            self._log_append(t["err_origin"])
            return
        if not Path(origem).is_dir():
            self._log_append(t["err_origin_nf"].format(origem))
            return
        if not destino:
            self._log_append(t["err_dest"])
            return

        self._log.config(state="normal")
        self._log.delete("1.0", tk.END)
        self._log.config(state="disabled")
        self._var_progresso.set(0)
        self._label_progresso.config(text="0%  (0 / 0)  ETA: --:--:--")
        self._var_status.set(t["starting"])
        self._btn_organizar.config(state="disabled")

        dry_run = self._var_dry_run.get()
        copiar = self._var_copiar.get()

        if dry_run:
            modo = t["sim_label"]
        elif copiar:
            modo = t["copy_label"]
        else:
            modo = t["real_label"]

        self._log_append(t["init_log"].format(modo))
        self._log_append(t["origin_log"].format(origem))
        self._log_append(t["dest_log"].format(destino))
        self._log_append("-" * 60)

        while not self._fila_msgs.empty():
            self._fila_msgs.get_nowait()
        while not self._fila_progresso.empty():
            self._fila_progresso.get_nowait()

        thread = threading.Thread(
            target=organizar,
            args=(origem, destino, dry_run, copiar, self._fila_msgs, self._fila_progresso, t),
            daemon=True,
        )
        thread.start()
        self.after(100, self._processar_filas)

    def _processar_filas(self):
        encerrou = False
        try:
            while True:
                tipo, dados = self._fila_msgs.get_nowait()
                if tipo == "log":
                    self._log_append(dados)
                elif tipo == "status":
                    self._var_status.set(dados)
                elif tipo == "fim":
                    encerrou = True
                    self._var_status.set(self.t["done"])
                    self._btn_organizar.config(state="normal")
        except queue.Empty:
            pass

        try:
            while True:
                idx, total, eta_str = self._fila_progresso.get_nowait()
                pct = (idx / total * 100) if total > 0 else 0
                self._var_progresso.set(pct)
                self._label_progresso.config(text="{}%  ({} / {})  ETA: {}".format(int(pct), idx, total, eta_str))
        except queue.Empty:
            pass

        if not encerrou:
            self.after(100, self._processar_filas)

    def _log_append(self, texto):
        self._log.config(state="normal")
        self._log.insert(tk.END, texto + "\n")
        self._log.see(tk.END)
        self._log.config(state="disabled")


def main():
    tela_idioma = TelaIdioma()
    idioma = tela_idioma.obter_idioma()

    if idioma is None:
        import sys
        sys.exit(0)

    app = App(idioma)
    app.mainloop()


if __name__ == "__main__":
    main()
