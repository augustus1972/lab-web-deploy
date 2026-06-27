#!/usr/bin/env python3
"""Deploy via WinRM - wykonuje deploy.ps1 zdalnie na Windows EC2."""
import argparse
import sys
import winrm

p = argparse.ArgumentParser()
p.add_argument('--host', required=True)
p.add_argument('--user', required=True)
p.add_argument('--password', required=True)
p.add_argument('--build', required=True)
p.add_argument('--commit', required=True)
p.add_argument('--template', required=True)
p.add_argument('--script', required=True)
args = p.parse_args()

with open(args.template, 'r', encoding='utf-8') as f:
    template = f.read()
with open(args.script, 'r', encoding='utf-8') as f:
    script_body = f.read()

# Wstrzykujemy template jako zmienną PowerShell
ps_command = f"""
$TemplateContent = @'
{template}
'@
{script_body}
"""

# Wywołujemy deploy.ps1 z parametrami (przez wrapper który już ma $TemplateContent)
wrapped = f"""
$BuildNumber = '{args.build}'
$GitCommit = '{args.commit}'
$TemplateContent = @'
{template}
'@

{script_body}
"""

print(f"[winrm] Connecting to {args.host}...")
session = winrm.Session(
    f'http://{args.host}:5985/wsman',
    auth=(args.user, args.password),
    transport='ntlm',
    server_cert_validation='ignore'
)

result = session.run_ps(wrapped)
print("STDOUT:", result.std_out.decode('utf-8', errors='ignore'))
if result.std_err:
    print("STDERR:", result.std_err.decode('utf-8', errors='ignore'))
if result.status_code != 0:
    sys.exit(result.status_code)
print(f"[winrm] ✅ Deploy on {args.host} successful")