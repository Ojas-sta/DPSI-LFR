import paramiko

hosts = ["192.168.1.108", "192.168.20.160"]
user = "dpsi-lfr"
password = "toor"

found = False
for host in hosts:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password, timeout=5)
        print(f"Connected to {host}!")
        print("Reading /home/dpsi-lfr/Desktop/main.py...")
        stdin, stdout, stderr = ssh.exec_command("cat /home/dpsi-lfr/Desktop/main.py")
        out = stdout.read().decode()
        if out: 
            print(out)
            found = True
        break
    except Exception as e:
        print(f"Failed on {host}: {e}")
    finally:
        ssh.close()
        
if not found:
    print("Could not find or read file on any host.")
