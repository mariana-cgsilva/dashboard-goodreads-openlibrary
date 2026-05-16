# Projeto Final - Dashboard Goodreads

Tema: analise de popularidade, qualidade e interesse futuro em livros da base Goodreads.

## Por que este tema funciona para o enunciado

- A base tem mais de 10.000 registros quando consideramos as avaliacoes de usuarios.
- Usa mais de dois arquivos: `books.csv`, `ratings.csv` e `to_read.csv`.
- Inclui ponto extra de coleta externa: enriquecimento dos livros via API publica Open Library por ISBN.
- Permite merge, agregacoes, limpeza, criacao de variaveis e analise comparativa.
- O dashboard tem duas partes: visao geral executiva e exploracao interativa.

## Estrutura

- `data/raw/`: arquivos brutos usados no projeto.
- `data/external/`: arquivo coletado da Open Library, gerado pelo script de coleta.
- `data/processed/`: arquivos gerados pelo pipeline.
- `analise_processamento_goodreads.ipynb`: notebook com a etapa didatica de leitura, exploracao, limpeza, transformacao, merge, criacao de variaveis e exportacao dos dados.
- `collect_openlibrary_data.py`: script de coleta de metadados externos por ISBN na API publica Open Library.
- `prepare_data.py`: prepara, integra e transforma os dados.
- `app.py`: dashboard em Dash.
- `relatorio_insights.md`: resumo gerado com os principais achados.
- `roteiro_apresentacao.md`: sugestao de fala para a apresentacao.

## Como executar

1. Instale Python 3.10 ou superior.
2. Abra um terminal nesta pasta.
3. Instale as dependencias:

```powershell
python -m pip install -r requirements.txt
```

4. Opcionalmente, abra e execute o notebook para acompanhar o processamento passo a passo:

```powershell
jupyter notebook analise_processamento_goodreads.ipynb
```

5. Para buscar o ponto extra, rode a coleta externa da Open Library:

```powershell
python collect_openlibrary_data.py
```

Esse script consulta a API publica da Open Library por ISBN e cria:

```text
data/external/openlibrary_books.csv
```

6. Prepare os dados pelo script reprodutivel:

```powershell
python prepare_data.py
```

7. Rode o dashboard:

```powershell
python app.py
```

8. Abra o navegador no endereco indicado pelo Dash, normalmente:

```text
http://127.0.0.1:8050
```

## Ideia central da analise

A pergunta que guia o projeto e: **o que torna um livro popular e bem avaliado?**

Para responder, o projeto compara:

- volume de avaliacoes;
- nota media;
- nota ponderada, para reduzir distorcao de livros com poucas avaliacoes;
- quantidade de usuarios que marcaram o livro para ler;
- quantidade de paginas e assunto/editora coletados na Open Library;
- idioma, decada de publicacao e autor principal.

## Dashboards

### Dashboard 1 - Visao Geral

Mostra indicadores principais, ranking executivo, distribuicao das notas, evolucao por decada e composicao por idioma.

### Dashboard 2 - Exploracao Interativa

Permite filtrar por idioma, periodo de publicacao e nota minima. Tambem permite escolher a metrica do ranking. Contem pelo menos cinco visualizacoes: ranking, dispersao, histograma, autores, boxplot por idioma e tabela.
