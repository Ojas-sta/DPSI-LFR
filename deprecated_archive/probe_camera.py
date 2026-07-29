import paramiko

host = "192.168.20.160"
user = "dpsi-lfr"
password = "toor"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(host, username=user, password=password, timeout=10)
    print("OS Version:")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/os-release")
    print(stdout.read().decode())
    
    print("dmesg errors:")
    stdin, stdout, stderr = ssh.exec_command("dmesg | grep -i ov5647")
    print(stdout.read().decode())
    
    stdin, stdout, stderr = ssh.exec_command("dmesg | grep -i i2c")
    print(stdout.read().decode())
        
except Exception as e:
    print(f"Error: {e}")
finally:
    ssh.close()
