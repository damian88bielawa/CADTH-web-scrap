import os
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import pdfplumber
from datetime import datetime

#------------MAIN SCRAPER--------------
def pages_scrap():
    main_table = []
    for numer in range(0,5,1):
            print(numer)
            url = f'https://www.cadth.ca/reimbursement-review-reports?search_api_fulltext=&field_project_type=All&items_per_page=50&page={numer}'
            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')

            brands = brand_name(soup)
            links = global_links(soup)
            substa = substance_name(soup)
            indica = indication_main_name(soup)
            recommend = recommendation_general(soup)
            end = zlec_end_date(soup)
            start = zlec_start_date(soup)
            project_page_scrap = simple_page_scrap(links)

            #cadth don't have these same process pages - they have differencies. Below code check if lengh of scraped list are identicall. If not - there must by error
            if (len(brands) and len(substa) and len(indica) and len(recommend) and len(end) and len(start)) == len(links):
                print("List are ok")
            else:
                print('Error')
                print(f"Brandy: {len(brands)}")
                print(f"Linki: {len(links)}")
                print(len(substa))
                print(len(indica))
                print(len(recommend))
                print(len(end))
                print(len(start))
                break

            for brand, link, substance, indication, recommendation, end_date, start_date, project_page in zip(brands, links, substa, indica, recommend, end, start, project_page_scrap):
                        zlec = {'brand': brand, 'link': link, 'substance': substance, 'indication': indication, 'recommendation': recommendation, 'company': project_page['manufacturer'], 'long_tag': project_page['project'], 'start_date': start_date, 'Submission received date': project_page['Submission received date'],
                                'Submission accepted date': project_page['Submission accepted date'], 'Review initiated': project_page['Review initiated'], 'Frist Draft review': project_page['Draft review'],
                                'First CADTH body meeting': project_page['First CADTH body meeting'], 'end_date': end_date, 'Final recommendation': project_page['Final recommendation'], 'Links': project_page['Links']}
                        main_table.append(zlec)

    return main_table



#------------ process link download start--------------
#create a list of process links
#cadtch reimbursement reviews pagination is incrementation by 1 at the end. 

def global_links(soup):
    # in urls_list list of url for each process
    ulrs_list = []
    for link in soup.find_all('td', class_='views-field views-field-field-brand-name is-active'):
        # looking for anchor tag inside the <td>tag
        a = link.find('a')
        try:
            # looking for href inside anchor tag
            if 'href' in a.attrs:
                # storing the value of href in a separate variable
                url = a.get('href')
                # appending the url to the output list
                ulrs_list.append("https://www.cadth.ca" + url)
        # if the list does not has a anchor tag or an anchor tag
        # does not has a href params we pass
        except:
            pass

    return ulrs_list

#------------ process link download end--------------

#------------scrap basic process data (from main table) start --------------
def brand_name(soup):
    brand_zlec = []
    for zlec in soup.find_all('td', class_='views-field views-field-field-brand-name is-active'):
        brand_zlec.append(zlec.text.strip())
        if zlec.text == '':
            brand_zlec.append("")
    return brand_zlec


def substance_name(soup):
  substance_zlec = []
    for zlec in soup.find_all('td', class_='views-field views-field-field-generic-name'):
        substance_zlec.append(zlec.text.strip().lower())
        if zlec.text == '':
            substance_zlec.append("")
    return substance_zlec


def indication_main_name(soup):
    # szuka textu z nazwą wskazania (głownego)
    main_indication_zlec = []
    for zlec in soup.find_all('td', class_='views-field views-field-field-therapeutic-area'):
        main_indication_zlec.append(zlec.text.strip())
        if zlec.text == '':
            main_indication_zlec.append("")

    return main_indication_zlec


def recommendation_general(soup):
    main_recommendation_zlec = []
    for zlec in soup.find_all('td', class_='views-field views-field-field-recommendation-type'):
        main_recommendation_zlec.append(zlec.text.strip())
        if zlec.text == '':
            main_recommendation_zlec.append("")
    return main_recommendation_zlec


def zlec_start_date(soup):
    start_date_zlec = []
    for zlec in soup.find_all('td', class_='views-field views-field-field-date-submission-received'):
        aa = zlec.text.strip()
        if aa is not None:
            try:
                bb = str(datetime.strptime(aa, '%b %d, %Y').date())
                start_date_zlec.append(str(bb))
            except:
                start_date_zlec.append("")
        if zlec.text == '':
            start_date_zlec.append("")
    return start_date_zlec


def zlec_end_date(soup):
    end_date_zlec = []
    for zlec in soup.find_all('td', class_='views-field views-field-field-final-recommendation-cdr-1'):
        aa = zlec.text.strip()
        if aa is not None:
            try:
                bb = datetime.strptime(aa, '%b %d, %Y').date()
                end_date_zlec.append(str(bb))
            except:
                end_date_zlec.append("")
        if zlec.text == '':
            end_date_zlec.append("")
    return end_date_zlec
#------------scrap basic process data end --------------


#------------download documents for each process start--------------
def pdf_downloader(pdf_links):
    #if there is a text that may be a pdf with recommendation the download it
    #create a folder in desktop
    folder_location = r'xxxxxxxxxx'
    if not os.path.exists(folder_location): os.mkdir(folder_location)
    response = requests.get(pdf_links)

    if str(pdf_links).count("cdr/complete/") > 0 or str(pdf_links).count("_fn_rec.") > 0 or str(pdf_links).count('Rec-Final.') > 0 or str(pdf_links).count('%20Final.pdf') or str(pdf_links).count('Final%20Recommendation'):
        s = re.sub('^(?s:.*)/', "", str(pdf_links))
        if 'pdf' in s:
            filename = os.path.join(folder_location, s)
        else:
            filename = os.path.join(folder_location, s + ".pdf")
        print(f"Downloading File: {filename}")
        with open(filename, 'wb') as f:
            f.write(response.content)
        scrap = {}
        with pdfplumber.open(filename) as pdf:
            page = pdf.pages[0]
            text = page.extract_text().replace('\uf0b7', '')
            text = " ".join(text.split())

            scrap['text'] = text
            scrap["file_name"] = filename
                # create a list with the keywords extracted from current document
        return scrap
    else:
        pass
#------------download documents for each process end--------------

#------------scrap each process page (more detailed info) start--------------
def simple_page_scrap(links):

    pages = []
    for link in links:
        r = requests.get(link)
        soup = BeautifulSoup(r.text, 'html.parser')
        #dict for one page
        page = {}

        #BASIC FROM PAGE
        #------------
        #Pharma Companies, form each of specific assessement
        manufacturer = soup.find('div',
                                 class_='field field--name-field-manufacturer field--type-string field--label-above field__item')
        if manufacturer is not None:
            page['manufacturer'] = manufacturer.text.strip()
        else:
            try:
                page['manufacturer'] = soup.find('div', class_="field field--name-field-manufacturer-pcodr field--type-string field--label-above field__item").text.strip()
            except:
                page['manufacturer'] = ''

        # ------------
        # Project Number, form each of specific assessement  = LONG TAG
        project = soup.find('div',
                                 class_='field field--name-field-project-number field--type-string field--label-above field__item')
        if project is not None:
            page['project'] = project.text.strip()
        else:
            page['project'] = ''

        #DATES FROM KEY MILESTONES

        #-------------
        #sub received
        sub_rec_date = soup.find('th', text=lambda t: t in ('Submission Date', 'Submission received'))
        #companies = []
        try:
            page['Submission received date'] = sub_rec_date.find_next('td').text
        except:
            try:
                page['Submission received date'] = soup.find('div', class_="field field--name-field-submission-date field--type-datetime field--label-above field__item").text.strip()
            except:
                page['Submission received date'] = ''

            #companies.append('')

        # --------------
        #sub accepted
        sub_acc_date = soup.find('th', text=lambda t: t in ('Submission accepted', 'Submission Deemed Complete'))
        #companies = []
        if sub_acc_date is not None:
            try:
                page['Submission accepted date'] = sub_acc_date.find_next('td').text
            except:
                page['Submission accepted date'] = ''
        else:
            try:
                page['Submission accepted date'] = soup.find('div',
                                                             class_="field field--name-field-submission-deemed-complete field--type-datetime field--label-above field__item").text.strip()
            except:
                page['Submission accepted date'] = ''

        # --------------
        #Review initiated
        rev_init = soup.find('th', text='Review initiated')
        #companies = []
        if rev_init is not None:
            try:
                page['Review initiated'] = rev_init.find_next('td').text
            except:
                page['Review initiated'] = ''
        else:
            try:
                page['Review initiated'] = soup.find('div',
                                                             class_="field field--name-field-patient-input-deadline field--type-datetime field--label-above field__item").text.strip()
            except:
                page['Review initiated'] = ''

        # --------------
        #First Draft review
        draft_rev = soup.find('th', text=lambda t: t in ('Draft CADTH review report(s) sent to sponsor', 'Initial Recommendation', 'Draft CADTH review report(s) provided to sponsor for comment'))
        if draft_rev is not None:
            try:
                page['Draft review'] = draft_rev.find_next('td').text
            except:
                page['Draft review'] = ''
        else:
            try:
                page['Draft review'] = soup.find('div',
                                                     class_="field field--name-field-initial-recommendation field--type-datetime field--label-above field__item").text.strip()
            except:
                page['Draft review'] = ''

        # --------------
        #First CADTH body meeting
        cadth_meeting = soup.find('th', text=lambda t: t in ('pERC Meeting', 'Expert committee meeting (initial)', 'Canadian Drug Expert Committee (CDEC) meeting', 'Expert Committee meeting (initial)'))
        if cadth_meeting is not None:
            try:
                page['First CADTH body meeting'] = cadth_meeting.find_next('td').text
            except:
                page['First CADTH body meeting'] = ''
        else:
            try:
                page['First CADTH body meeting'] = soup.find('div',
                                                 class_="field field--name-field-perc-meeting field--type-datetime field--label-above field__item").text.strip()
            except:
                page['First CADTH body meeting'] = ''


        # --------------
        #CADTH final recommendation
        final_recomendation = soup.find('th', text=lambda t: t in ('CDEC Final Recommendation posted', 'Final Recommendation posted', 'Final Recommendation Issued', 'Final recommendation posted', 'CDEC Final recommendation posted'))
        if final_recomendation is not None:
            try:
                page['Final recommendation'] = final_recomendation.find_next('td').text
            except:
                page['Final recommendation'] = ''
        else:
            try:
                page['Final recommendation'] = soup.find('div',
                                                             class_="field field--name-field-final-recommendation field--type-datetime field--label-above field__item").text.strip()
            except:
                page['Final recommendation'] = ''


        # --------------
        #document links + document link name + RECOMENDATION TEXT FROM PDF
        documents_tag = soup.find_all('a', class_='project-file')

        if documents_tag is not None:
            document_links = []
            for link in documents_tag:
                if 'href' in link.attrs:
                    ass_links = {}
                    try:
                        if  "cadth.ca" in link.get('href'):
                            url = link.get('href')
                        else:
                            url = "https://www.cadth.ca" + link.get('href')
                        # appending the url to the output list

                        ass_links['Link'] = url
                        #ap_link = []
                        #ap_link.append(pdf_downloader(url))
                        document_link_text = link.find('span',
                                                       class_='doc-title').text.strip().replace(
                            '\n', '')
                        ass_links['link name'] = document_link_text
                        #ass_links['Recommendation text'] = ap_link

                        document_links.append(ass_links)
                    except:
                        document_links = ''
            page['Links'] = document_links
        else:
            page['Links'] = ''

        #Create list of dicts for link
        pages.append(page)
    return pages

#------------scrap each process page (more detailed info) end--------------

#------------save as csv--------------

def main():

    df = pd.DataFrame(pages_scrap())
    df.to_csv("CADTH2023.csv", index=False)
#------------save as csv end--------------

if __name__ == '__main__':
    main()
