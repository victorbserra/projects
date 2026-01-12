import os
import random
import subprocess
import time

class VPNChanger:
    def __init__(self):
        self.vpn_bin = 'C:/Program Files/OpenVPN/bin/openvpn.exe'
        self.config_dir = 'C:/Program Files/OpenVPN/config'
        self.cred_file = 'credentials.txt'
        self.proc = None
        self.config_files = self.get_vpn_files()

    def connect_vpn(self, config_file):
        command = [self.vpn_bin, '--config', f'{self.config_dir}/{config_file}', '--auth-user-pass', self.cred_file]
        print(f'Connecting to {config_file}...')
        with open('openvpn_output.txt', 'w') as f:
            self.proc = subprocess.Popen(command, stdout=f, stderr=f)
        time.sleep(10)

    def disconnect_vpn(self):
        print('Disconnecting...')
        if self.proc:
            self.proc.terminate()
            time.sleep(5)

    def change_ip(self):
        self.disconnect_vpn()
        vpn_file = random.choice(self.config_files)
        self.connect_vpn(vpn_file)

    def get_vpn_files(self):
        return [f for f in os.listdir(self.config_dir) if f.endswith('.ovpn')]