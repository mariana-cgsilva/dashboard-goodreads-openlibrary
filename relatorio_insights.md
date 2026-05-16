# Relatorio de insights - Dashboard Goodreads

## Fonte dos dados

- Base Goodreads usada nas aulas da disciplina.
- Arquivos brutos: `books.csv`, `ratings.csv` e `to_read.csv`.
- Enriquecimento opcional via coleta na API publica Open Library por ISBN.
- Volume: 10.000 livros, milhoes de avaliacoes de usuarios e marcacoes de livros para leitura futura.

## Pipeline executado

1. Leitura dos arquivos com Pandas.
2. Agregacao de ratings por livro e distribuicao geral das notas.
3. Agregacao de marcacoes `to_read` por livro.
4. Merge entre livros, avaliacoes agregadas e interesse futuro de leitura.
5. Integracao dos metadados coletados na Open Library quando `data/external/openlibrary_books.csv` esta disponivel.
6. Limpeza de anos invalidos, idiomas ausentes e titulos/autores nulos.
7. Criacao de variaveis: decada, autor principal, faixa de paginas, taxa de reviews, proporcao de 5 estrelas, proporcao de notas baixas, nota ponderada e score de popularidade.

## Insights principais para a apresentacao

- O livro com maior score combinado de popularidade e qualidade foi **The Hunger Games (The Hunger Games, #1)**, com score 90.76.
- Entre livros com pelo menos 50.000 avaliacoes, o destaque de qualidade foi **Harry Potter Boxset (Harry Potter, #1-7)**, com nota ponderada 4.70.
- A decada com maior media de nota, considerando pelo menos 20 livros, foi **1940s**, com media 4.08.
- A distribuicao de notas indica predominancia de avaliacoes positivas: 33.18% das notas da amostra sao 5 estrelas.
- Notas baixas, 1 ou 2 estrelas, representam 8.09% da amostra, sugerindo vies de avaliacao mais positivo na plataforma.
- A comparacao entre media de nota e volume de avaliacoes ajuda a separar livros populares de livros realmente bem avaliados.
- A variavel `to_read_count` mostra demanda futura: alguns livros aparecem com alto interesse mesmo quando nao lideram o ranking de avaliacoes ja feitas.
- A coleta externa da Open Library trouxe quantidade de paginas para 168 livros da amostra coletada.