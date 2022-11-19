# Raspando Dados de Deputados

Web scrap de custos e informações de deputados no ano de 2022.

O site alvo foi [esse](https://www.camara.leg.br/deputados). A única forma de buscar o gênero dos deputados nesse site é utilizando a url, para isso, durante a listagem dos mesmos, foram utilizadas essas URLs específicas para [homens](https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=56&sexo=M) e [mulheres](https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=56&sexo=F).

## Ferramental

A biblioteca utilizada é a `scrapy`, além de utilizar `pandas` para realizar operações com os dados.

Antes de tudo, é necessário criar um ambiente virtual e instalar as dependências que serão utilizadas. Para isso, execute os seguintes comandos (considerando que você está na pasta "scrapping-deputados"):

```
python3 -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

## Execução

Para realizar a extração dos dados, é necessário executar a `spider`, que buscará diferentes tipos de informações dos deputados, como gênero, informações de presenças e ausências no plenário e em comissões, e custos parlamentar e de gabinete ao longo do ano.

Para isso, execute o seguinte comando:

```
scrapy crawl deputados
```

O comando anterior criará diversos arquivos no diretório `./data/deputados`. Cada arquivo representa os dados extraídos de um certo deputado. 

Por fim, se for desejado unificar todos os arquivos em um arquivo só, ainda na raiz do diretório, execute o comando:

```
python3 src/utils/unify.py
```

Um arquivo nomeado `deputados.csv` será criado no diretório `data/`, reunindo todos os dados de todos os deputados que foram extraídos.
