"""
Organizador de Fotos e Videos
==============================
Organiza fotos e videos em subpastas <ANO>/<MES>/ com renomeacao sequencial.

Uso: python organize_photos.py

Dependencias: Pillow, exifread (pip install Pillow exifread)

Melhorias implementadas:
  - Correcoes de bugs (makedirs, timeouts, symlinks, permissoes)
  - Opcao copiar vs mover
  - Log em arquivo com timestamp
  - Deteccao de duplicatas com hash MD5
  - Barra de progresso com ETA
  - Retomar de checkpoint
  - Verificacao de integridade pos-transferencia
  - Estatisticas finais detalhadas
"""

import hashlib
import json
import os
import re
import shutil
import threading
import queue
import time
import tkinter as tk
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import ttk, filedialog, scrolledtext

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
        "flag": "EN",
        "lang_name": "English",
        "app_title": "Photo and Video Organizer",
        "select_lang": "Select Language",
        "continue": "Continue",
        "origin": "Source folder:",
        "destination": "Destination folder:",
        "browse": "Browse",
        "dry_run": "Simulate before moving (Dry Run)",
        "copy_instead": "Copy instead of move",
        "organize": "ORGANIZE",
        "log": "Log:",
        "waiting": "Waiting...",
        "done": "Done!",
        "starting": "Starting...",
        "processing": "Processing: {}",
        "no_files": "No supported files found in source folder.",
        "total_found": "Total files found: {}",
        "summary": "SUMMARY",
        "total_processed": "  Total processed       : {}",
        "total_ignored": "  Total ignored          : {}",
        "no_date": "  No date                : {}",
        "sim_mode": "  SIMULATION mode - no files were moved.",
        "init_log": "Starting organization [{}]",
        "sim_label": "SIMULATION",
        "real_label": "REAL EXECUTION",
        "copy_label": "COPY MODE",
        "origin_log": "Source      : {}",
        "dest_log": "Destination : {}",
        "moved": "[MOVED]",
        "copied": "[COPIED]",
        "simulated": "[SIMULATION]",
        "error": "[ERROR]",
        "err_origin": "[ERROR] Please set the source folder.",
        "err_origin_nf": "[ERROR] Source folder not found: {}",
        "err_dest": "[ERROR] Please set the destination folder.",
        "err_move": "[ERROR] Could not move/copy {}: {}",
        "err_permission": "[PERMISSION ERROR] Skipping: {}",
        "select_origin": "Select source folder",
        "select_dest": "Select destination folder",
        "manual_check_folder": "Check_manually",
        "log_saved": "Log saved to: {}",
        "duplicate": "[DUPLICATE]",
        "total_duplicates": "  Duplicates skipped     : {}",
        "checkpoint_resumed": "Resuming from checkpoint: {} files already processed",
        "checkpoint_saved": "Checkpoint saved ({} files)",
        "integrity_ok": "[OK]",
        "integrity_error": "[INTEGRITY ERROR]",
        "total_integrity_errors": "  Integrity errors       : {}",
        "year_dist": "  Year distribution:",
        "total_size": "  Total size             : {}",
        "avg_speed": "  Avg speed              : {} files/sec",
        "total_time": "  Total time             : {}",
        "months": {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December",
        },
    },
    "es": {
        "flag": "ES",
        "lang_name": "Espanol",
        "app_title": "Organizador de Fotos y Videos",
        "select_lang": "Seleccionar Idioma",
        "continue": "Continuar",
        "origin": "Carpeta de origen:",
        "destination": "Carpeta de destino:",
        "browse": "Explorar",
        "dry_run": "Simular antes de mover (Dry Run)",
        "copy_instead": "Copiar en vez de mover",
        "organize": "ORGANIZAR",
        "log": "Registro:",
        "waiting": "Esperando...",
        "done": "Completado!",
        "starting": "Iniciando...",
        "processing": "Procesando: {}",
        "no_files": "No se encontraron archivos compatibles en la carpeta de origen.",
        "total_found": "Total de archivos encontrados: {}",
        "summary": "RESUMEN",
        "total_processed": "  Total procesados       : {}",
        "total_ignored": "  Total ignorados        : {}",
        "no_date": "  Sin fecha              : {}",
        "sim_mode": "  Modo SIMULACION - ningun archivo fue movido.",
        "init_log": "Iniciando organizacion [{}]",
        "sim_label": "SIMULACION",
        "real_label": "EJECUCION REAL",
        "copy_label": "MODO COPIA",
        "origin_log": "Origen      : {}",
        "dest_log": "Destino     : {}",
        "moved": "[MOVIDO]",
        "copied": "[COPIADO]",
        "simulated": "[SIMULACION]",
        "error": "[ERROR]",
        "err_origin": "[ERROR] Indique la carpeta de origen.",
        "err_origin_nf": "[ERROR] Carpeta de origen no encontrada: {}",
        "err_dest": "[ERROR] Indique la carpeta de destino.",
        "err_move": "[ERROR] No se pudo mover/copiar {}: {}",
        "err_permission": "[ERROR DE PERMISO] Omitiendo: {}",
        "select_origin": "Seleccione la carpeta de origen",
        "select_dest": "Seleccione la carpeta de destino",
        "manual_check_folder": "Verificar_manualmente",
        "log_saved": "Log guardado en: {}",
        "duplicate": "[DUPLICADO]",
        "total_duplicates": "  Duplicados omitidos    : {}",
        "checkpoint_resumed": "Reanudando desde checkpoint: {} archivos ya procesados",
        "checkpoint_saved": "Checkpoint guardado ({} archivos)",
        "integrity_ok": "[OK]",
        "integrity_error": "[ERROR DE INTEGRIDAD]",
        "total_integrity_errors": "  Errores de integridad  : {}",
        "year_dist": "  Distribucion por ano:",
        "total_size": "  Tamano total           : {}",
        "avg_speed": "  Velocidad media        : {} archivos/seg",
        "total_time": "  Tiempo total           : {}",
        "months": {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
        },
    },
    "ru": {
        "flag": "RU",
        "lang_name": "Russkiy",
        "app_title": "Organayzer foto i video",
        "select_lang": "Vybor yazyka",
        "continue": "Prodolzhit",
        "origin": "Iskhodnaya papka:",
        "destination": "Papka naznacheniya:",
        "browse": "Obzor",
        "dry_run": "Simulyatsiya pered peremeshcheniyem (Dry Run)",
        "copy_instead": "Kopirovat vmesto peremeshcheniya",
        "organize": "ORGANIZOVAT",
        "log": "Zhurnal:",
        "waiting": "Ozhidaniye...",
        "done": "Gotovo!",
        "starting": "Zapusk...",
        "processing": "Obrabotka: {}",
        "no_files": "Podderzhivayemye fayly ne naydeny v iskhodnoy papke.",
        "total_found": "Vsego naydeno faylov: {}",
        "summary": "ITOG",
        "total_processed": "  Obrabotano             : {}",
        "total_ignored": "  Propushcheno           : {}",
        "no_date": "  Bez daty               : {}",
        "sim_mode": "  Rezhim SIMULYATSII - fayly ne peremeshchalis.",
        "init_log": "Zapusk organizatsii [{}]",
        "sim_label": "SIMULYATSIYA",
        "real_label": "REALNYY ZAPUSK",
        "copy_label": "REZHIM KOPIROVANIYA",
        "origin_log": "Istochnik   : {}",
        "dest_log": "Naznacheniye: {}",
        "moved": "[PEREMESHCHENO]",
        "copied": "[SKOPIROVANO]",
        "simulated": "[SIMULYATSIYA]",
        "error": "[OSHIBKA]",
        "err_origin": "[OSHIBKA] Ukazhite iskhodnuyu papku.",
        "err_origin_nf": "[OSHIBKA] Iskhodnaya papka ne naydena: {}",
        "err_dest": "[OSHIBKA] Ukazhite papku naznacheniya.",
        "err_move": "[OSHIBKA] Ne udalos peremestit/skopirovat {}: {}",
        "err_permission": "[OSHIBKA DOSTUPA] Propusk: {}",
        "select_origin": "Vyberte iskhodnuyu papku",
        "select_dest": "Vyberte papku naznacheniya",
        "manual_check_folder": "Proverit_vruchnuyu",
        "log_saved": "Zhurnal sokhranen v: {}",
        "duplicate": "[DUBLIKAT]",
        "total_duplicates": "  Dublikaty propushcheny : {}",
        "checkpoint_resumed": "Vozobnovleniye s tochki kontrolya: {} faylov uzhe obrabotano",
        "checkpoint_saved": "Tochka kontrolya sokhranena ({} faylov)",
        "integrity_ok": "[OK]",
        "integrity_error": "[OSHIBKA TSELOSTNOSTI]",
        "total_integrity_errors": "  Oshibki tselostnosti   : {}",
        "year_dist": "  Raspredeleniye po godam:",
        "total_size": "  Obshchiy razmer        : {}",
        "avg_speed": "  Sred. skorost          : {} faylov/sek",
        "total_time": "  Obshcheye vremya       : {}",
        "months": {
            1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
            5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
            9: "Sentyabr", 10: "Oktyabr", 11: "Noyabr", 12: "Dekabr",
        },
    },
    "zh": {
        "flag": "ZH",
        "lang_name": "Zhongwen",
        "app_title": "Zhaopian he shipin zhengliji",
        "select_lang": "Xuanze yuyan",
        "continue": "Jixu",
        "origin": "Yuan wenjianjia:",
        "destination": "Mubiao wenjianjia:",
        "browse": "Liulan",
        "dry_run": "Yidong qian moni yunxing (Dry Run)",
        "copy_instead": "Fuzhi er bu shi yidong",
        "organize": "ZHENGLI",
        "log": "Rizhi:",
        "waiting": "Dengdai zhong...",
        "done": "Wancheng!",
        "starting": "Qidong zhong...",
        "processing": "Zheng zai chuli: {}",
        "no_files": "Zai yuan wenjianjia zhong wei zhaodao zhichi de wenjian.",
        "total_found": "Gong zhaodao wenjian: {}",
        "summary": "ZHAIYAO",
        "total_processed": "  Yi chuli               : {}",
        "total_ignored": "  Yi hulue               : {}",
        "no_date": "  Wu riqi                : {}",
        "sim_mode": "  Moni moshi - meiyou wenjian bei yidong.",
        "init_log": "Kaishi zhengli [{}]",
        "sim_label": "MONI",
        "real_label": "SHIJI ZHIXING",
        "copy_label": "FUZHI MOSHI",
        "origin_log": "Laiyuan     : {}",
        "dest_log": "Mubiao      : {}",
        "moved": "[YI YIDONG]",
        "copied": "[YI FUZHI]",
        "simulated": "[MONI]",
        "error": "[CUOWU]",
        "err_origin": "[CUOWU] Qing shezhi yuan wenjianjia.",
        "err_origin_nf": "[CUOWU] Wei zhaodao yuan wenjianjia: {}",
        "err_dest": "[CUOWU] Qing shezhi mubiao wenjianjia.",
        "err_move": "[CUOWU] Wufa yidong/fuzhi {}: {}",
        "err_permission": "[QUANXIAN CUOWU] Tiaoguo: {}",
        "select_origin": "Xuanze yuan wenjianjia",
        "select_dest": "Xuanze mubiao wenjianjia",
        "manual_check_folder": "Shou_dong_jian_cha",
        "log_saved": "Rizhi yi baocun zhi: {}",
        "duplicate": "[CHONGFU]",
        "total_duplicates": "  Chongfu tiaoguo        : {}",
        "checkpoint_resumed": "Cong jiancha dian jixu: {} ge wenjian yi chuli",
        "checkpoint_saved": "Jiancha dian yi baocun ({} ge wenjian)",
        "integrity_ok": "[OK]",
        "integrity_error": "[WANZHENGXING CUOWU]",
        "total_integrity_errors": "  Wanzhengxing cuowu     : {}",
        "year_dist": "  Nian fen bu:",
        "total_size": "  Zong da xiao           : {}",
        "avg_speed": "  Ping jun su du         : {} ge/miao",
        "total_time": "  Zong shi jian          : {}",
        "months": {
            1: "Yiyue", 2: "Eryue", 3: "Sanyue", 4: "Siyue",
            5: "Wuyue", 6: "Liuyue", 7: "Qiyue", 8: "Bayue",
            9: "Jiuyue", 10: "Shiyue", 11: "Shiyiyue", 12: "Shi_eryue",
        },
    },
}

LANGUAGE_ORDER = ["en", "es", "ru", "zh"]

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
EXTENSOES_IMAGEM = {
    ".jpg", ".jpeg", ".jpe", ".jif", ".jfif", ".jfi",
    ".png", ".apng",
    ".gif",
    ".bmp", ".dib",
    ".tiff", ".tif",
    ".webp",
    ".heic", ".heif",
    ".avif",
    ".jxl",
    ".svg", ".svgz",
    ".ico", ".cur",
    ".psd", ".psb",
    ".ai", ".eps",
    ".cr2", ".cr3", ".crw",
    ".nef", ".nrw",
    ".arw", ".srf", ".sr2",
    ".raf",
    ".orf",
    ".rw2",
    ".pef", ".ptx",
    ".rwl",
    ".srw",
    ".x3f",
    ".kdc", ".dcr",
    ".mrw",
    ".dng", ".raw", ".3fr", ".erf", ".mef", ".mos",
    ".exr", ".hdr", ".rgbe",
    ".tga", ".icb", ".vda", ".vst",
    ".pcx",
    ".xbm", ".xpm",
    ".wmf", ".emf",
    ".xcf",
    ".ppm", ".pgm", ".pbm", ".pnm", ".pfm",
    ".sgi", ".rgb", ".rgba", ".bw",
    ".j2k", ".jp2", ".jpf", ".jpx", ".jpm", ".mj2",
}

EXTENSOES_VIDEO = {
    ".mp4", ".m4v", ".m4p",
    ".mov", ".qt",
    ".avi",
    ".mkv", ".mk3d",
    ".wmv", ".asf",
    ".flv", ".f4v", ".f4p",
    ".3gp", ".3g2", ".3gpp", ".3gpp2",
    ".mpg", ".mpeg", ".mpe", ".mpv", ".m1v", ".m2v",
    ".ts", ".mts", ".m2ts", ".tp", ".trp",
    ".vob",
    ".webm",
    ".ogv", ".ogg",
    ".rm", ".rmvb",
    ".divx",
    ".mxf",
    ".dv", ".dif",
    ".swf",
    ".amv", ".nsv", ".yuv", ".gifv",
}

EXTENSOES_SUPORTADAS = EXTENSOES_IMAGEM | EXTENSOES_VIDEO

PADROES_DATA_NOME = [
    re.compile(r'(?<!\d)(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)'),
    re.compile(r'(20\d{2})[-_](0[1-9]|1[0-2])[-_](0[1-9]|[12]\d|3[01])'),
]

CHECKPOINT_FILENAME = "organize_checkpoint.json"
CHECKPOINT_INTERVAL = 50

# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------

def formatar_tamanho(bytes_total):
    """Converte bytes para string legivel (KB, MB, GB)."""
    if bytes_total < 1024:
        return "{} B".format(bytes_total)
    elif bytes_total < 1024 ** 2:
        return "{:.1f} KB".format(bytes_total / 1024)
    elif bytes_total < 1024 ** 3:
        return "{:.1f} MB".format(bytes_total / 1024 ** 2)
    else:
        return "{:.2f} GB".format(bytes_total / 1024 ** 3)


def calcular_hash(caminho, block_size=65536):
    """Calcula hash MD5 de um arquivo. Retorna None em caso de erro."""
    hasher = hashlib.md5()
    try:
        with open(caminho, "rb") as f:
            while True:
                bloco = f.read(block_size)
                if not bloco:
                    break
                hasher.update(bloco)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return None


# ---------------------------------------------------------------------------
# Logica de negocio - deteccao de data
# ---------------------------------------------------------------------------

def extrair_data_exif_pillow(caminho):
    """Extrai data EXIF usando Pillow. Protegido com try/except generico."""
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
    """Extrai data EXIF usando exifread com timeout de 5 segundos."""
    if not EXIFREAD_OK:
        return None

    resultado = [None]
    excecao = [None]

    def _ler():
        try:
            with open(caminho, "rb") as f:
                tags = exifread.process_file(
                    f, stop_tag="EXIF DateTimeOriginal", details=False
                )
            chave = "EXIF DateTimeOriginal"
            if chave in tags:
                valor = str(tags[chave])
                resultado[0] = datetime.strptime(valor, "%Y:%m:%d %H:%M:%S")
        except Exception as e:
            excecao[0] = e

    t = threading.Thread(target=_ler, daemon=True)
    t.start()
    t.join(timeout=5)
    if t.is_alive():
        return None
    if excecao[0] is not None:
        return None
    return resultado[0]


def extrair_data_nome(nome_arquivo):
    """Tenta extrair data a partir do nome do arquivo."""
    for padrao in PADROES_DATA_NOME:
        m = padrao.search(nome_arquivo)
        if m:
            try:
                ano = int(m.group(1))
                mes = int(m.group(2))
                dia = int(m.group(3))
                return datetime(ano, mes, dia)
            except ValueError:
                continue
    return None


def extrair_data_modificacao(caminho):
    """Usa a data de modificacao do arquivo como fallback."""
    try:
        ts = os.path.getmtime(caminho)
        return datetime.fromtimestamp(ts)
    except Exception:
        return None


def detectar_data(caminho):
    """Detecta a data de um arquivo tentando varias estrategias."""
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
    """Lista arquivos suportados. followlinks=False evita loops em symlinks.
    Trata PermissionError por pasta e por arquivo individualmente."""
    arquivos = []
    for raiz, dirs, nomes in os.walk(pasta_origem, followlinks=False):
        dirs_ok = []
        for d in dirs:
            caminho_d = os.path.join(raiz, d)
            try:
                os.listdir(caminho_d)
                dirs_ok.append(d)
            except PermissionError:
                pass
        dirs[:] = dirs_ok

        for nome in nomes:
            ext = Path(nome).suffix.lower()
            if ext in EXTENSOES_SUPORTADAS:
                caminho = os.path.join(raiz, nome)
                try:
                    os.stat(caminho)
                    arquivos.append(caminho)
                except PermissionError:
                    pass
    return arquivos


def gerar_nome_destino(pasta_destino, mes_nome, ano, ext, contadores):
    """Gera um caminho de destino unico com nomenclatura sequencial."""
    chave = os.path.join(pasta_destino, str(ano), mes_nome)
    if chave not in contadores:
        n = 1
        if os.path.isdir(chave):
            existentes = os.listdir(chave)
            padrao_n = re.compile(
                r'^'  + re.escape(mes_nome) + r'_' + re.escape(str(ano)) + r'_(\d+)\.',
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
        nome_base = "{}_{}_{}{}".format(mes_nome, ano, n, ext)
        caminho_completo = os.path.join(chave, nome_base)

    contadores[chave] = n + 1
    return caminho_completo


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------

def carregar_checkpoint(pasta_destino):
    """Carrega lista de arquivos ja processados do checkpoint, se existir."""
    caminho = os.path.join(pasta_destino, CHECKPOINT_FILENAME)
    if os.path.isfile(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return set(dados.get("processed", []))
        except Exception:
            pass
    return set()


def salvar_checkpoint(pasta_destino, processados_set):
    """Salva checkpoint com a lista de arquivos ja processados."""
    caminho = os.path.join(pasta_destino, CHECKPOINT_FILENAME)
    try:
        os.makedirs(pasta_destino, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump({"processed": list(processados_set)}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def deletar_checkpoint(pasta_destino):
    """Remove o arquivo de checkpoint apos conclusao bem-sucedida."""
    caminho = os.path.join(pasta_destino, CHECKPOINT_FILENAME)
    try:
        if os.path.isfile(caminho):
            os.remove(caminho)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Funcao principal de organizacao
# ---------------------------------------------------------------------------

def organizar(pasta_origem, pasta_destino, dry_run, copiar, fila_msgs, fila_progresso, t):
    """
    Organiza os arquivos de pasta_origem para pasta_destino.

    Parametros:
        pasta_origem   : pasta com as fotos/videos originais
        pasta_destino  : pasta onde serao organizados
        dry_run        : True = simulacao, nao move/copia nada
        copiar         : True = usar shutil.copy2; False = usar shutil.move
        fila_msgs      : queue.Queue para enviar mensagens de log para a GUI
        fila_progresso : queue.Queue para enviar progresso (idx, total, eta_str)
        t              : dicionario de traducoes do idioma selecionado
    """

    # ------------------------------------------------------------------
    # 1. Criar pasta destino e abrir log em arquivo
    # ------------------------------------------------------------------
    os.makedirs(pasta_destino, exist_ok=True)

    ts_inicio_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_log = "organize_{}.log".format(ts_inicio_str)
    caminho_log = os.path.join(pasta_destino, nome_log)

    log_file = None
    if not dry_run:
        try:
            log_file = open(caminho_log, "w", encoding="utf-8")
        except Exception:
            log_file = None

    def _emit(msg):
        """Envia mensagem para a fila GUI e escreve no arquivo de log."""
        fila_msgs.put(("log", msg))
        if log_file is not None:
            try:
                log_file.write(msg + "\n")
                log_file.flush()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 2. Carregar checkpoint
    # ------------------------------------------------------------------
    ja_processados = set()
    if not dry_run:
        ja_processados = carregar_checkpoint(pasta_destino)
        if ja_processados:
            _emit(t["checkpoint_resumed"].format(len(ja_processados)))

    # ------------------------------------------------------------------
    # 3. Listar arquivos
    # ------------------------------------------------------------------
    todos_arquivos = listar_arquivos(pasta_origem)
    total_encontrados = len(todos_arquivos)

    if total_encontrados == 0:
        _emit(t["no_files"])
        fila_msgs.put(("fim", (0, 0, 0)))
        if log_file:
            log_file.close()
        return

    _emit(t["total_found"].format(total_encontrados))

    arquivos = [a for a in todos_arquivos if a not in ja_processados]
    total = len(arquivos)
    fila_progresso.put((0, total, "--:--:--"))

    # ------------------------------------------------------------------
    # 4. Estruturas de controle
    # ------------------------------------------------------------------
    contadores = {}
    hashes_destino = {}
    processados_set = set(ja_processados)

    processados = 0
    ignorados = 0
    sem_data = 0
    duplicatas = 0
    erros_integridade = 0
    por_ano = defaultdict(int)
    tamanho_total = 0

    tempo_inicio = time.time()

    # ------------------------------------------------------------------
    # 5. Loop principal
    # ------------------------------------------------------------------
    for idx, caminho_orig in enumerate(arquivos, start=1):
        nome_orig = os.path.basename(caminho_orig)
        fila_msgs.put(("status", t["processing"].format(nome_orig)))

        ext = Path(caminho_orig).suffix.lower()

        # Tamanho do arquivo
        try:
            tamanho_arq = os.path.getsize(caminho_orig)
        except Exception:
            tamanho_arq = 0

        # Hash do arquivo de origem
        hash_orig = calcular_hash(caminho_orig)

        # Verificar duplicata pelo hash
        if hash_orig is not None and hash_orig in hashes_destino:
            _emit(
                "{}  {}  ->  ja existe em: {}".format(
                    t["duplicate"], caminho_orig, hashes_destino[hash_orig]
                )
            )
            duplicatas += 1
            elapsed = time.time() - tempo_inicio
            velocidade = idx / elapsed if elapsed > 0 else 0
            restantes = total - idx
            eta_segundos = restantes / velocidade if velocidade > 0 else 0
            eta_str = str(timedelta(seconds=int(eta_segundos)))
            fila_progresso.put((idx, total, eta_str))
            processados_set.add(caminho_orig)
            if not dry_run and idx % CHECKPOINT_INTERVAL == 0:
                salvar_checkpoint(pasta_destino, processados_set)
                _emit(t["checkpoint_saved"].format(len(processados_set)))
            continue

        # Detectar data
        dt, fonte = detectar_data(caminho_orig)

        # Gerar caminho de destino
        if dt is None:
            pasta_sd = os.path.join(pasta_destino, t["manual_check_folder"])
            destino = os.path.join(pasta_sd, nome_orig)
            if os.path.exists(destino):
                base, extensao = os.path.splitext(nome_orig)
                contador_sd = 1
                while os.path.exists(destino):
                    destino = os.path.join(
                        pasta_sd, "{}_{}{}".format(base, contador_sd, extensao)
                    )
                    contador_sd += 1
            sem_data += 1
            ano_arq = None
        else:
            mes_nome = t["months"][dt.month]
            ano_arq = dt.year
            destino = gerar_nome_destino(pasta_destino, mes_nome, ano_arq, ext, contadores)
            por_ano[ano_arq] += 1

        # Prefixo de log
        if dry_run:
            prefixo = t["simulated"]
        elif copiar:
            prefixo = t["copied"]
        else:
            prefixo = t["moved"]

        _emit("{}  {}  ->  {}  (data: {})".format(prefixo, caminho_orig, destino, fonte))

        # Executar operacao real
        if not dry_run:
            try:
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                if copiar:
                    shutil.copy2(caminho_orig, destino)
                else:
                    shutil.move(caminho_orig, destino)

                # Verificacao de integridade (apenas no modo mover real)
                if not copiar and hash_orig is not None:
                    hash_dest = calcular_hash(destino)
                    if hash_dest == hash_orig:
                        _emit("{}  {}".format(t["integrity_ok"], os.path.basename(destino)))
                    else:
                        _emit(
                            "{}  {}  (orig: {}  dest: {})".format(
                                t["integrity_error"],
                                os.path.basename(destino),
                                hash_orig,
                                hash_dest,
                            )
                        )
                        erros_integridade += 1

                # Registrar hash no dicionario
                if hash_orig is not None:
                    hashes_destino[hash_orig] = destino

                tamanho_total += tamanho_arq
                processados += 1
                processados_set.add(caminho_orig)

            except PermissionError:
                _emit(t["err_permission"].format(nome_orig))
                ignorados += 1
            except Exception as e:
                _emit(t["err_move"].format(nome_orig, e))
                ignorados += 1
        else:
            # Simulacao: apenas contabilizar
            if hash_orig is not None:
                hashes_destino[hash_orig] = destino
            tamanho_total += tamanho_arq
            processados += 1

        # ETA
        elapsed = time.time() - tempo_inicio
        velocidade = idx / elapsed if elapsed > 0 else 0
        restantes = total - idx
        eta_segundos = restantes / velocidade if velocidade > 0 else 0
        eta_str = str(timedelta(seconds=int(eta_segundos)))
        fila_progresso.put((idx, total, eta_str))

        # Checkpoint periodico
        if not dry_run and idx % CHECKPOINT_INTERVAL == 0:
            salvar_checkpoint(pasta_destino, processados_set)
            _emit(t["checkpoint_saved"].format(len(processados_set)))

    # ------------------------------------------------------------------
    # 6. Estatisticas finais detalhadas
    # ------------------------------------------------------------------
    tempo_total_s = time.time() - tempo_inicio
    tempo_total_str = str(timedelta(seconds=int(tempo_total_s)))
    velocidade_media = (
        round(processados / tempo_total_s, 1) if tempo_total_s > 0 else 0.0
    )

    _emit("")
    _emit("=" * 60)
    _emit(t["summary"])
    _emit(t["total_processed"].format(processados))
    _emit(t["total_ignored"].format(ignorados))
    _emit(t["no_date"].format(sem_data))
    _emit(t["total_duplicates"].format(duplicatas))
    _emit(t["total_integrity_errors"].format(erros_integridade))
    _emit(t["total_size"].format(formatar_tamanho(tamanho_total)))
    _emit(t["avg_speed"].format(velocidade_media))
    _emit(t["total_time"].format(tempo_total_str))

    if por_ano:
        _emit(t["year_dist"])
        partes = ["    {}:  {} files".format(ano, qtd) for ano, qtd in sorted(por_ano.items())]
        _emit("  |  ".join(partes))

    if dry_run:
        _emit(t["sim_mode"])
    _emit("=" * 60)

    # ------------------------------------------------------------------
    # 7. Finalizar checkpoint e log
    # ------------------------------------------------------------------
    if not dry_run:
        deletar_checkpoint(pasta_destino)
        if log_file:
            _emit(t["log_saved"].format(caminho_log))
            log_file.close()

    fila_msgs.put(("fim", (processados, ignorados, sem_data)))


# ---------------------------------------------------------------------------
# Tela de selecao de idioma
# ---------------------------------------------------------------------------

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
        tk.Label(
            self,
            text="Select Language",
            font=("Helvetica", 15, "bold"),
            pady=10,
        ).pack(pady=(20, 4))

        tk.Label(
            self,
            text="Choose the interface language:",
            font=("Helvetica", 10),
            fg="#555555",
        ).pack(pady=(0, 16))

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


# ---------------------------------------------------------------------------
# Interface principal
# ---------------------------------------------------------------------------

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

        # Titulo (row=0)
        tk.Label(
            self,
            text=t["app_title"],
            font=("Helvetica", 16, "bold"),
        ).grid(row=0, column=0, columnspan=3, pady=(16, 8))

        # Pasta de origem (row=1)
        tk.Label(self, text=t["origin"]).grid(row=1, column=0, sticky="e", **pad)
        self._var_origem = tk.StringVar()
        tk.Entry(self, textvariable=self._var_origem, width=52).grid(
            row=1, column=1, sticky="ew", **pad
        )
        tk.Button(self, text=t["browse"], command=self._escolher_origem).grid(
            row=1, column=2, **pad
        )

        # Pasta de destino (row=2)
        tk.Label(self, text=t["destination"]).grid(row=2, column=0, sticky="e", **pad)
        self._var_destino = tk.StringVar()
        tk.Entry(self, textvariable=self._var_destino, width=52).grid(
            row=2, column=1, sticky="ew", **pad
        )
        tk.Button(self, text=t["browse"], command=self._escolher_destino).grid(
            row=2, column=2, **pad
        )

        self._var_origem.trace_add("write", self._atualizar_destino_padrao)

        # Checkbox dry run (row=3)
        self._var_dry_run = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self,
            text=t["dry_run"],
            variable=self._var_dry_run,
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=14, pady=(4, 0))

        # Checkbox copiar em vez de mover (row=4)
        self._var_copiar = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self,
            text=t["copy_instead"],
            variable=self._var_copiar,
        ).grid(row=4, column=0, columnspan=3, sticky="w", padx=14, pady=(0, 2))

        # Botao organizar (row=5)
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

        # Barra de progresso (row=6)
        frame_prog = tk.Frame(self)
        frame_prog.grid(row=6, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 2))
        frame_prog.columnconfigure(0, weight=1)

        self._var_progresso = tk.DoubleVar(value=0)
        self._barra = ttk.Progressbar(
            frame_prog,
            variable=self._var_progresso,
            maximum=100,
            length=400,
        )
        self._barra.grid(row=0, column=0, sticky="ew")

        self._label_progresso = tk.Label(
            frame_prog, text="0%  (0 / 0)  ETA: --:--:--", width=34
        )
        self._label_progresso.grid(row=0, column=1, padx=(8, 0))

        # Label de status (row=7)
        self._var_status = tk.StringVar(value=t["waiting"])
        tk.Label(
            self,
            textvariable=self._var_status,
            anchor="w",
            fg="#555555",
        ).grid(row=7, column=0, columnspan=3, sticky="ew", padx=14)

        # Label de log (row=8)
        tk.Label(self, text=t["log"], anchor="w").grid(
            row=8, column=0, columnspan=3, sticky="w", padx=14
        )

        # Area de log (row=9)
        self._log = scrolledtext.ScrolledText(
            self,
            height=14,
            state="disabled",
            wrap="word",
            font=("Courier", 10),
        )
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
            args=(
                origem,
                destino,
                dry_run,
                copiar,
                self._fila_msgs,
                self._fila_progresso,
                t,
            ),
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
                self._label_progresso.config(
                    text="{}%  ({} / {})  ETA: {}".format(int(pct), idx, total, eta_str)
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
        import sys
        sys.exit(0)

    app = App(idioma)
    app.mainloop()
