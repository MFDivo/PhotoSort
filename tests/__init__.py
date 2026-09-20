from datetime import datetime
from pathlib import Path

from photo_sort.core import extrair_data_nome, formatar_tamanho, gerar_nome_destino, listar_arquivos


def test_extrair_data_nome_returns_datetime():
    assert extrair_data_nome("2024_05_12_IMG_001.jpg") == datetime(2024, 5, 12)


def test_formatar_tamanho_uses_units():
    assert formatar_tamanho(512) == "512 B"
    assert formatar_tamanho(1024) == "1.0 KB"


def test_listar_arquivos_only_supported_extensions(tmp_path):
    supported = tmp_path / "photo.jpg"
    supported.write_bytes(b"fake")
    nested = tmp_path / "nested"
    nested.mkdir()
    nested_video = nested / "clip.mp4"
    nested_video.write_bytes(b"fake")
    other = tmp_path / "notes.txt"
    other.write_text("ignore me")

    files = listar_arquivos(str(tmp_path))

    assert str(supported) in files
    assert str(nested_video) in files
    assert str(other) not in files


def test_gerar_nome_destino_avoids_overwrite(tmp_path):
    destino = tmp_path / "destino"
    destino.mkdir()

    year_dir = destino / "2024"
    month_dir = year_dir / "Maio"
    month_dir.mkdir(parents=True)

    existing = month_dir / "Maio_2024_1.jpg"
    existing.write_bytes(b"first")

    target = gerar_nome_destino(str(destino), "Maio", 2024, ".jpg", {})

    assert Path(target).name == "Maio_2024_2.jpg"
    assert str(target).startswith(str(destino))

