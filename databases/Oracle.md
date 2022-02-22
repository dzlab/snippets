## Oracle:
### Azure
See https://docs.microsoft.com/en-us/azure/virtual-machines/workloads/oracle/oracle-database-quick-create

Create Oracle VM

```
az vm create --resource-group toto_group --name totooracle --image Oracle:Oracle-Database-Ee:12.1.0.2:latest --size Standard_DS2_v2 --admin-username <USERNAME> --admin-password <Password>
```

In the output of the previous command get the VM IP address, e.g.
```
ssh <USERNAME>@<IP_ADDRESS>
```

Create Oracle DB
```
sudo -su oracle
lsnrctl start
```

Create data folder for Oracle DB
```
mkdir /u01/app/oracle/oradata
```

Create the database
```
dbca -silent \
       -createDatabase \
       -templateName General_Purpose.dbc \
       -gdbname cdb1 \
       -sid cdb1 \
       -responseFile NO_VALUE \
       -characterSet AL32UTF8 \
       -sysPassword OraPasswd1 \
       -systemPassword OraPasswd1 \
       -createAsContainerDatabase true \
       -numberOfPDBs 1 \
       -pdbName pdb1 \
       -pdbAdminPassword OraPasswd1 \
       -databaseType MULTIPURPOSE \
       -automaticMemoryManagement false \
       -storageType FS \
       -datafileDestination "/u01/app/oracle/oradata/" \
       -ignorePreReqs
```

Set Oracle env variables (`ORACLE_HOME` should have been added)
```
cat ~/.bashrc
echo 'export ORACLE_SID=cdb1' >> ~/.bashrc
source ~/.bashrc
```

#### Oracle EM Express connectivity
Set up connectivity to Oracle Mgmt UI
```
sqlplus / as sysdba
```
Once in the SQL shell run
```
SQL> exec DBMS_XDB_CONFIG.SETHTTPSPORT(5502);

SQL> select con_id, name, open_mode from v$pdbs;

SQL> alter session set container=pdb1;
SQL> alter database open;
SQL> quit
[oracle@totooracle totoadmin]$ exit
```

#### Automate database startup and shutdown
Sign in as root
```
sudo su -
```
Vim `/etc/oratab` and change `N` to `Y`
```
# /etc/oratab
cdb1:/u01/app/oracle/product/12.1.0/dbhome_1:Y
```

Create a `/etc/init.d/dbora` file with following content
```
#!/bin/sh
# chkconfig: 345 99 10
# Description: Oracle auto start-stop script.
#
# Set ORA_HOME to be equivalent to $ORACLE_HOME.
ORA_HOME=/u01/app/oracle/product/12.1.0/dbhome_1
ORA_OWNER=oracle

case "$1" in
'start')
    # Start the Oracle databases:
    # The following command assumes that the Oracle sign-in
    # will not prompt the user for any values.
    # Remove "&" if you don't want startup as a background process.
    su - $ORA_OWNER -c "$ORA_HOME/bin/dbstart $ORA_HOME" &
    touch /var/lock/subsys/dbora
    ;;

'stop')
    # Stop the Oracle databases:
    # The following command assumes that the Oracle sign-in
    # will not prompt the user for any values.
    su - $ORA_OWNER -c "$ORA_HOME/bin/dbshut $ORA_HOME" &
    rm -f /var/lock/subsys/dbora
    ;;
esac
```

Change file permissions
```
chgrp dba /etc/init.d/dbora
chmod 750 /etc/init.d/dbora
```

Create symbolic links
```
ln -s /etc/init.d/dbora /etc/rc.d/rc0.d/K01dbora
ln -s /etc/init.d/dbora /etc/rc.d/rc3.d/S99dbora
ln -s /etc/init.d/dbora /etc/rc.d/rc5.d/S99dbora
```

Reboot the VM so the changes take effect
```
reboot
```

#### Open ports for connectivity
Get the security group created for the VM, it should be <VM-NAME>NSG

```
az network nsg rule create --resource-group rg_group --nsg-name oracleNSG --name allow-oracle --protocol tcp --priority 1001 --destination-port-range 1521
az network nsg rule create --resource-group rg_group --nsg-name oracleNSG --name allow-oracle-EM --protocol tcp --priority 1002 --destination-port-range 5502
```

Get the Public IP address of the VM (name of the resource should be <VM-NAME>PublicIP)

```
az network public-ip show --resource-group rg_group --name oraclePublicIP --query '[ipAddress]' --output tsv
```

You can now connect to Mgmt UI at https://<IP_ADDRESS>:5502/em

To connect to the Magemnt console use
```
hostname: <IP_ADDRESS>:1521
  
username: system
  
password: OraPasswd1
  
database: cdb1
```

Test with [Oracle SQL Developer](https://www.oracle.com/tools/downloads/sqldev-v192-downloads.html), and setting with the following (username system, password OraPasswd1 as set for system user, and SID cdb1 according to the instruction above), the connection can be successfully built.
![image](https://user-images.githubusercontent.com/1645304/155213423-2476e7b9-f7db-4da0-83ac-8a5b72ce3c2d.png)


### AWS
See https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_GettingStarted.CreatingConnecting.Oracle.html

```
PROMPT>sqlplus 'mydbusr@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=endpoint)(PORT=1521))(CONNECT_DATA=(SID=ORCL)))'
```
