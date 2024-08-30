import requests
import os
import sys
import configparser

# Author Jason Ward, ChatGPT

# Load configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Read values from the config file
cpanel_url = config['cpanel']['url']
cpanel_user = config['cpanel']['user']
cpanel_api_token = config['cpanel']['api_token']
domain = config['dns']['domain']
dns_record_name = config['dns']['record_name'] + '.'  # Ensure record_name ends with a dot
ttl = int(config['dns']['ttl'])
ip_file = config['local']['ip_file']
ip_service_url = config['ip_service']['provider_url']


# Function to get current external IP address
def get_external_ip():
    try:
        ip = requests.get(ip_service_url).text
        return ip
    except requests.RequestException as e:
        print(f"Failed to get external IP from {ip_service_url}: {e}", file=sys.stderr)
        return None


# Function to get the current DNS records for the domain
def get_dns_records():
    endpoint = f"{cpanel_url}/json-api/cpanel"
    payload = {
        "cpanel_jsonapi_user": cpanel_user,
        "cpanel_jsonapi_apiversion": "2",
        "cpanel_jsonapi_module": "ZoneEdit",
        "cpanel_jsonapi_func": "fetchzone",
        "domain": domain,
    }

    headers = {
        "Authorization": f"cpanel {cpanel_user}:{cpanel_api_token}"
    }

    try:
        response = requests.get(endpoint, params=payload, headers=headers)
        response_data = response.json()
        if response.status_code == 200:
            return response_data.get('cpanelresult', {}).get('data', [{}])[0].get('record', [])
        else:
            print(f"Failed to fetch DNS records: {response_data}", file=sys.stderr)
            return []
    except requests.RequestException as e:
        print(f"Failed to fetch DNS records: {e}", file=sys.stderr)
        return []


# Function to update DNS 'A' record on cPanel
def update_dns_record(ip_address, record_line=None):
    endpoint = f"{cpanel_url}/json-api/cpanel"
    payload = {
        "cpanel_jsonapi_user": cpanel_user,
        "cpanel_jsonapi_apiversion": "2",
        "cpanel_jsonapi_module": "ZoneEdit",
        "cpanel_jsonapi_func": "edit_zone_record" if record_line else "add_zone_record",
        "domain": domain,
        "name": dns_record_name,
        "type": "A",
        "address": ip_address,
        "ttl": ttl
    }

    if record_line:
        payload["line"] = record_line

    headers = {
        "Authorization": f"cpanel {cpanel_user}:{cpanel_api_token}"
    }

    try:
        response = requests.get(endpoint, params=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200:
            # Check the 'status' key within the response data to confirm success
            status = response_data.get('cpanelresult', {}).get('data', [{}])[0].get('result', {}).get('status')

            if status == 1:
                print(f"DNS 'A' record for {dns_record_name} successfully updated to {ip_address}", file=sys.stdout)
            else:
                print(f"DNS record update failed with status: {status} - Response: {response_data}", file=sys.stderr)
        else:
            print(f"Failed to update DNS record: {response_data}", file=sys.stderr)

    except requests.RequestException as e:
        print(f"Failed to update DNS record: {e}", file=sys.stderr)


# Main logic
def main():
    current_ip = get_external_ip()
    if not current_ip:
        print("Could not determine external IP address.", file=sys.stderr)
        return

    # Read the last known IP address from the file
    last_known_ip = None
    if os.path.exists(ip_file):
        with open(ip_file, 'r') as file:
            last_known_ip = file.read().strip()

    # If the IP address hasn't changed, no need to update the DNS
    if current_ip == last_known_ip:
        print("IP address has not changed, no update needed.", file=sys.stdout)
        return

    # Fetch current DNS records to find the 'A' record
    records = get_dns_records()
    a_record = next((r for r in records if r.get('name') == dns_record_name and r.get('type') == "A"), None)

    if a_record:
        # Update existing record
        update_dns_record(current_ip, record_line=a_record['line'])
    else:
        # Create new 'A' record
        print(f"'A' record for {dns_record_name} not found. Creating new record.", file=sys.stdout)
        update_dns_record(current_ip)

    # Save the current IP address to the file
    with open(ip_file, 'w') as file:
        file.write(current_ip)


if __name__ == "__main__":
    main()
