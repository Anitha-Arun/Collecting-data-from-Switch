import paramiko
import time
import logging
import socket
import re
import configparser
import csv
import os

# Configure logging for detailed debugging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CustomSSHClient(paramiko.SSHClient):
    def _auth(self, username, password, *args, **kwargs):
        """
        Custom authentication method to handle various authentication scenarios
        """
        try:
            self._transport.auth_none(username)
        except paramiko.BadAuthenticationType as e:
            logger.info(f"Allowed authentication types: {e.allowed_types}")
            if 'publickey' in e.allowed_types:
                logger.info("Attempting public key authentication")
                self._transport.auth_publickey(username, paramiko.RSAKey.generate(2048))
            if 'password' in e.allowed_types:
                logger.info("Attempting password authentication")
                self._transport.auth_password(username, password)
            if not self._transport.is_authenticated():
                raise

def read_inventory(file_path=r"C:\Users\v-adamarla\OneDrive - Microsoft\Desktop\cisco_switch_ansible\lldp\library\inventory.ini", section='switches'):
    """
    Read connection details from an inventory.ini file
    Supports multiple hosts in the same section
    """
    print(f"Looking for inventory file at: {os.path.abspath(file_path)}")  # Debugging step
    config = configparser.ConfigParser()
    config.read(file_path)
    
    if section not in config:
        raise Exception(f"Section '{section}' not found in {file_path}. Check the inventory file.")
    
    # Extract hosts dynamically
    hosts = []
    for key in config[section]:
        if key.startswith('host'):
            host_info = {
                'host': config[section][key],
                'username': config[section].get('username', ''),
                'password': config[section].get('password', '')
            }
            hosts.append(host_info)
    
    if not hosts:
        raise Exception(f"No hosts found in section '{section}' of {file_path}.")
    
    return hosts

def ssh_connect(host, username, password):
    """
    Establish an SSH connection with advanced authentication handling
    """
    try:
        ssh_client = CustomSSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connection_params = {
            'hostname': host,
            'username': username,
            'password': password,
            'look_for_keys': True,
            'allow_agent': True,
            'disabled_algorithms': {
                'kex': ['diffie-hellman-group1-sha1', 'diffie-hellman-group14-sha1'],
                'mac': ['hmac-sha1']
            },
            'timeout': 15
        }
        logger.info(f"Attempting to connect to {host} with username {username}")
        ssh_client.connect(**connection_params)
        channel = ssh_client.invoke_shell()
        channel.settimeout(20)
        logger.info(f"Successfully connected to {host}")
        return ssh_client, channel
    except Exception as e:
        logger.error(f"Connection error for {host}: {e}")
        print(f"Connection error for {host}: {e}")
        return None, None

def extract_lldp_info(output):
    """
    Extract relevant LLDP neighbor information
    """
    device_id_pattern = re.compile(r'Device ID:\s+(\S+)')
    port_id_pattern = re.compile(r'Port ID:\s+(\S+)')
    system_name_pattern = re.compile(r'System Name:\s+(\S+)')
    serial_number_pattern = re.compile(r'Serial number:\s+(\S+)')
    model_name_pattern = re.compile(r'Model name:\s+(\S+)')

    return {
        'Device ID': re.search(device_id_pattern, output).group(1) if re.search(device_id_pattern, output) else None,
        'Port ID': re.search(port_id_pattern, output).group(1) if re.search(port_id_pattern, output) else None,
        'System Name': re.search(system_name_pattern, output).group(1) if re.search(system_name_pattern, output) else None,
        'Serial Number': re.search(serial_number_pattern, output).group(1) if re.search(serial_number_pattern, output) else None,
        'Model Name': re.search(model_name_pattern, output).group(1) if re.search(model_name_pattern, output) else None
    }

def save_to_csv(data, filename='lldp_info.csv'):
    """
    Save extracted LLDP information to a CSV file
    """
    fieldnames = ['Host', 'Device ID', 'Port ID', 'System Name', 'Serial Number', 'Model Name']
    
    with open(filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Write header if the file is empty
        if file.tell() == 0:
            writer.writeheader()
        
        writer.writerow(data)

def send_command(channel, command, wait_time=3, expected_prompts=None):
    """
    Send command and handle output
    """
    try:
        logger.info(f"Sending command: {command}")
        channel.send(command + '\n')
        time.sleep(wait_time)
        output = ""
        
        while channel.recv_ready():
            chunk = channel.recv(4096).decode('utf-8', errors='ignore')
            output += chunk

            # Handle 'More' prompt
            if 'More:' in output:
                before_more = output.split('More:')[0]
                after_more = output.split('More:')[1]
                
                output = before_more
                channel.send(' ' + '\n')
                time.sleep(1)
                output += after_more

            # Handle expected prompts
            if expected_prompts:
                for prompt in expected_prompts:
                    if prompt['text'] in output:
                        logger.info(f"Responding to prompt: {prompt['text']}")
                        channel.send(prompt['response'] + '\n')
                        time.sleep(1)
                        output = ""

        logger.info(f"Full command output: {output}")
        return output
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        return f"Error: {e}"

def extract_lldp_ports(output):
    """
    Extract valid LLDP neighbor ports from the command output
    """
    lines = output.split('\n')
    port_pattern = re.compile(r'^\s*(gi\d+)\s+')
    ports = []
    for line in lines[2:]:
        match = port_pattern.search(line)
        if match:
            ports.append(match.group(1))
    return ports

def process_host(host_info):
    """
    Process a single host for LLDP discovery
    """
    HOST = host_info['host']
    USERNAME = host_info['username']
    PASSWORD = host_info['password']

    print(f"\n===== Processing Host: {HOST} =====")
    
    ssh_client, channel = ssh_connect(HOST, USERNAME, PASSWORD)
    if ssh_client and channel:
        try:
            prompts = [{'text': 'User Name:', 'response': USERNAME},
                       {'text': 'Password:', 'response': PASSWORD}]
            
            print("Entering enable mode:")
            send_command(channel, 'enable', expected_prompts=prompts)
            
            print("\nRunning LLDP Neighbor Discovery:")
            lldp_output = send_command(channel, 'show lldp neighbor', wait_time=5,
                                       expected_prompts=prompts)
            ports = extract_lldp_ports(lldp_output)
            
            print("\nLLDP Neighbor Ports:")
            for port in ports:
                print(f"Running command for port: {port}")
                lldp_port_output = send_command(channel, f"show lldp neighbor {port}", wait_time=5,
                                                expected_prompts=prompts)
                
                # Extract and save LLDP info with host
                lldp_info = extract_lldp_info(lldp_port_output)
                lldp_info['Host'] = HOST
                save_to_csv(lldp_info)
        except Exception as e:
            logger.error(f"Error processing {HOST}: {e}")
        finally:
            if ssh_client:
                ssh_client.close()
                logger.info(f"SSH connection to {HOST} closed.")
                print(f"SSH connection to {HOST} closed.")
    else:
        logger.error(f"Failed to establish SSH connection to {HOST}")

def main():
    try:
        # Read all hosts from inventory
        hosts = read_inventory()
        
        # Process each host
        for host_info in hosts:
            process_host(host_info)
    
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()