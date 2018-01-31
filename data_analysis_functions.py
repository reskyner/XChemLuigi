import proasis_api_funcs as paf
import os

def run_edstats(strucid):

    working_directory = os.getcwd()

    print('running edstats for ' + strucid + '...')

    os.system('source /dls/science/groups/i04-1/software/pandda-update/ccp4/ccp4-7.0/bin/ccp4.setup-sh')
    if not os.path.isdir('temp'):
        os.mkdir('temp')
    os.chdir('temp')

    mtz_file = paf.get_struc_mtz(strucid, '.')
    if mtz_file:
        pdb_file = paf.get_struc_pdb(strucid, str(strucid + '.pdb'))
        if pdb_file:
            print('writing temporary edstats output...')
            os.system('source /dls/science/groups/i04-1/software/pandda-update/ccp4/ccp4-7.0/bin/ccp4.setup-sh; '
                      'edstats.pl -hklin=' + mtz_file + ' -xyzin=' + pdb_file + ' -out=edstats.out > temp.out')
            # print('reading temporary edstats output...')
            with open('edstats.out', 'r') as f:
                output = f.read().strip().replace('\r\n', '\n').replace('\r', '\n').splitlines()

            if output:
                header = output.pop(0).split()
                assert header[:3] == ['RT', 'CI', 'RN'], 'edstats output headers are not as expected! {!s}'.format(output)
                num_fields = len(header)
                header = header[3:]
            else:
                header = []

                # List to be returned
            outputdata = []

            # Process the rest of the data
            for line in output:
                line = line.strip()
                if not line:
                    continue

                    fields = line.split()
                    if len(fields) != num_fields:
                        raise ValueError("Error Parsing EDSTATS output: Header & Data rows have different numbers of fields")

                    # Get and process the residue information
                    residue, chain, resnum = fields[:3]
                    try:
                        resnum = int(resnum)
                        inscode = ' '
                    except ValueError:
                        inscode = resnum[-1:]
                        resnum = int(resnum[:-1])

                    # Remove the processed columns
                    fields = fields[3:]

                    # Process the other columns (changing n/a to None and value to int)
                    for i, x in enumerate(fields):
                        if x == 'n/a':
                            fields[i] = None
                        else:
                            try:
                                fields[i] = int(x)
                            except:
<<<<<<< HEAD
                                try:
                                    fields[i] = float(x)
                                except:
                                    fields[i] = x

                    # print residue
                    if 'LIG' in residue:
                        outputdata.append([[residue, chain, resnum], fields])
            #else:
                #raise Exception('No output found!')
        else:
            try:
                os.system('rm ' + mtz_file)
                os.system('rm ' + mtz_file + '.gz')
            except:
                print('problem removing files')
=======
                                fields[i] = x

                # print residue
                if 'LIG' in residue:
                    outputdata.append([[residue, chain, resnum], fields])
>>>>>>> parent of 2ac6350... changed my own permissions in blacklist, exception handling for edstats classes

    else:
<<<<<<< HEAD
        try:
            os.system('rm ' + mtz_file)
            os.system('rm ' + mtz_file + '.gz')
        except:
            print('problem removing files')

        raise Exception('No mtz file found for ' + strucid + ' so not running edstats!')
=======
        pdb_file = None
        outputdata = None
        header = None
        print('No mtz file found for ' + strucid + ' so not running edstats!')
>>>>>>> parent of 2ac6350... changed my own permissions in blacklist, exception handling for edstats classes

    try:
        os.system('rm ' + pdb_file)
        os.system('rm ' + mtz_file)
        os.system('rm ' + mtz_file + '.gz')
        os.system('rm edstats.out')
    except:
        print('problem removing files')

    os.chdir(working_directory)

    return outputdata, header