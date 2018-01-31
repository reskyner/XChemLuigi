import luigi, os
import data_in_proasis

class KickOff(luigi.Task):
    def output(self):
        return luigi.LocalTarget('pipeline.done')

    def requires(self):
        try:
            os.system('./pg_backup.sh')
            os.system('rm pipeline.done')
            os.system('rm /dls/science/groups/i04-1/software/luigi_pipeline/hits.done')
            os.system('rm /dls/science/groups/i04-1/software/luigi_pipeline/leads.done')
            os.system('rm /dls/science/groups/i04-1/software/luigi_pipeline/transfer.txt')
            os.system('rm /dls/science/groups/i04-1/software/luigi_pipeline/hits.done')
            os.system('rm /dls/science/groups/i04-1/software/luigi_pipeline/findprojects.done')
            os.system('rm /dls/science/groups/i04-1/software/luigi_pipeline/blacklists.done')
        except:
            print('Whoops...')

        return data_in_proasis.WriteBlackLists()

    def run(self):
        with self.output().open('wb') as f:
            f.write('')