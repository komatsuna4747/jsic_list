import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
from logging import getLogger

logger = getLogger(__name__)


class JSICDefinitionExtractor:

    def __init__(self):
        self.dict_jsic_code = None

    def get_jsic_code(self) -> None:

        url = "https://www.soumu.go.jp/toukei_toukatsu/index/seido/sangyo/02toukatsu01_03000044.html"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "lxml")

        # Divisions
        code_division = [division.text.split()[1] for division in soup.find_all("h2")]
        
        # Major groups
        code_major_group = [major_group.text.split()[1] for major_group in soup.find_all("h3")]

        # Groups and details
        code_group, code_detail = [], []
        for tag in soup.find_all("li", attrs={"style":"list-style-type:none"}):
            tag = tag.text.split()
            if len(tag[0]) == 3:
                code_group.append(tag[0])
            else:
                code_detail.append(tag[0])
        
        self.dict_jsic_code = {
            "code_division": code_division,
            "code_major_group": code_major_group,
            "code_group": code_group,
            "code_detail": code_detail
        }

    def get_jsic_definition(self, classification: str) -> pd.DataFrame:

        if classification not in ["division", "major_group", "group", "detail"]:
            raise ValueError("'classification' must be either 'division', 'major_group', 'group', or 'detail'.")

        # Get JSIC codes
        self.get_jsic_code()
        code_jsic = self.dict_jsic_code[f"code_{classification}"]

        logger.info(f"Number of {classification}: {len(code_jsic)}")

        list_df = []

        for count, code in enumerate(code_jsic):
            if (count + 1) % 10 == 0:
                logger.info(f"Progress of extracting JSIC {classification}: {count + 1} / {len(code_jsic)}")

            time.sleep(2)
            url = f"https://www.e-stat.go.jp/classifications/terms/10/03/{code}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "lxml")

            dict_raw = dict(
                zip(
                    [var.text for var in soup.find_all("th")],
                    [value.text for value in soup.find_all("td")]
                )
            )      

            dict_jsic = {}

            # Classification
            for tag in [("大分類", "division"), ("中分類", "major_group"), ("小分類", "group"), ("細分類", "detail")]:
                if tag[0] in dict_raw.keys():
                    list_tag = dict_raw[tag[0]].split()
                    dict_jsic[f"code_{tag[1]}"] = list_tag[0]
                    dict_jsic[f"label_{tag[1]}"] = list_tag[1]
            
            # Description
            for key, value in dict_raw.items():
                if "説明" in key:
                    dict_jsic[f"description_{classification}"] = value.replace("　", "").replace(" ", "").replace("総説", "")

            # Example (for detail)
            if classification == "detail":
                for var in [("事例", "example"), ("不適合事例", "unsuitable_example")]:
                    if var[0] not in dict_raw.keys():
                        dict_jsic[var[1]] = None
                    else:
                        dict_jsic[var[1]] = [dict_raw[var[0]].split("；")]

            # Append the dictionary
            list_df.append(pd.DataFrame(dict_jsic, index=[0]))
        
        return pd.concat(list_df).reset_index(drop=True)
