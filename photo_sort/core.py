import hashlib
import json
import os
import re
import shutil
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

try:
    from .config import (
        CHECKPOINT_FILENAME,
        CHECKPOINT_INTERVAL,
        EXTENSOES_IMAGEM,
        EXTENSOES_SUPORTADAS,
        EXTENSOES_VIDEO,
        PADROES_DATA_NOME,
    )
except ImportError:  # pragma: no cover
    from config import (
        CHECKPOINT_FILENAME,
        CHECKPOINT_INTERVAL,
        EXTENSOES_IMAGEM,
        EXTENSOES_SUPORTADAS,
        EXTENSOES_VIDEO,
        PADROES_DATA_NOME,
    )

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
                tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal", details=False)
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


def listar_arquivos(pasta_origem):
    """Lista arquivos suportados. followlinks=False evita loops em symlinks."""
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
                r'^' + re.escape(mes_nome) + r'_' + re.escape(str(ano)) + r'_(\d+)\.',
                re.IGNORECASE,
            )
            for arq in existentes:
                m = padrao_n.match(arq)
                if m:
                    n = max(n, int(m.group(1)) + 1)
        contadores[chave] = n

    n = contadores[chave]
    nome_base = "{}_{}_{}{}".format(mes_nome, ano, n, ext)
    caminho_completo = os.path.join(chave, nome_base)

    while os.path.exists(caminho_completo):
        n += 1
        nome_base = "{}_{}_{}{}".format(mes_nome, ano, n, ext)
        caminho_completo = os.path.join(chave, nome_base)

    contadores[chave] = n + 1
    return caminho_completo


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


def organizar(pasta_origem, pasta_destino, dry_run, copiar, fila_msgs, fila_progresso, t):
    """
    Organiza os arquivos de pasta_origem para pasta_destino.
    """
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
        fila_msgs.put(("log", msg))
        if log_file is not None:
            try:
                log_file.write(msg + "\n")
                log_file.flush()
            except Exception:
                pass

    ja_processados = set()
    if not dry_run:
        ja_processados = carregar_checkpoint(pasta_destino)
        if ja_processados:
            _emit(t["checkpoint_resumed"].format(len(ja_processados)))

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

    for idx, caminho_orig in enumerate(arquivos, start=1):
        nome_orig = os.path.basename(caminho_orig)
        fila_msgs.put(("status", t["processing"].format(nome_orig)))

        ext = Path(caminho_orig).suffix.lower()

        try:
            tamanho_arq = os.path.getsize(caminho_orig)
        except Exception:
            tamanho_arq = 0

        hash_orig = calcular_hash(caminho_orig)

        if hash_orig is not None and hash_orig in hashes_destino:
            _emit("{}  {}  ->  ja existe em: {}".format(t["duplicate"], caminho_orig, hashes_destino[hash_orig]))
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

        dt, fonte = detectar_data(caminho_orig)

        if dt is None:
            pasta_sd = os.path.join(pasta_destino, t["manual_check_folder"])
            destino = os.path.join(pasta_sd, nome_orig)
            if os.path.exists(destino):
                base, extensao = os.path.splitext(nome_orig)
                contador_sd = 1
                while os.path.exists(destino):
                    destino = os.path.join(pasta_sd, "{}_{}{}".format(base, contador_sd, extensao))
                    contador_sd += 1
            sem_data += 1
            ano_arq = None
        else:
            mes_nome = t["months"][dt.month]
            ano_arq = dt.year
            destino = gerar_nome_destino(pasta_destino, mes_nome, ano_arq, ext, contadores)
            por_ano[ano_arq] += 1

        if dry_run:
            prefixo = t["simulated"]
        elif copiar:
            prefixo = t["copied"]
        else:
            prefixo = t["moved"]

        _emit("{}  {}  ->  {}  (data: {})".format(prefixo, caminho_orig, destino, fonte))

        if not dry_run:
            try:
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                if copiar:
                    shutil.copy2(caminho_orig, destino)
                else:
                    shutil.move(caminho_orig, destino)

                if not copiar and hash_orig is not None:
                    hash_dest = calcular_hash(destino)
                    if hash_dest == hash_orig:
                        _emit("{}  {}".format(t["integrity_ok"], os.path.basename(destino)))
                    else:
                        _emit("{}  {}  (orig: {}  dest: {})".format(t["integrity_error"], os.path.basename(destino), hash_orig, hash_dest))
                        erros_integridade += 1

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
            if hash_orig is not None:
                hashes_destino[hash_orig] = destino
            tamanho_total += tamanho_arq
            processados += 1

        elapsed = time.time() - tempo_inicio
        velocidade = idx / elapsed if elapsed > 0 else 0
        restantes = total - idx
        eta_segundos = restantes / velocidade if velocidade > 0 else 0
        eta_str = str(timedelta(seconds=int(eta_segundos)))
        fila_progresso.put((idx, total, eta_str))

        if not dry_run and idx % CHECKPOINT_INTERVAL == 0:
            salvar_checkpoint(pasta_destino, processados_set)
            _emit(t["checkpoint_saved"].format(len(processados_set)))

    tempo_total_s = time.time() - tempo_inicio
    tempo_total_str = str(timedelta(seconds=int(tempo_total_s)))
    velocidade_media = round(processados / tempo_total_s, 1) if tempo_total_s > 0 else 0.0

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

    if not dry_run:
        deletar_checkpoint(pasta_destino)
        if log_file:
            _emit(t["log_saved"].format(caminho_log))
            log_file.close()

    fila_msgs.put(("fim", (processados, ignorados, sem_data)))
