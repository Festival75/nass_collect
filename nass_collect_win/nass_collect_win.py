import requests
from bs4 import BeautifulSoup
import json
import re
import urllib.request
import os


def read_config(path):
    try:
        with open('config_win.json') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        print('config_win.json not found in {0}.'.format(path))
        exit()
    return config


def get_url_content(url, session):
    request = session.get(url)
    content = BeautifulSoup(request.content, "lxml")
    return content


def get_summary_case_info(content, config):
    result = []
    case_info_block = content.find("div", {"class": config['class']['case_info_block']})
    tables = case_info_block.find_all('table')
    for table in tables:
        table_rows = table.find_all('tr')
        for row in table_rows:
            titles = row.find_all("div", {"class": "heading"})
            headers = row.find_all('th')
            headers_list = []
            datas = row.find_all('td')
            data_list = []
            for header in headers:
                headers_list.append(header.text)

            for data in datas:
                data_list.append(data.text)

            headers_list = list(filter(None, headers_list))
            data_list = list(filter(None, data_list))
            result_str = ', '.join(headers_list) + ' ' + ', '.join(data_list)
            result.append(result_str)
    return result


def get_case_photos(content, config):
    urls = []
    names = []
    photo_ids = content.find_all("td", text=re.compile('\\b(Image ID).+\\b'))
    for photo_id in photo_ids:
        image_url = 'https://www-nass.nhtsa.dot.gov/nass/cds/'
        id_string = re.findall("\\b\d+\\b", photo_id.text)
        image_src_ver1 = 'GetBinary.aspx?Image&ImageID=' + id_string[0] + '&CaseID=' + config['case_id'] + '&Version=1'
        image_src_ver0 = 'GetBinary.aspx?Image&ImageID=' + id_string[0] + '&CaseID=' + config['case_id'] + '&Version=0'
        image = content.find("img", {"src": image_src_ver1})
        if image is None:
            image = content.find("img", {"src": image_src_ver0})
            name = image.get("alt")
            image_url += image_src_ver0
        else:
            image_url += image_src_ver1
            name = image.get("alt")
        for char in name:
            if char in ":":
                name = name.replace(char, '')
            if char in " =/\\()":
                name = name.replace(char, '_')
        names.append(name)
        urls.append(image_url)
    return urls, names


def make_result_folder(config):
    if not os.path.exists(config['path_to_save'] + 'Case_' + config['case_id'] + '\images\Vehicle1\\'):
        os.makedirs(config['path_to_save'] + 'Case_' + config['case_id'] + '\images\Vehicle1\\')
    if not os.path.exists(config['path_to_save'] + 'Case_' + config['case_id'] + '\images\Vehicle2\\'):
        os.makedirs(config['path_to_save'] + 'Case_' + config['case_id'] + '\images\Vehicle2\\')


def data_to_txt(data, config):
    with open(config['path_to_save'] + 'Case_' + config['case_id'] + '\info.txt', "w") as file:
        for row in data:
            file.write(row)
            file.write('\n')


def main():
    config = read_config('config_win.json')
    make_result_folder(config)
    session = requests.session()
    request = session.get('https://www-nass.nhtsa.dot.gov/nass/cds/CaseForm.aspx?ViewText&CaseID=' + config['case_id'] + '&xsl=textonly.xsl&websrc=true')
    content = BeautifulSoup(request.content, "lxml")
    #content = BeautifulSoup(open("/home/mikhail/PycharmProjects/nass_collect_win/web/crash_overview.html"), "lxml")
    urls, names = get_case_photos(content, config)
    count = 0
    for url in urls:
        print(config['path_to_save'] + 'Case_' + config['case_id'] + '\images\\' + names[count] + ".jpg")
        urllib.request.urlretrieve(url, config['path_to_save'] + 'Case_' + config['case_id'] + '/images/' + names[count] + ".jpg")
        count += 1
    summary_case_info = get_summary_case_info(content, config)
    data_to_txt(summary_case_info, config)


if __name__ == '__main__':
    main()
