#!/usr/bin/env python3
"""Smoke test ALB - sprawdza HTTP 200, unikalność hostname, distribution."""
import urllib.request
import sys
import re
import os
import time
from collections import Counter

ALB = os.environ.get("ALB_DNS", "web-alb-1488561596.us-east-1.elb.amazonaws.com")
EXPECTED_BUILD = os.environ.get("BUILD_NUMBER", "")
N_REQUESTS = 30

print(f"[smoke] Target: http://{ALB}")
print(f"[smoke] Expected build: #{EXPECTED_BUILD}")
print(f"[smoke] Requests: {N_REQUESTS}\n")

hosts = Counter()
builds = Counter()
errors = 0

for i in range(N_REQUESTS):
    try:
        req = urllib.request.Request(f"http://{ALB}", headers={"Connection": "close"})
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read().decode("utf-8", errors="ignore")
            if r.status != 200:
                errors += 1
                continue
            m_host = re.search(r'Serwer:\s*<span[^>]*>([^<]+)</span>', body)
            m_build = re.search(r'Build #<span[^>]*>([^<]+)</span>', body)
            if m_host: hosts[m_host.group(1)] += 1
            if m_build: builds[m_build.group(1)] += 1
    except Exception as e:
        errors += 1
        print(f"[smoke] req {i+1}: ERROR {e}")
    time.sleep(0.1)

print("\n=== RESULTS ===")
print(f"Errors: {errors}/{N_REQUESTS}")
print(f"Hosts seen: {dict(hosts)}")
print(f"Builds seen: {dict(builds)}")

# Assertions
fail = False
if errors > 0:
    print(f"❌ FAIL: {errors} errors")
    fail = True
if len(hosts) < 2:
    print(f"❌ FAIL: Only {len(hosts)} unique host(s) — load balancing broken")
    fail = True
if EXPECTED_BUILD and EXPECTED_BUILD not in builds:
    print(f"❌ FAIL: Build #{EXPECTED_BUILD} not seen on any server")
    fail = True

if fail:
    sys.exit(1)
print("✅ ALL CHECKS PASSED")