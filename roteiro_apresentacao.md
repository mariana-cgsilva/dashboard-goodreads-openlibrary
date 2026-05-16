# Roteiro de apresentacao

## 1. Abertura

Este projeto analisa dados da plataforma Goodreads para entender o que torna um livro popular e bem avaliado. A pergunta principal e: popularidade e qualidade caminham juntas?

## 2. Fonte dos dados

Usamos tres arquivos:

- `books.csv`: catalogo com informacoes dos livros, autores, idioma, ano e metricas gerais.
- `ratings.csv`: avaliacoes feitas por usuarios.
- `to_read.csv`: livros marcados por usuarios como interesse de leitura futura.

A base atende ao requisito de volume porque o arquivo de avaliacoes possui milhoes de registros.

Como ponto extra, tambem foi criado um script de coleta externa usando a API publica da Open Library. A coleta consulta livros por ISBN e gera o arquivo `data/external/openlibrary_books.csv`, com metadados como numero de paginas, editora, assunto principal, link e capa quando disponiveis.

## 3. Pipeline de dados

Primeiro os arquivos foram lidos com Pandas. Em seguida, as avaliacoes foram agregadas por livro, o interesse de leitura futura foi agregado por livro e os resultados foram integrados ao catalogo principal por `book_id`.

Na limpeza, tratamos anos invalidos, valores ausentes de idioma, titulos e autores. Na transformacao, criamos novas variaveis: decada de publicacao, autor principal, faixa de paginas, proporcao de cinco estrelas, proporcao de notas baixas, taxa de reviews, nota ponderada e score de popularidade.

Depois, os dados coletados da Open Library foram integrados por `book_id`, permitindo analisar se caracteristicas editoriais, como tamanho do livro, ajudam a explicar diferencas de avaliacao e popularidade.

## 4. Dashboard 1 - Visao geral

O primeiro dashboard funciona como painel executivo. Ele mostra o tamanho da base, o volume de avaliacoes, a nota media ponderada e o interesse futuro de leitura.

Depois, apresenta os livros com melhor equilibrio entre alcance, avaliacao e interesse futuro. Tambem mostra como as notas se distribuem, quais idiomas dominam a base e como a media muda por decada.

Tambem foi adicionada uma visualizacao dos metadados externos, comparando a nota media por faixa de paginas dos livros coletados na Open Library.

## 5. Dashboard 2 - Exploracao interativa

O segundo dashboard permite explorar recortes. O usuario pode filtrar por idioma, periodo de publicacao e nota media minima. Tambem pode escolher se o ranking deve priorizar score geral, nota ponderada ou interesse futuro.

As visualizacoes ajudam a comparar livros, autores, idiomas e relacao entre popularidade e qualidade.

## 6. Insights para destacar

- A maioria das avaliacoes tende a ser positiva, com concentracao grande em notas 4 e 5.
- Livros muito populares nem sempre sao os mais bem avaliados; por isso a nota ponderada e importante.
- O interesse futuro de leitura revela livros com demanda potencial, mesmo quando o volume de avaliacoes ainda nao e o maior.
- A coleta externa permite comparar caracteristicas editoriais, como quantidade de paginas, com nota media e popularidade.
- Autores com alto alcance aparecem de forma consistente quando juntamos quantidade de livros e volume de avaliacoes.
- A analise por decada e idioma ajuda a contextualizar a base e evita olhar apenas para rankings gerais.

## 7. Fechamento

O dashboard nao serve apenas para mostrar graficos. Ele organiza uma historia: separar popularidade, qualidade percebida e interesse futuro permite interpretar melhor o comportamento dos leitores e tomar decisoes mais fundamentadas sobre recomendacao, curadoria ou catalogo.
