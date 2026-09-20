# PhotoSort

Aplicativo para organizar fotos e vídeos em pastas por ano e mês, mantendo uma estrutura simples e fácil de navegar.

## Visão geral

O PhotoSort percorre uma pasta de origem, identifica a data de cada arquivo (priorizando EXIF, nome do arquivo e data de modificação), e organiza os itens em subpastas no formato:

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

Ele também suporta:

- simulação antes de mover arquivos
- cópia em vez de movimentação
- detecção de duplicatas por hash MD5
- checkpoint para continuar uma organização interrompida
- log com relatório detalhado
- barra de progresso e estimativa de tempo restante
- organização de imagens e vídeos com extensões conhecidas
- interface gráfica em Python (Tkinter)

## Funcionalidades

- Organização automática por ano e mês
- Extração de data a partir de EXIF (Pillow / exifread)
- Detecção por nome do arquivo como fallback
- Use da data de modificação do arquivo como último recurso
- Arquivos sem data podem ser enviados para uma pasta de revisão manual
- Modo de simulação para testar antes de mover arquivos
- Modo de cópia para preservar a origem intacta
- Deteção e ignorar arquivos duplicados
- Arquivos com problemas de permissão não quebram o processo
- Relatório final com estatísticas e distribuição por ano

## Requisitos

- Python 3.9+
- Bibliotecas:

```bash
pip install Pillow exifread
```

## Como executar

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

## Uso da interface

Ao abrir o programa, você pode:

- selecionar a pasta de origem
- selecionar a pasta de destino
- escolher entre simulação, cópia ou movimentação real
- iniciar a organização
- acompanhar progresso, status e log em tempo real

## Estrutura do projeto

```text
PhotoSort/
├── README.md
├── organize_photos.py
├── OrganizadorDeFotos.spec
├── build_windows.bat
├── PhotoSort.exe
└── ...
```

## Observações importantes

- Em modo de movimentação real, os arquivos são transferidos para a pasta de destino.
- Em modo de cópia, a origem permanece intacta.
- Em modo de simulação, o programa apenas calcula o que seria feito sem alterar os arquivos.
- O checkpoint é salvo na pasta de destino durante a execução para permitir continuidade em caso de interrupção.

## Exemplo de organização

Antes:

```text
minha_pasta/
├── IMG_001.jpg
├── IMG_002.jpg
├── video_1.mp4
├── 20240515_120000.png
```

Depois:

```text
minha_pasta_organizada/
├── 2024/
│   ├── Maio/
│   │   ├── Maio_2024_1.jpg
│   │   ├── Maio_2024_2.jpg
│   │   └── Maio_2024_3.mp4
│   └── ...
```

## Licença

Este projeto está sendo compartilhado como ferramenta utilitária pessoal/opensource. Verifique o arquivo ou repositório principal para detalhes específicos de uso e distribuição.

## Dica

Para arquivos com datas ambíguas ou sem metadados, o programa cria uma pasta de revisão manual para facilitar a conferência final.

---

Se você quiser, posso continuar e criar também uma versão mais profissional do README com badges, screenshots, guia de instalação para Windows e uma descrição mais “de produto”.
