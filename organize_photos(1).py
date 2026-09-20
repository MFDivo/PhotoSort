"""
Organizador de Fotos e Videos
==============================
Organiza fotos e videos em subpastas <ANO>/<MES>/ com renomeacao sequencial.

Uso: python organize_photos.py

Dependencias: Pillow, exifread (pip install Pillow exifread)
"""

import os
import re
import shutil
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Tentativa de importar dependencias opcionais
# ---------------------------------------------------------------------------
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

try:
    import exifread
    EXIFREAD_OK = True
except ImportError:
    EXIFREAD_OK = False

# ---------------------------------------------------------------------------
# Traducoes
# ---------------------------------------------------------------------------
TRADUCOES = {
    "en": {
        "flag": "🇬🇧",
        "lang_name": "English",
        "app_title": "Photo and Video Organizer",
        "select_lang": "Select Language",
        "continue": "Continue",
        "origin": "Source folder:",
        "destination": "Destination folder:",
        "browse": "Browse",
        "dry_run": "Simulate before moving (Dry Run)",
        "organize": "ORGANIZE",
        "log": "Log:",
        "waiting": "Waiting...",
        "done": "Done!",
        "starting": "Starting...",
        "processing": "Processing: {}",
        "no_files": "No supported files found in source folder.",
        "total_found": "Total files found: {}",
        "summary": "SUMMARY",
        "total_processed": "  Total processed : {}",
        "total_ignored": "  Total ignored   : {}",
        "no_date": "  No date         : {}",
        "sim_mode": "  SIMULATION mode - no files were moved.",
        "init_log": "Starting organization [{}]",
        "sim_label": "SIMULATION",
        "real_label": "REAL EXECUTION",
        "origin_log": "Source : {}",
        "dest_log": "Destination: {}",
        "moved": "[MOVED]",
        "simulated": "[SIMULATION]",
        "error": "[ERROR]",
        "err_origin": "[ERROR] Please set the source folder.",
        "err_origin_nf": "[ERROR] Source folder not found: {}",
        "err_dest": "[ERROR] Please set the destination folder.",
        "err_move": "[ERROR] Could not move {}: {}",
        "select_origin": "Select source folder",
        "select_dest": "Select destination folder",
        "no_date_folder": "no_date",
        "months": {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December",
        },
    },
    "es": {
        "flag": "🇪🇸",
        "lang_name": "Español",
        "app_title": "Organizador de Fotos y Videos",
        "select_lang": "Seleccionar Idioma",
        "continue": "Continuar",
        "origin": "Carpeta de origen:",
        "destination": "Carpeta de destino:",
        "browse": "Explorar",
        "dry_run": "Simular antes de mover (Dry Run)",
        "organize": "ORGANIZAR",
        "log": "Registro:",
        "waiting": "Esperando...",
        "done": "¡Completado!",
        "starting": "Iniciando...",
        "processing": "Procesando: {}",
        "no_files": "No se encontraron archivos compatibles en la carpeta de origen.",
        "total_found": "Total de archivos encontrados: {}",
        "summary": "RESUMEN",
        "total_processed": "  Total procesados : {}",
        "total_ignored": "  Total ignorados  : {}",
        "no_date": "  Sin fecha        : {}",
        "sim_mode": "  Modo SIMULACION - ningun archivo fue movido.",
        "init_log": "Iniciando organizacion [{}]",
        "sim_label": "SIMULACION",
        "real_label": "EJECUCION REAL",
        "origin_log": "Origen : {}",
        "dest_log": "Destino: {}",
        "moved": "[MOVIDO]",
        "simulated": "[SIMULACION]",
        "error": "[ERROR]",
        "err_origin": "[ERROR] Indique la carpeta de origen.",
        "err_origin_nf": "[ERROR] Carpeta de origen no encontrada: {}",
        "err_dest": "[ERROR] Indique la carpeta de destino.",
        "err_move": "[ERROR] No se pudo mover {}: {}",
        "select_origin": "Seleccione la carpeta de origen",
        "select_dest": "Seleccione la carpeta de destino",
        "no_date_folder": "sin_fecha",
        "months": {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
        },
    },
    "ru": {
        "flag": "🇷🇺",
        "lang_name": "Русский",
        "app_title": "Органайзер фото и видео",
        "select_lang": "Выбор языка",
        "continue": "Продолжить",
        "origin": "Исходная папка:",
        "destination": "Папка назначения:",
        "browse": "Обзор",
        "dry_run": "Симуляция перед перемещением (Dry Run)",
        "organize": "ОРГАНИЗОВАТЬ",
        "log": "Журнал:",
        "waiting": "Ожидание...",
        "done": "Готово!",
        "starting": "Запуск...",
        "processing": "Обработка: {}",
        "no_files": "Поддерживаемые файлы не найдены в исходной папке.",
        "total_found": "Всего найдено файлов: {}",
        "summary": "ИТОГ",
        "total_processed": "  Обработано  : {}",
        "total_ignored": "  Пропущено   : {}",
        "no_date": "  Без даты    : {}",
        "sim_mode": "  Режим СИМУЛЯЦИИ - файлы не перемещались.",
        "init_log": "Запуск организации [{}]",
        "sim_label": "СИМУЛЯЦИЯ",
        "real_label": "РЕАЛЬНЫЙ ЗАПУСК",
        "origin_log": "Источник : {}",
        "dest_log": "Назначение: {}",
        "moved": "[ПЕРЕМЕЩЕНО]",
        "simulated": "[СИМУЛЯЦИЯ]",
        "error": "[ОШИБКА]",
        "err_origin": "[ОШИБКА] Укажите исходную папку.",
        "err_origin_nf": "[ОШИБКА] Исходная папка не найдена: {}",
        "err_dest": "[ОШИБКА] Укажите папку назначения.",
        "err_move": "[ОШИБКА] Не удалось переместить {}: {}",
        "select_origin": "Выберите исходную папку",
        "select_dest": "Выберите папку назначения",
        "no_date_folder": "bez_daty",
        "months": {
            1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
            5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
            9: "Sentyabr", 10: "Oktyabr", 11: "Noyabr", 12: "Dekabr",
        },
    },
    "zh": {
        "flag": "🇨🇳",
        "lang_name": "中文",
        "app_title": "照片和视频整理器",
        "select_lang": "选择语言",
        "continue": "继续",
        "origin": "源文件夹:",
        "destination": "目标文件夹:",
        "browse": "浏览",
        "dry_run": "移动前模拟运行 (Dry Run)",
        "organize": "整理",
        "log": "日志:",
        "waiting": "等待中...",
        "done": "完成！",
        "starting": "启动中...",
        "processing": "正在处理: {}",
        "no_files": "在源文件夹中未找到支持的文件。",
        "total_found": "共找到文件: {}",
        "summary": "摘要",
        "total_processed": "  已处理 : {}",
        "total_ignored": "  已忽略 : {}",
        "no_date": "  无日期 : {}",
        "sim_mode": "  模拟模式 - 没有文件被移动。",
        "init_log": "开始整理 [{}]",
        "sim_label": "模拟",
        "real_label": "实际执行",
        "origin_log": "来源 : {}",
        "dest_log": "目标: {}",
        "moved": "[已移动]",
        "simulated": "[模拟]",
        "error": "[错误]",
        "err_origin": "[错误] 请设置源文件夹。",
        "err_origin_nf": "[错误] 未找到源文件夹: {}",
        "err_dest": "[错误] 请设置目标文件夹。",
        "err_move": "[错误] 无法移动 {}: {}",
        "select_origin": "选择源文件夹",
        "select_dest": "选择目标文件夹",
        "no_date_folder": "sem_data",
        "months": {
            1: "Yiyue", 2: "Eryue", 3: "Sanyue", 4: "Siyue",
            5: "Wuyue", 6: "Liuyue", 7: "Qiyue", 8: "Bayue",
            9: "Jiuyue", 10: "Shiyue", 11: "Shiyiyue", 12: "Shi'eryue",
        },
    },
}

LANGUAGE_ORDER = ["en", "es", "ru", "zh"]

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
EXTENSOES_IMAGEM = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp",
    ".tiff", ".tif", ".webp", ".heic",
    ".cr2", ".nef", ".arw", ".dng", ".raw",
}

EXTENSOES_VIDEO = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv",
    ".m4v", ".3gp", ".flv",
}

EXTENSOES_SUPORTADAS = EXTENSOES_IMAGEM | EXTENSOES_VIDEO

PADROES_DATA_NOME = [
    re.compile(r'(?<!\d)(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)'),
    re.compile(r'(20\d{2})[-_](0[1-9]|1[0-2])[-_](0[1-9]|[12]\d|3[01])'),
]

# ---------------------------------------------------------------------------
# Logica de negocio - deteccao de data
# ---------------------------------------------------------------------------

def extrair_data_exif_pillow(caminho):
    if not PILLOW_OK:
        return None
    try:
        img = Image.open(caminho)
        exif_data = img._getexif()
        if not exif_data:
            return None
        for tag_id, valor in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal":
                return datetime.strptime(str(valor), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def extrair_data_exif_exifread(caminho):
    if not EXIFREAD_OK:
        return None
    try:
        with open(caminho, "rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal", details=False)
        chave = "EXIF DateTimeOriginal"
        if chave in tags:
            valor = str(tags[chave])
            return datetime.strptime(valor, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def extrair_data_nome(nome_arquivo):
    for padrao in PADROES_DATA_NOME:
        m = padrao.search(nome_arquivo)
        if m:
            try:
                ano, mes, dia = int(m.group(1)), int(m.group(2)), int(m.group(3))
                return datetime(ano, mes, dia)
            except ValueError:
                continue
    return None


def extrair_data_modificacao(caminho):
    try:
        ts = os.path.getmtime(caminho)
        return datetime.fromtimestamp(ts)
    except Exception:
        return None


def detectar_data(caminho):
    nome = os.path.basename(caminho)
    ext = Path(caminho).suffix.lower()

    if ext in EXTENSOES_IMAGEM:
        dt = extrair_data_exif_pillow(caminho)
        if dt:
            return dt, "EXIF (Pillow)"
        dt = extrair_data_exif_exifread(caminho)
        if dt:
            return dt, "EXIF (exifread)"

    dt = extrair_data_nome(nome)
    if dt:
        return dt, "nome do arquivo"

    dt = extrair_data_modificacao(caminho)
    if dt:
        return dt, "data de modificacao"

    return None, "nenhuma"


# ---------------------------------------------------------------------------
# Logica de negocio - organizacao
# ---------------------------------------------------------------------------

def listar_arquivos(pasta_origem):
    arquivos = []
    for raiz, _, nomes in os.walk(pasta_origem):
        for nome in nomes:
            ext = Path(nome).suffix.lower()
            if ext in EXTENSOES_SUPORTADAS:
                arquivos.append(os.path.join(raiz, nome))
    return arquivos


def gerar_nome_destino(pasta_destino, mes_nome, ano, ext, contadores):
    chave = os.path.join(pasta_destino, str(ano), mes_nome)
    if chave not in contadores:
        n = 1
        if os.path.isdir(chave):
            existentes = os.listdir(chave)
            padrao_n = re.compile(
                r'^' + re.escape(mes_nome) + r'_' + re.escape(str(ano)) + r'_(\d+)\.',
                re.IGNORECASE,
            )
            for arq in existentes:
                m = padrao_n.match(arq)
                if m:
                    n = max(n, int(m.group(1)) + 1)
        contadores[chave] = n

    n = contadores[chave]
    nome_base = "{}_{}_{}{}" .format(mes_nome, ano, n, ext)
    caminho_completo = os.path.join(chave, nome_base)

    while os.path.exists(caminho_completo):
        n += 1
        nome_base = "{}_{}_{}{}" .format(mes_nome, ano, n, ext)
        caminho_completo = os.path.join(chave, nome_base)

    contadores[chave] = n + 1
    return caminho_completo


def organizar(pasta_origem, pasta_destino, dry_run, fila_msgs, fila_progresso, t):
    arquivos = listar_arquivos(pasta_origem)
    total = len(arquivos)

    if total == 0:
        fila_msgs.put(("log", t["no_files"]))
        fila_msgs.put(("fim", (0, 0, 0)))
        return

    fila_msgs.put(("log", t["total_found"].format(total)))
    fila_progresso.put((0, total))

    contadores = {}
    processados = 0
    ignorados = 0
    sem_data = 0

    for idx, caminho_orig in enumerate(arquivos, start=1):
        nome_orig = os.path.basename(caminho_orig)
        fila_msgs.put(("status", t["processing"].format(nome_orig)))

        ext = Path(caminho_orig).suffix.lower()
        dt, fonte = detectar_data(caminho_orig)

        if dt is None:
            pasta_sd = os.path.join(pasta_destino, t["no_date_folder"])
            destino = os.path.join(pasta_sd, nome_orig)
            if os.path.exists(destino):
                base, extensao = os.path.splitext(nome_orig)
                contador_sd = 1
                while os.path.exists(destino):
                    destino = os.path.join(pasta_sd, "{}_{}{}" .format(base, contador_sd, extensao))
                    contador_sd += 1
            sem_data += 1
        else:
            mes_nome = t["months"][dt.month]
            ano = dt.year
            destino = gerar_nome_destino(pasta_destino, mes_nome, ano, ext, contadores)

        prefixo = t["simulated"] if dry_run else t["moved"]
        fila_msgs.put(("log", "{}  {}  ->  {}  (data: {})".format(prefixo, caminho_orig, destino, fonte)))

        if not dry_run:
            try:
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                shutil.move(caminho_orig, destino)
                processados += 1
            except Exception as e:
                fila_msgs.put(("log", t["err_move"].format(nome_orig, e)))
                ignorados += 1
        else:
            processados += 1

        fila_progresso.put((idx, total))

    fila_msgs.put(("log", ""))
    fila_msgs.put(("log", "=" * 60))
    fila_msgs.put(("log", t["summary"]))
    fila_msgs.put(("log", t["total_processed"].format(processados)))
    fila_msgs.put(("log", t["total_ignored"].format(ignorados)))
    fila_msgs.put(("log", t["no_date"].format(sem_data)))
    if dry_run:
        fila_msgs.put(("log", t["sim_mode"]))
    fila_msgs.put(("log", "=" * 60))
    fila_msgs.put(("fim", (processados, ignorados, sem_data)))


# ---------------------------------------------------------------------------
# Tela de selecao de idioma
# ---------------------------------------------------------------------------

class TelaIdioma(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Language / Idioma / Язык / 语言")
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
        # Titulo
        tk.Label(
            self,
            text="🌐  Select Language",
            font=("Helvetica", 15, "bold"),
            pady=10,
        ).pack(pady=(20, 4))

        tk.Label(
            self,
            text="Choose the interface language:",
            font=("Helvetica", 10),
            fg="#555555",
        ).pack(pady=(0, 16))

        # Botoes de idioma
        frame = tk.Frame(self)
        frame.pack()

        cores = {
            "en": ("#1d4ed8", "white"),
            "es": ("#b91c1c", "white"),
            "ru": ("#15803d", "white"),
            "zh": ("#b45309", "white"),
        }

        for i, lang in enumerate(LANGUAGE_ORDER):
            t = TRADUCOES[lang]
            bg, fg = cores[lang]
            btn = tk.Button(
                frame,
                text="{}  {}".format(t["flag"], t["lang_name"]),
                font=("Helvetica", 13),
                bg=bg,
                fg=fg,
                activebackground=bg,
                activeforeground=fg,
                relief="flat",
                padx=24,
                pady=10,
                cursor="hand2",
                width=18,
                command=lambda l=lang: self._selecionar(l),
            )
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=8)

    def _selecionar(self, lang):
        self._idioma_selecionado = lang
        self.destroy()

    def obter_idioma(self):
        self.mainloop()
        return self._idioma_selecionado


# ---------------------------------------------------------------------------
# Interface principal
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self, idioma):
        super().__init__()
        self.t = TRADUCOES[idioma]
        self.title(self.t["app_title"])
        self.resizable(True, True)
        self.minsize(680, 520)
        self._fila_msgs = queue.Queue()
        self._fila_progresso = queue.Queue()
        self._construir_interface()
        self._centralizar(720, 560)

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

        # Titulo
        tk.Label(
            self,
            text=t["app_title"],
            font=("Helvetica", 16, "bold"),
        ).grid(row=0, column=0, columnspan=3, pady=(16, 8))

        # Pasta de origem
        tk.Label(self, text=t["origin"]).grid(row=1, column=0, sticky="e", **pad)
        self._var_origem = tk.StringVar()
        tk.Entry(self, textvariable=self._var_origem, width=50).grid(row=1, column=1, sticky="ew", **pad)
        tk.Button(self, text=t["browse"], command=self._escolher_origem).grid(row=1, column=2, **pad)

        # Pasta de destino
        tk.Label(self, text=t["destination"]).grid(row=2, column=0, sticky="e", **pad)
        self._var_destino = tk.StringVar()
        tk.Entry(self, textvariable=self._var_destino, width=50).grid(row=2, column=1, sticky="ew", **pad)
        tk.Button(self, text=t["browse"], command=self._escolher_destino).grid(row=2, column=2, **pad)

        self._var_origem.trace_add("write", self._atualizar_destino_padrao)

        # Checkbox dry run
        self._var_dry_run = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self,
            text=t["dry_run"],
            variable=self._var_dry_run,
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=14, pady=(4, 2))

        # Botao organizar
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
        self._btn_organizar.grid(row=4, column=0, columnspan=3, pady=(10, 6))

        # Barra de progresso
        frame_prog = tk.Frame(self)
        frame_prog.grid(row=5, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 2))
        frame_prog.columnconfigure(0, weight=1)

        self._var_progresso = tk.DoubleVar(value=0)
        self._barra = ttk.Progressbar(
            frame_prog,
            variable=self._var_progresso,
            maximum=100,
            length=400,
        )
        self._barra.grid(row=0, column=0, sticky="ew")

        self._label_progresso = tk.Label(frame_prog, text="0%  (0 / 0)", width=24)
        self._label_progresso.grid(row=0, column=1, padx=(8, 0))

        # Label de status
        self._var_status = tk.StringVar(value=t["waiting"])
        tk.Label(
            self,
            textvariable=self._var_status,
            anchor="w",
            fg="#555555",
        ).grid(row=6, column=0, columnspan=3, sticky="ew", padx=14)

        # Area de log
        tk.Label(self, text=t["log"], anchor="w").grid(row=7, column=0, columnspan=3, sticky="w", padx=14)
        self._log = scrolledtext.ScrolledText(
            self,
            height=14,
            state="disabled",
            wrap="word",
            font=("Courier", 10),
        )
        self._log.grid(row=8, column=0, columnspan=3, sticky="nsew", padx=12, pady=(0, 12))

        self.columnconfigure(1, weight=1)
        self.rowconfigure(8, weight=1)

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
        if not os.path.isdir(origem):
            self._log_append(t["err_origin_nf"].format(origem))
            return
        if not destino:
            self._log_append(t["err_dest"])
            return

        self._log.config(state="normal")
        self._log.delete("1.0", tk.END)
        self._log.config(state="disabled")
        self._var_progresso.set(0)
        self._label_progresso.config(text="0%  (0 / 0)")
        self._var_status.set(t["starting"])

        self._btn_organizar.config(state="disabled")

        dry_run = self._var_dry_run.get()
        modo = t["sim_label"] if dry_run else t["real_label"]
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
            args=(origem, destino, dry_run, self._fila_msgs, self._fila_progresso, t),
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
                atual, total = self._fila_progresso.get_nowait()
                pct = (atual / total * 100) if total > 0 else 0
                self._var_progresso.set(pct)
                self._label_progresso.config(
                    text="{}%  ({} / {})".format(int(pct), atual, total)
                )
        except queue.Empty:
            pass

        if not encerrou:
            self.after(100, self._processar_filas)

    def _log_append(self, texto):
        self._log.config(state="normal")
        self._log.insert(tk.END, texto + "\n")
        self._log.see(tk.END)
        self._log.config(state="disabled")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tela_idioma = TelaIdioma()
    idioma = tela_idioma.obter_idioma()

    if idioma is None:
        # Usuario fechou a janela sem selecionar
        import sys
        sys.exit(0)

    app = App(idioma)
    app.mainloop()
