from pyspark import SparkContext
from pyspark import SparkConf
 
if __name__ == "__main__": 
 
    conf = SparkConf()
    conf.setMaster("spark://conda-1.rhs:7077")
    conf.setAppName("GetHosts")
 
    sc = SparkContext(conf = conf)

file = sc.textFile("/mnt/glusterfs/grimm/pg2591.txt")
counts = file.flatMap(lambda line: line.split(" ")) \
             .map(lambda word: (word, 1)) \
             .reduceByKey(lambda a, b: a + b)
counts.saveAsTextFile("/mnt/glusterfs/grimm/wordcount")
