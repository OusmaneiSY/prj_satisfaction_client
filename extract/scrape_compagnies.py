import requests
import json
import pandas as pd
from bs4 import BeautifulSoup as bs


def get_company_data_from_trustpilot(company_name):
    """
    Get HTML code from Trustpilot website review page

    Args:
        company_name (str): Name of the company.

    Returns:
        str: Text content of the HTML code
    """

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"}
    page_url = "https://www.trustpilot.com/review/{}".format(company_name)
    page_html = requests.get(page_url, headers=headers)

    return page_html.content


def parse_company_data(company_data_html):
    """
    Parses HTML content to extract company information

    Args:
        company_data_html (bytes): bytes object containing the HTML content

    Returns:
        dict: company information
    """

    soup = bs(company_data_html, "lxml")
    
    company_raw_data = soup.find("script",attrs={"id" : "__NEXT_DATA__"})
   
    company_json_data = json.loads(company_raw_data.text)

    company_details_data = company_json_data["props"]["pageProps"]["businessUnit"]
       
    if len(company_details_data['categories']) == 1:
        category = company_details_data['categories'][0]["name"]
    else:
        for item in company_details_data['categories']:
            if item['isPrimary'] == True:
                category = item["name"]
        
    company_dict_data = {
                        'id': company_details_data['id'],
                        'displayName' : company_details_data['displayName'],
                        'numberOfReviews' : company_details_data['numberOfReviews'],
                        'trustScore' : company_details_data['trustScore'],
                        'websiteUrl' : company_details_data['websiteUrl'],
                        'stars' : company_details_data['stars'],
                        'category' : category,
                        'email' : company_details_data['contactInfo']['email'],
                        'address' : company_details_data['contactInfo']['address'],
                        'city' : company_details_data['contactInfo']['city'],
                        'country' : company_details_data['contactInfo']['country'],
                        'phone' : company_details_data['contactInfo']['phone'],
                        'zipCode' : company_details_data['contactInfo']['zipCode'],
                        'five-star-rating-percent' : soup.find("label",attrs={"data-star-rating" : "five"}).find_next("p",attrs={"data-rating-distribution-row-percentage-typography" : "true"}).text,
                        'four-star-rating-percent' : soup.find("label",attrs={"data-star-rating" : "four"}).find_next("p",attrs={"data-rating-distribution-row-percentage-typography" : "true"}).text,
                        'three-star-rating-percent' : soup.find("label",attrs={"data-star-rating" : "three"}).find_next("p",attrs={"data-rating-distribution-row-percentage-typography" : "true"}).text,
                        'two-star-rating-percent' : soup.find("label",attrs={"data-star-rating" : "two"}).find_next("p",attrs={"data-rating-distribution-row-percentage-typography" : "true"}).text,
                        'one-star-rating-percent' : soup.find("label",attrs={"data-star-rating" : "one"}).find_next("p",attrs={"data-rating-distribution-row-percentage-typography" : "true"}).text
                        }

    return company_dict_data


def create_company_data_dataframe(company_list):
    """
    Collect information of companies and store it in a dataframe.

    Args:
        company_list (list(str)): list of company names

    Returns:
        dataFrame: company information
    """
    # create an empty dataframe to store gathered company information
    temp_df = pd.DataFrame()

    # loop to get company information and store it in companies_df dataframe
    for company in company_list:
        # collect and parse information of the company
        company_row = parse_company_data(get_company_data_from_trustpilot(company))
        # store collected information as a new raw in companies_df dataframe
        temp_df = pd.concat([temp_df, pd.DataFrame([company_row])], ignore_index=False)

    # set the companies_df index to 'id' column
    temp_df = temp_df.set_index('id')

    return temp_df


def main_scrape_companies():
    # create the list of company names we want to get information from Trustpilot
    companies = ["www.showroomprive.com","loaded.com","westernunion.com","justfly.com","www.facebook.com"]

    # collect company information in a dataframe 
    companies_df = create_company_data_dataframe(companies)

    # write the content of companies_df to a csv file
    companies_df.to_csv("companies_information.csv")


def test_get_company_data_from_trustpilot():
    output = str(get_company_data_from_trustpilot("www.showroomprive.com")).find("www.showroomprive.com")
    assert output != -1


def test_parse_company_data():
    output = parse_company_data(get_company_data_from_trustpilot("www.showroomprive.com"))["displayName"]
    assert output == "Showroomprive"


if __name__ == "__main__":
    print("Récupération des données globales des entreprises...")
    main_scrape_companies()