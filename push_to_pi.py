import paramiko
import os
import sys

host = "192.168.29.73"
user = "dpsi-lfr"
password = "toor"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print("Connecting to Pi...")
    ssh.connect(host, username=user, password=password, timeout=10)
    print("Connected!")
    
    print("Packaging and Transferring package (excluding large weights and venv)...")
    # Package the main rbpi_package directory
    os.system("tar --exclude='.venv' --exclude='.idea' --exclude='__pycache__' --exclude='jepa_weights.pth' --exclude='OLD' -czf /tmp/rbpi_package.tar.gz rbpi_package/")
    
    sftp = ssh.open_sftp()
    sftp.put("/tmp/rbpi_package.tar.gz", "/home/dpsi-lfr/rbpi_package.tar.gz")
    sftp.close()
    print("Transfer complete.")
    
    print("Extracting package on the Raspberry Pi...")
    ssh.exec_command("tar -xzf /home/dpsi-lfr/rbpi_package.tar.gz -C /home/dpsi-lfr/")
    print("Successfully pushed the latest code to the Raspberry Pi!")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
