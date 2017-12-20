import luigi
import subprocess
import os
import datetime
import logging
import db_functions, misc_functions

class FindSoakDBFiles(luigi.Task):
    # date parameter - needs to be changed
    date = luigi.DateParameter(default=datetime.date.today())

    # filepath parameter can be changed elsewhere
    filepath = luigi.Parameter(default="/dls/labxchem/data/*/lb*/*")

    def output(self):
        return luigi.LocalTarget(self.date.strftime('soakDBfiles/soakDB_%Y%m%d.txt'))

    def run(self):
        # maybe change to *.sqlite to find renamed files? - this will probably pick up a tonne of backups
        process = subprocess.Popen(str('''find ''' + self.filepath +  ''' -maxdepth 5 -path "*/lab36/*" -prune -o -path "*/initial_model/*" -prune -o -path "*/beamline/*" -prune -o -path "*/analysis/*" -prune -o -path "*ackup*" -prune -o -path "*old*" -prune -o -path "*TeXRank*" -prune -o -name "soakDBDataFile.sqlite" -print'''),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        # run process to find sqlite files
        out, err = process.communicate()

        # write filepaths to file as output
        with self.output().open('w') as f:
            f.write(out)


class CheckFiles(luigi.Task):
    date = luigi.DateParameter(default=datetime.date.today())
    def requires(self):
        conn, c = db_functions.connectDB()
        exists = db_functions.table_exists(c, 'soakdb_files')
        if not exists:
            return TransferAllFedIDsAndDatafiles()
        else:
            return FindSoakDBFiles()

    def output(self):
        return luigi.LocalTarget('new_soakdb_files.txt')

    def run(self):
        logfile = self.date.strftime('transfer_logs/CheckFiles_%Y%m%d.txt')
        logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s %(message)s',
                            datefrmt='%m/%d/%y %H:%M:%S')

        conn, c = db_functions.connectDB()
        exists = db_functions.table_exists(c, 'soakdb_files')

        checked = []
        #changed = []
        new = []

        # Status codes:-
        # 0 = new
        # 1 = changed
        # 2 = not changed

        if exists:
            with self.input().open('r') as f:
                files = f.readlines()

            for filename in files:

                filename_clean = filename.rstrip('\n')

                c.execute('select filename, modification_date from soakdb_files where filename like %s;', (filename_clean,))

                for row in c.fetchall():
                    if len(row) > 0:
                        data_file = str(row[0])
                        checked.append(data_file)
                        old_mod_date = str(row[1])
                        current_mod_date = misc_functions.get_mod_date(data_file)

                        if current_mod_date > old_mod_date:
                            logging.info(str(data_file) + ' has changed!')
                            #changed.append(data_file)
                            c.execute('UPDATE soakdb_files SET status_code = 1 where filename like %s;', (filename_clean,))
                            c.execute('UPDATE soakdb_files SET modification_date = %s where filename like %s,;', (current_mod_date, filename_clean))
                            conn.commit()
                            # start class to add row and kick off process for that file
                        else:
                            logging.info(str(data_file) + ' has not changed!')
                            c.execute('UPDATE soakdb_files SET status_code = 2 where filename like %s;', (filename_clean,))
                            conn.commit()

            c.execute('select filename from soakdb_files;')

            for row in c.fetchall():
                if str(row[0]) not in checked:
                    data_file = str(row[0])
                    file_exists = os.path.isfile(data_file)

                    if not file_exists:
                        logging.warning(str(data_file) + ' no longer exists! - notify users!')

                    else:
                        logging.info(str(row[0]) + ' is a new file!')
                        # the piece of code below is dumb - the entry does not exist yet!
                        # c.execute('UPDATE soakdb_files SET status_code = 0 where filename like %s;', (filename_clean,))
                        # conn.commit()
                        new.append(str(row[0]))

        new_string = ''
        for i in new:
            new_string += str(i + ',')

        with self.output().open('w') as f:
            f.write(new_string)

class TransferAllFedIDsAndDatafiles(luigi.Task):
    # date parameter for daily run - needs to be changed
    date = luigi.DateParameter(default=datetime.date.today())

    # needs a list of soakDB files from the same day
    def requires(self):
        return FindSoakDBFiles()

    # output is just a log file
    def output(self):
        return luigi.LocalTarget(self.date.strftime('transfer_logs/fedids_%Y%m%d.txt'))

    # transfers data to a central postgres db
    def run(self):
        # connect to central postgres db
        conn, c = db_functions.connectDB()
        # create a table to hold info on sqlite files
        c.execute('''CREATE TABLE IF NOT EXISTS soakdb_files (id SERIAL UNIQUE PRIMARY KEY, filename TEXT, modification_date BIGINT, proposal TEXT, status_code INT)'''
                  )
        conn.commit()

        # set up logging
        logfile = self.date.strftime('transfer_logs/fedids_%Y%m%d.txt')
        logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s %(message)s',
                            datefrmt='%m/%d/%y %H:%M:%S')

        # use list from previous step as input to write to postgres
        with self.input().open('r') as database_list:
            for database_file in database_list.readlines():
                database_file = database_file.replace('\n', '')

                # take proposal number from filepath (for whitelist)
                proposal = database_file.split('/')[5].split('-')[0]
                proc = subprocess.Popen(str('getent group ' + str(proposal)), stdout=subprocess.PIPE, shell=True)
                out, err = proc.communicate()

                # need to put modification date to use in the proasis upload scripts
                modification_date = misc_functions.get_mod_date(database_file)
                c.execute('''INSERT INTO soakdb_files (filename, modification_date, proposal) SELECT %s,%s,%s WHERE NOT EXISTS (SELECT filename, modification_date FROM soakdb_files WHERE filename = %s AND modification_date = %s)''', (database_file, int(modification_date), proposal, database_file, int(modification_date)))
                conn.commit()

                logging.info(str('FedIDs written for ' + proposal))

        c.execute('CREATE TABLE IF NOT EXISTS proposals (proposal TEXT, fedids TEXT)')

        proposal_list = []
        c.execute('SELECT proposal FROM soakdb_files')
        rows = c.fetchall()
        for row in rows:
            proposal_list.append(str(row[0]))

        for proposal_number in set(proposal_list):
            proc = subprocess.Popen(str('getent group ' + str(proposal_number)), stdout=subprocess.PIPE, shell=True)
            out, err = proc.communicate()
            append_list = out.split(':')[3].replace('\n', '')

            c.execute(str('''INSERT INTO proposals (proposal, fedids) SELECT %s, %s WHERE NOT EXISTS (SELECT proposal, fedids FROM proposals WHERE proposal = %s AND fedids = %s);'''), (proposal_number, append_list, proposal_number, append_list))
            conn.commit()

        c.close()

        with self.output().open('w') as f:
            f.write('TransferFeDIDs DONE')

class TransferChangedDataFile(luigi.Task):
    data_file = luigi.Parameter()
    def requires(self):
        pass
    def output(self):
        pass
    def run(self):
        db_functions.transfer_data(self.data_file)


class TransferNewDataFiles(luigi.Task):
    data_file = luigi.Parameter()
    def requires(self):
        return CheckFiles()
    def output(self):
        pass
    def run(self):
        db_functions.transfer_data(self.data_file)


class StartNewTransfers(luigi.Task):

    def get_file_list(self):
        datafiles = []
        conn, c = db_functions.connectDB()
        c.execute('SELECT filename FROM soakdb_files WHERE status_code = 0')
        rows = c.fetchall
        for row in rows:
            datafiles.append(str(row[0]))
        return datafiles

    def requires(self):
        return [TransferNewDataFiles(data_file) for data_file in self.get_file_list()]

    def output(self):
        pass

    def run(self):
        pass


class TransferExperiment(luigi.Task):
    # date parameter - needs to be changed
    date = luigi.DateParameter(default=datetime.date.today())
    # data_file = luigi.Parameter()

    # needs soakDB list, but not fedIDs - this task needs to be spawned by soakDB class
    def requires(self):
        return FindSoakDBFiles()

    def output(self):
        return luigi.LocalTarget(self.date.strftime('transfer_logs/transfer_experiment_%Y%m%d.txt'))

    def run(self):
        # set up logging
        logfile = self.date.strftime('transfer_logs/transfer_experiment_%Y%m%d.txt')
        logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s %(message)s', datefrmt='%m/%d/%y %H:%M:%S')

