# pyspark-tutorial
Tutorial for Deploying Anaconda Cluster and PySpark on top of Red Hat Storage GlusterFS

# Heading 

How to deploy Conda Cluster on a 2 Node VM Cluster

As the initial step in setting up Conda Cluster with shared GlusterFS storage, first set up Conda Cluster to operate across a pair of Red Hat Storage nodes without configuring shared data support. This configuration allows running jobs where all data to be analysed is provided when submitting the job, rather than needing to be loaded from disk.

Create a  2 node RHS 3.0 VMs cluster. Setup their /etc/hosts so they have FQDNs.

Designate a Master in the VM cluster. That master should have pwdless SSH access into the other node in the cluster and into itself.

Install Anaconda 2.7 on a laptop (or client machine) that can reach the cluster.
https://store.continuum.io/cshop/anaconda/ (its free).

Install Conda Cluster on the laptop (or client machine)
# TOKEN={ You will need to get this from Continuum Analytics }
# conda install -c https://conda.binstar.org/t/$TOKEN/conda-cluster conda-cluster

Copy the VM CLuster Masters private SSH Key to the laptop to  ~/.conda/clusters.d/rhs-spark.key and set permissions on it (chmod 600).

From the laptop, define the VM Cluster YAML file for the Spark Cluster that conda cluster will be managing (ignore the aws provider):

# vi ~/.conda/clusters.d/rhs-spark.yaml 
rhs-spark:
    private_key         : ~/.conda/clusters.d/rhs-spark.key
    user                : root
    machines            :
         head      : ['192.168.58.219']
         compute   : ['192.168.58.218']
    provider            : simple_aws

From the laptop, verify conda cluster can find the newly defined cluster:
	conda cluster list; conda cluster manage rhs-spark status

From the laptop, bootstrap the cluster (install conda cluster on the VMs)
# conda cluster manage rhs-spark bootstrap --conda --loglevel DEBUG 

You have now completed setting up the Cluster. It is ready to ready Spark Jobs.

Shell into the cluster Master and submit a sample Spark Job across your cluster:
#python /opt/spark-example.py


How to integrate this with Red Hat Storage (GlusterFS)

As the second step in setting up Conda Cluster with shared GlusterFS storage, now configure the shared storage. This configuration allows running jobs where each worker may need to load analysis data from disk, without needing a dedicated central storage server. 

Install GlusterFS on each server in your VM Cluster. This example assumes your 2 VMs hostnames are conda-1.rh (192.168.58.219) and conda-2.rh (192.168.58.218)

Make sure each of the Servers in your VM cluster has an additional drive attached (e.g. /dev/sdb) that you can use as a brick for that server in your Gluster Volume. The examples assume this is a 20GB drive)

Do the following on all servers within your cluster that you intend to be part of your volume:

Format and create a new logical volume(/dev/rhs_vg1/rhs_lv1) from the additional drive (assumes it is a 20GB drive)
# pvcreate /dev/sdb; vgcreate rhs_vg1 /dev/sdb; lvcreate -L 19G -n rhs_lv1 rhs_vg1

XFS Format the the new LV you just created
# mkfs -t xfs -i size=512 -f /dev/rhs_vg1/rhs_lv1

Mount the new LV you created
# mkdir /mnt/brick1 
# mount -t xfs /dev/rhs_vg1/rhs_lv1 /mnt/brick1

Define the servers participating in the gluster volume by Shelling into the Master (conda-1.rh) and peer probing the IP of the additional server from it:
# gluster peer probe 192.168.58.218 

Shell into the Master in your cluster and create the Gluster Volume by passing the cluster IPs and the bricks you created
# gluster volume create MyVolume replica 2 192.168.58.219:/mnt/brick1/data 192.168.58.218:/mnt/brick1/data

Start the Volume
# gluster volume create MyVolume

Check the Volume Status
# gluster volume status

Mount the Volume on each server in the cluster
# mkdir /mnt/gluster
# mount -t glusterfs 192.168.58.219:/MyVolume /mnt/glusterfs

Shell in the Master and copy “Grimm’s Fairy Tales” into the Distributed Gluster Volume
# mkdir -p /mnt/glusterfs/grimm
# cd /mnt/glusterfs/grimm
# wget https://www.gutenberg.org/cache/epub/2591/pg2591.txt --no-check-certificate

Make sure that Spark is running. If not, from your laptop, run:
# conda cluster manage rhs-spark bootstrap --spark --loglevel DEBUG 

Shell into the Master and Create a Spark WordCount Job to run against that data:
#  vi /opt/spark-wordcount.py
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


Shell into the Master and run the WordCount Job
# python /opt/spark-wordcount.py





