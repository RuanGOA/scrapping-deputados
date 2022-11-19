import os
import pandas as pd
from tqdm import tqdm


def get_csv_list(dir_path):
    result = []

    print("Searching file names")
    for path in tqdm(os.listdir(dir_path)):
        if os.path.isfile(os.path.join(dir_path, path)) and \
            ".csv" in path:
            result.append(path)

    return result


def unify_csvs(dir_path):
    csv_names = get_csv_list(dir_path)

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
                "./data/deputados.csv",
                index=False
            )


if __name__ == "__main__":
    unify_csvs("./data/deputados/")
