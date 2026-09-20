# PhotoSort

Organizador automático de fotos e vídeos por ano e mês.

PhotoSort é uma ferramenta para organizar arquivos de mídia em pastas estruturadas no formato:

```text
Destino/
├── 2023/
│   ├── Janeiro/
│   ├── Fevereiro/
│   └── ...
├── 2024/
│   ├── Janeiro/
│   └── ...
```

Ele busca a data dos arquivos por EXIF, nome do arquivo e, como último recurso, pela data de modificação. Depois, move ou copia os itens para uma estrutura ordenada e fácil de navegar.

## Funcionalidades

- Organização automática por ano e mês
- Suporte para fotos e vídeos com extensões conhecidas
- Detecção de data por EXIF (Pillow / exifread)
- Fallback por nome do arquivo
- Fallback por data de modificação
- Modo de simulação antes de mover arquivos
- Opção de copiar em vez de mover
- Ignora arquivos duplicados por hash MD5
- Salva checkpoint para continuar processamento interrompido
- Gera log detalhado da operação
- Exibe progresso e estimativa de tempo restante
- Interface gráfica em Tkinter
- Suporte a múltiplos idiomas

## Requisitos

- Python 3.9 ou superior
- Dependências:

```bash
pip install Pillow exifread
```

## Como instalar

1. Clone o repositório:

```bash
git clone https://github.com/MFDivo/PhotoSort.git
cd PhotoSort
```

2. Instale as dependências:

```bash
pip install Pillow exifread
```

3. Execute o programa:

```bash
python organize_photos.py
```

## Como usar

Ao abrir a aplicação:

1. Selecione a pasta de origem
2. Selecione a pasta de destino
3. Escolha uma das opções:
   - Simulação (sem mover arquivos)
   - Copiar arquivos
   - Mover arquivos
4. Clique em organizar
5. Acompanhe a execução pelo progresso e pelo log

## Exemplos

Antes:

```text
fotos/
├── IMG_001.jpg
├── IMG_002.jpg
├── video_1.mp4
├── 20240515_120000.png
```

Depois:

```text
fotos_organizadas/
├── 2024/
│   ├── Maio/
│   │   ├── Maio_2024_1.jpg
│   │   ├── Maio_2024_2.jpg
│   │   └── Maio_2024_3.mp4
```

## Estrutura do projeto

```text
PhotoSort/
├── README.md
├── organize_photos.py
├── photo_sort/
│   ├── __init__.py
│   ├── config.py
│   ├── core.py
│   └── gui.py
├── OrganizadorDeFotos.spec
├── build_windows.bat
├── PhotoSort.exe
└── ...
```

## Observações importantes

- O modo de simulação é útil para testar a organização antes de mover arquivos reais.
- O modo de cópia preserva a pasta original intacta.
- O programa salva um checkpoint na pasta de destino para permitir continuidade em caso de interrupção.
- Arquivos sem data identificável podem ser movidos para uma pasta de revisão manual.
- Em casos de permissão ou erro de leitura, o sistema registra o problema e segue com os demais arquivos.

## Limitações

- A identificação de data depende da qualidade dos metadados do arquivo.
- Alguns formatos raros ou arquivos com metadados corrompidos podem exigir revisão manual.
- O programa foi pensado como ferramenta prática e útil, não como substituto de um organizador profissional de mídia.

## Licença

Este projeto é compartilhado como ferramenta utilitária. Verifique o repositório para detalhes específicos de uso e distribuição.

## Sobre o projeto

O PhotoSort foi criado para reduzir a dificuldade de organizar grandes coleções de imagens e vídeos, especialmente quando a estrutura de pastas e a data dos arquivos não seguem uma ordem consistente.

---

Se quiser, também posso criar uma versão do README em inglês, mais visual e pronta para apresentação pública no GitHub.
