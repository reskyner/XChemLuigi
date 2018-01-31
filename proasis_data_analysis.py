import proasis_api_funcs as paf
import os
import subprocess


def write_temp_file(json_dict, type):
    for i in range(0, len(json_dict['output'])):
        with open(str('temp.' + type), 'a') as f:
            f.write(json_dict['output'][i])

def fetch_data(type, strucid):
    fetch_url = str('http://cs04r-sc-vserv-137.diamond.ac.uk/proasisapi/v1.4/fetchfile/' + type + '/' + strucid)
    fetch_json = paf.get_json(fetch_url)
    fetch_dict = paf.dict_from_string(fetch_json)

    return fetch_dict

def run_analysis(strucid):
    mtz_dict = fetch_data('mtz', strucid)
    write_temp_file(mtz_dict, 'mtz')

    pdb_dict = fetch_data('originalpdb', strucid)
    write_temp_file(pdb_dict, 'pdb')

    os.system('source /dls/science/groups/i04-1/software/pandda-update/ccp4/ccp4-7.0/bin/ccp4.setup-sh')
    giant_score_string = 'giant.score_model temp.pdb temp.mtz'
    process = subprocess.Popen(giant_score_string, stdout=subprocess.PIPE, shell=True)
    out, err = process.communicate()

    print out

    print err

    #os.system('rm temp.pdb')
    #os.system('rm temp.mtz')

def on_the_fly_analysis():
    import db_functions
    import os

    # set filepaths
    hit_directory = '/dls/science/groups/proasis/LabXChem/'

    conn, c = db_functions.connectDB()
    c.execute("SELECT bound_conf, crystal_name, protein, strucid FROM proasis_hits WHERE strucid !=''")
    rows = c.fetchall()

    for row in rows:
        bound_pdb = str(row[0])
        protein_name = str(row[2])
        crystal = str(row[1])
        strucid = str(row[3])

        # set up directory paths for where files will be stored (for proasis)
        proasis_protein_directory = str(str(hit_directory) + '/' + str(protein_name) + '/')
        proasis_crystal_directory = str(str(hit_directory) + '/' + str(protein_name) + '/'
                                        + str(crystal) + '/')

        pdb_file_name = str(bound_pdb).split('/')[-1]

        # if the bound pdb is in a refinement folder, change the path to find the map files
        if 'Refine' in bound_pdb.replace(pdb_file_name, ''):
            remove_string = str(str(bound_pdb).split('/')[-2] + '/' + pdb_file_name)
            map_directory = str(bound_pdb).replace(remove_string, '')
        else:
            map_directory = str(bound_pdb).replace(pdb_file_name, '')

        print('Analysing ' + crystal + ' (' + strucid + ')')
        #os.system('module unload ccp4; source /dls/science/groups/i04-1/software/pandda-update/ccp4/ccp4-7.0/bin/ccp4.setup-sh; ')
        giant_score_string = str('module unload ccp4; '
                                 'source /dls/science/groups/i04-1/software/pandda-update'
                                 '/ccp4/ccp4-7.0/bin/ccp4.setup-sh; giant.score_model ' +
                                 str(bound_pdb) + ' ' +
                                 str(proasis_crystal_directory + '/refine.mtz'))

        process = subprocess.Popen(giant_score_string, stdout=subprocess.PIPE, shell=True)
        out, err = process.communicate()

        print out
        print err


