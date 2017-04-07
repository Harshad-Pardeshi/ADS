# Filename: run_luigi.py
import luigi
import boto
import boto.s3

from boto.s3.key import Key
from luigi.s3 import S3Target, S3Client

class PrintNumbers(luigi.Task):
 
    def requires(self):
        return []
 
    def output(self):
        return luigi.LocalTarget("numbers_up_to_10.txt")
 
    def run(self):
        with self.output().open('w') as f:
            for i in range(1, 11):
                f.write("{}\n".format(i))
 
class SquaredNumbers(luigi.Task):
 
    def requires(self):
        return [PrintNumbers()]
 
    def output(self):
        return luigi.LocalTarget("squares.txt")
 
    def run(self):
        with self.input()[0].open() as fin, self.output().open('w') as fout:
            for line in fin:
                n = int(line.strip())
                out = n * n
                fout.write("{}:{}\n".format(n, out))
				



class UploadToS3(luigi.Task):
    #awsKey = 'AKIAIKKVCJ2BT52MZHAA'
    #awsSecret = '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'
    awsKey = luigi.Parameter(config_path=dict(section='path',name='aws_key'))
    awsSecret = luigi.Parameter(config_path=dict(section='path',name='aws_secret'))
    
    def requires(self):
        return [SquaredNumbers()]

    #def output(self):
        #return luigi.S3Target('s3://team10-ads-assignment-2/square.txt')

    def run(self):
		
		#Creating a connection
        access_key = self.awsKey
        access_secret = self.awsSecret
        conn = boto.connect_s3(access_key,access_secret)

        bucket_name = 'team10-ads-assignment-2'
        bucket = conn.get_bucket(bucket_name)

        k = Key(bucket)
        k.key = "squares.txt"
        k.set_contents_from_filename("squares.txt")
        # this will return a file stream that reads the file from your aws s3 bucket
                 
if __name__ == '__main__':
    luigi.run()