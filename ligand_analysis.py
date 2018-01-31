import luigi
import data_in_proasis
import data_analysis_functions as daf
import db_functions as dbf
import pandas

class EdstatsScores(luigi.Task):
    strucid = luigi.Parameter()
    crystal = luigi.Parameter()

    def output(self):
        filename = str('./edstats' + self.crystal + '_' + self.strucid + '.done')
        return luigi.LocalTarget(filename)

    def run(self):
        results_dict = {'crystal': [], 'strucid': [], 'ligand': []}

        output_data, header = daf.run_edstats(self.strucid)
        if output_data:
            for ligand in output_data:

                lig_string = '-'.join([str(x) for x in ligand[0]])
                print lig_string
                results_dict['ligand'].append(lig_string)
                for j in range(0, len(header[24:36])):
                    if header[24 + j] not in results_dict.keys():
                        results_dict[header[24 + j]] = []
                    results_dict[header[24 + j]].append(str(ligand[1][24 + j]))
                results_dict['crystal'].append(self.crystal)
                results_dict['strucid'].append(self.strucid)

<<<<<<< HEAD
        #else:
            #raise Exception('No output data was found...')

=======
>>>>>>> parent of 2ac6350... changed my own permissions in blacklist, exception handling for edstats classes
        data_frame = pandas.DataFrame.from_dict(results_dict)
        # data_frame.to_csv('edstats_proasis_ligands.csv')
        # print data_frame


class StartEdstatsScores(luigi.Task):

    def requires(self):
        conn, c = dbf.connectDB()
        c.execute("select crystal_name, strucid from proasis_hits where strucid !=''")
        rows = c.fetchall()

        crystal_list=[]
        strucid_list=[]

        for row in rows:
            crystal_list.append(str(row[0]))
            strucid_list.append(str(row[1]))

        list = zip(crystal_list, strucid_list)

        return data_in_proasis.StartHitTransfers(), \
               [EdstatsScores(crystal=crystal_name, strucid=strucid_no)
               for (crystal_name, strucid_no) in list]

    def output(self):
        return luigi.LocalTarget('edstats.done')

    def run(self):
        with self.output().open('wb') as f:
            f.write('')