1. Go to RDS
2. Go to "Create with full configuration
Create a database with custom configurations and enable features you want across a variety of engines including Aurora (compatible with MySQL & PostgreSQL), MySQL, PostgreSQL, MariaDB, Oracle, Microsoft SQL Server, and IBM Db2. Or use an existing database using restore from S3."
3. Choose "PostgreSQL", Database Creation: "Full Configuration", Templates: "Sandbox", Deployment options: "Single-AZ DB instance deployment (1 instance)"
4. Write DB instance identifier, Master username, Credentials management: "Self Managed", Auto-generate password, Instance type: "db.t4g.micro", Storage type: "gp2", Compute Resource: "Don’t connect to an EC2 compute resource"
5. Write Public Access: "Yes", VPC security group (firewall): "Create New" 
6. Keep everything off in Monitoring
7. Write Initial Database Name, turn off "Enable automated backup", copy all credentials and then go to terminal to add the data "psql -h <your-endpoint> -p 5432 -U postgres -d querymind" (from data folder)
8. Run these: \i load_olist.sql, \i add_foreign_keys.sql, \i load_data.sql

1. Go to EC2
2. Write Name, AMI: "Ubuntu Server 24.04 LTS", Instance type: "t3.micro", create key pair (Key pair type: "RSA" and ".pem")
3. In network settings, update security group name and description, in security group rule 1, change source type to my IP and in security group 2, type: "Custom TCP", Port: "8000", source type: "Anywhere", Description: "FastAPI backend", create instance.
