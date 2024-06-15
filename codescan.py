import subprocess
import json
from prettytable import PrettyTable
import pandas as pd
from supabase import create_client, Client
import os

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def check_vulnerabilities(requirements_path):
    result = subprocess.run(['safety', 'check', '--json', '--file', requirements_path], capture_output=True, text=True)
    try:
        vulnerabilities = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Failed to decode JSON from safety check output.")
        return

    if vulnerabilities:
        table = PrettyTable()
        table.field_names = ["Package", "Affected", "Installed", "Vulnerability ID", "Description"]
        
        vuln_list = vulnerabilities.get("vulnerabilities", [])
        
        for vuln in vuln_list:
            if not isinstance(vuln, dict):
                print("Expected a dictionary for each vulnerability, got:", type(vuln))
                continue
            
            scanned_packages = []
            for pkg, details in vulnerabilities['scanned_packages'].items():
                scanned_packages.append({
                    'Package Name': details['name'],
                    'Version': details['version'],
                    'Requirement': details['requirements'][0]['raw'],
                    'File Found In': details['requirements'][0]['found']
                })

            for vuln in vulnerabilities['vulnerabilities']:
                data={
                    'vuln_id': vuln['vulnerability_id'],
                    'package_name': vuln['package_name'],
                    'version': vuln['analyzed_version'],
                    'vuln_spec': ', '.join(vuln['vulnerable_spec']),
                    'advisory': vuln['advisory'],
                    'cve': vuln['CVE'],
                }
            response, error = supabase.table("code_vulnerabilities").insert(data).execute()    
            if error:
                print(f"Failed to insert data into Supabase: {response.error.message}")
            else:
                print(f"Vulnerability data inserted successfully for package: {vuln['Package Name']}")
            df_scanned_packages = pd.DataFrame(scanned_packages)
            df_vulnerabilities = pd.DataFrame(data)

            # Display the DataFrames
            print("Scanned Packages:")
            print(df_scanned_packages.to_markdown(index=False))

            print("\nVulnerabilities Found:")
            print(df_vulnerabilities.to_markdown(index=False))
            # affected_versions = vuln.get("affected_versions", "N/A")
            # installed_version = vuln.get("installed_version", "N/A")
            # vuln_id = vuln.get("vuln_id", "N/A")
            # description = vuln.get("description", "N/A")
            
            # # Adding row to the table
            # table.add_row([package, affected_versions, installed_version, vuln_id, description])
        
        # Print the table if there are vulnerabilities
    #     if not table.rows:
    #         print("No vulnerabilities found.")
    #     else:
    #         print(table)
    # else:
    #     print("No vulnerabilities detected or failed to parse the output.")



requirements_path = 'C:/Users/aswin/Desktop/VayuDrishti/requirements.txt'
vulnerabilities = check_vulnerabilities(requirements_path)