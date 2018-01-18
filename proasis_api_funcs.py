import requests
import os

def get_json(url):
    # send API request and pull output as json
    data = '''{"username":"uzw12877","password":"uzw12877"}'''
    r = requests.get(url, data=data)
    json_string = r.json()

    return json_string


def dict_from_string(json_string):
    # empty dict and counter to enumerate json
    dict = {}
    counter = -1

    # reformat json into python dictionary
    for key in json_string.keys():
        try:
            counter += 1
            dict[key] = json_string.values()[counter].split(',')
        except:
            dict[key] = json_string.values()[counter]

    print dict

    return dict


def get_strucids_from_project(project):
    url = str("http://cs04r-sc-vserv-137.diamond.ac.uk/proasisapi/v1.4/projectlookup/" + project +
              "?strucsource=inh&idonly=1")

    json_string_strucids = get_json(url)
    dict_strucids = dict_from_string(json_string_strucids)
    try:
        strucids = list(dict_strucids['strucids'])

        return strucids
    except:
        return None

def delete_structure(strucid):
    delete_string = str('/usr/local/Proasis2/utils/removestruc.py -s ' + str(strucid))
    os.system(delete_string)

def delete_project(name):
    delete_string = str('/usr/local/Proasis2/utils/removeoldproject.py -p ' + str(name))
    os.system(delete_string)


def delete_all_inhouse(exception_list=['Zitzmann', 'Ali', 'CMGC_Kinases']):
    all_projects_url = 'http://cs04r-sc-vserv-137.diamond.ac.uk/proasisapi/v1.4/projects/'

    json_string_projects = get_json(all_projects_url)
    dict_projects = dict_from_string(json_string_projects)

    all_projects = dict_projects['ALLPROJECTS']

    for project in all_projects:
        project_name = str(project['project'])
        print project_name
        if project_name in exception_list:
            continue
        else:
            strucids = get_strucids_from_project(str(project_name))
            for strucid in strucids:
                print strucid
                delete_structure(strucid)
            delete_project(project_name)
