import os
import html
from time import sleep
from math import ceil
from tqdm import tqdm
import pandas as pd
from scrapy import (
    Spider,
    Request
)

COLUMNS = [
    'id', 'name', 'gender', 'presença_plenario',
    'ausencia_justificada_plenario', 'ausencia_plenario',
    'presenca_comissao', 'ausencia_justificada_comissao',
    'ausencia_comissao', 'data_nascimento', 'salario_bruto',
    'salario_bruto_par', 'quant_viagem', 'gasto_total_par', 'gasto_jan_par',
    'gasto_fev_par', 'gasto_mar_par', 'gasto_abr_par ', 'gasto_maio_par',
    'gasto_junho_par', 'gasto_jul_par', 'gasto_agosto_par', 'gasto_set_par',
    'gasto_out_par', 'gasto_nov_par', 'gasto_dez_par', 'gasto_total_gab',
    'gasto_jan_gab', 'gasto_fev_gab', 'gasto_mar_gab', 'gasto_abr_gab',
    'gasto_maio_gab', 'gasto_junho_gab', 'gasto_jul_gab',
    'gasto_agosto_gab', 'gasto_set_gab', 'gasto_out_gab', 'gasto_nov_gab',
    'gasto_dez_gab'
]

months_index = {
    "janeiro": 0,
    "fevereiro": 1,
    "março": 2,
    "abril": 3,
    "maio": 4,
    "junho": 5,
    "julho": 6,
    "agosto": 7,
    "setembro": 8,
    "outubro": 9,
    "novembro": 10,
    "dezembro": 11
}

URL_LIST = "https://www.camara.leg.br/deputados/quem-sao/resultado?search=&partido=&uf=&legislatura=56"
URL_DEPUTADO = "https://www.camara.leg.br/deputados"

class DeputadosSpider(Spider):
    name = "deputados"

    def start_requests(self):
        genders = ["M", "F"]
        for gender in genders:
            i = 1
            yield Request(
                self.__generate_url_list(gender, i),
                callback=self.get_deputados,
                cb_kwargs=dict(
                    gender=gender
                )
            )
            while self.__verify_corner_page(gender, i):
                i += 1
                yield Request(
                    self.__generate_url_list(gender, i),
                    callback=self.get_deputados,
                    cb_kwargs=dict(
                        gender=gender
                    )
                )

        self.unify_csvs("./data/deputados/")


    def get_deputados(self, response, gender):
        names = response.css(
            'h3.lista-resultados__cabecalho > a::text'
        ).getall()

        ids = response.css('h3.lista-resultados__cabecalho > a').getall()
        ids = list(map(self.__get_id, ids))

        for i in range(len(names)):
            deputado = [
                ids[i],
                names[i],
                gender
            ]

            yield Request(
                f"{URL_DEPUTADO}/{ids[i]}",
                callback=self.get_deputado_info,
                cb_kwargs=dict(
                    dept_id=ids[i],
                    deputado=deputado
                )
            )


    def get_deputado_info(self, response, dept_id, deputado):
        presencas = list(
            map(
                lambda x: x.strip(),
                response.css("dd.list-table__definition-description::text").getall()
            )
        )
        deputado += presencas

        data_nascimento = self.__get_birthday(
            response.css("ul.informacoes-deputado > li::text").getall()
        )
        deputado += [ data_nascimento ]

        salario_bruto = self.__get_salary(
            response.css("a.beneficio__info::text").getall()
        )
        deputado += [ salario_bruto ]

        salario_bruto_par = None
        deputado += [ salario_bruto_par ]

        qnt_viagens = response.css("span.beneficio__info::text").getall()[-1]
        qnt_viagens = None if "Não" in qnt_viagens else qnt_viagens

        deputado += [ qnt_viagens ]

        par_url = html.unescape(
            self.__get_costs_par_url(
                response.css(
                    "a.veja-mais__item"
                ).getall()
            )
        )

        sleep(2)
        yield Request(
            par_url,
            callback=self.handle_par_costs,
            cb_kwargs=dict(
                dept_id=dept_id,
                deputado=deputado
            )
        )


    def handle_par_costs(self, response, dept_id, deputado):
        total = response.css("tr.mestre > td.numerico::text").getall()[0]
        deputado += [total]

        costs = list(
            map(
                lambda x: x.strip(),
                response.css("tr.detalhe > td.numerico::text").getall()
            )
        )

        months = self.__handle_months(
            response.css("tr.detalhe > th > a::text").getall()
        )

        costs_months = [None] * 12
        for index, month in enumerate(months):
            costs_months[months_index[month]] = costs[index]

        deputado += costs_months

        sleep(2)
        yield Request(
            f"https://www.camara.leg.br/deputados/{dept_id}/verba-gabinete?ano=2022",
            callback=self.handle_gab_costs,
            cb_kwargs=dict(
                dept_id=dept_id,
                deputado=deputado
            )
        )


    def handle_gab_costs(self, response, dept_id, deputado):
        data = response.css("tr > td::text").getall()

        results = [0 for i in range(12)]
        index = None
        for i in range(len(data)):
            if i % 3 == 0:
                index = int(data[i]) - 1
            if i % 3 == 2:
                results[index] = data[i].strip()

        deputado += [None]
        deputado += results

        df_deputado = pd.DataFrame(columns=COLUMNS)
        df_deputado.loc[0] = deputado
        df_deputado.to_csv(
            f"./data/deputados/deputado_{dept_id}.csv",
            index=False
        )


    def unify_csvs(self, dir_path):
        csv_names = self.__get_csv_list(dir_path)

        if len(csv_names) > 0:
            df_columns = pd.read_csv(f"{dir_path}/{csv_names[0]}").columns

            new_df = pd.DataFrame(columns=df_columns)

            print("Creating Data Frame")
            for file in tqdm(csv_names):
                data = pd.read_csv(f"{dir_path}/{file}")

                for row in data.itertuples(index=False):
                    new_df.loc[len(new_df.index)] = row

            new_df = new_df.reset_index(drop=True)

            if len(new_df) > 0:
                new_df.to_csv(
                    f"./data/deputados.csv",
                    index=False
                )


    def __get_csv_list(self, dir_path):
        result = []

        print("Searching file names")
        for path in tqdm(os.listdir(dir_path)):
            if os.path.isfile(os.path.join(dir_path, path)) and \
                ".csv" in path:
                result.append(path)

        return result


    def __handle_months(self, months_list):
        result = []
        for month in months_list:
            result.append(month.strip().split("/")[0].lower())

        return result


    def __get_costs_par_url(self, list_tags):
        result = ""
        for tag in list_tags:
            if "parlamentar" in tag:
                result = tag
                break

        result = result.split()[1].split('"')[1]

        return result


    def __get_salary(self, list_beneficio):
        for benef in list_beneficio:
            if "R$" in benef:
                result = benef.strip().split()
                result = ' '.join(result)
                return result

        return None


    def __get_birthday(self, list_infos):
        for info in list_infos:
            if "/" in info:
                return info.strip()

        return None


    def __get_id(self, tag):
        return tag.split()[1].split("/")[-1].split('"')[0]


    def __verify_corner_page(self, gender, page):
        if gender == "M":
            return ceil(509/25) >= page

        return ceil(89/25) >= page


    def __generate_url_list(self, gender, page):
        return f"{URL_LIST}&sexo={gender}&pagina={page}"
