#!/usr/bin/env python3
"""
Convert manual source files (direct.txt, proxy.txt) into output rule formats:
  - sing-box JSON (.json)
  - sing-box binary (.srs)   — requires `sing-box` CLI
  - mihomo domain YAML (.yaml)
  - mihomo domain binary (.mrs) — requires `mihomo` CLI
  - mihomo IP YAML (.yaml)
  - mihomo IP binary (.mrs)   — requires `mihomo` CLI
"""

import json
import subprocess
import sys
import ipaddress
from pathlib import Path


def parse_rule_line(line):
    """Parse a single line from the rule file, categorizing it."""
    line = line.strip()
    if not line or line.startswith('#'):
        return None, None

    # Check if it is an IP address or CIDR
    try:
        net = ipaddress.ip_network(line, strict=False)
        return "ip_cidr", str(net)
    except ValueError:
        # It's a domain/suffix
        if line.startswith('*.'):
            return "domain_suffix", line[2:]
        elif line.startswith('+.'):
            return "domain_suffix", line[2:]
        else:
            return "domain", line


def parse_rule_file(path):
    """Read and parse the rules from a text file."""
    result = {
        "domain": set(),
        "domain_suffix": set(),
        "ip_cidr": set()
    }
    if not path.exists():
        print(f"  ⚠️  Source file not found: {path}")
        return result

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            category, value = parse_rule_line(line)
            if category:
                result[category].add(value)

    return {
        "domain": sorted(result["domain"]),
        "domain_suffix": sorted(result["domain_suffix"]),
        "ip_cidr": sorted(result["ip_cidr"])
    }


def build_singbox_ruleset(parsed):
    """Build sing-box rule-set JSON structure."""
    rule = {}
    if parsed["domain"]:
        rule["domain"] = parsed["domain"]
    if parsed["domain_suffix"]:
        rule["domain_suffix"] = parsed["domain_suffix"]
    if parsed["ip_cidr"]:
        rule["ip_cidr"] = parsed["ip_cidr"]
    return {"version": 2, "rules": [rule]}


def write_yaml_payload(path, payload):
    """Write mihomo rule-provider YAML file."""
    with open(path, "w", encoding="utf-8") as f:
        if not payload:
            f.write("payload: []\n")
            print(f"  📄 Written: {path}")
            return
        f.write("payload:\n")
        for item in payload:
            f.write(f"  - '{item}'\n")
    print(f"  📄 Written: {path}")


def to_mihomo_domain_payload(domains, suffixes):
    """Format domains and suffixes for mihomo domain payload."""
    payload = []
    for d in domains:
        payload.append(d)
    for s in suffixes:
        payload.append(f"+.{s}")
    return payload


def compile_singbox_srs(json_path, srs_path):
    """Compile sing-box JSON to binary SRS via sing-box CLI."""
    try:
        subprocess.run(
            ["sing-box", "rule-set", "compile", str(json_path), "-o", str(srs_path)],
            check=True, capture_output=True, text=True
        )
        print(f"  📦 Compiled: {srs_path}")
        return True
    except FileNotFoundError:
        print("  ⚠️  sing-box CLI not found, skipping .srs compilation")
        return False
    except subprocess.CalledProcessError as e:
        print(f"  ❌ sing-box compile error: {e.stderr.strip()}")
        return False


def compile_mihomo_mrs(yaml_path, mrs_path, rule_type="domain"):
    """Compile mihomo YAML to binary MRS via mihomo CLI."""
    try:
        subprocess.run(
            ["mihomo", "convert-ruleset", rule_type, "yaml", str(yaml_path), str(mrs_path)],
            check=True, capture_output=True, text=True
        )
        print(f"  📦 Compiled: {mrs_path}")
        return True
    except FileNotFoundError:
        print("  ⚠️  mihomo CLI not found, skipping .mrs compilation")
        return False
    except subprocess.CalledProcessError as e:
        print(f"  ❌ mihomo compile error: {e.stderr.strip()}")
        return False


def write_mihomo_outputs(name, mihomo_dir, domains, suffixes, ip_cidrs):
    """Write mihomo domain/ip YAML files and compile MRS when possible."""
    mh_dom_yaml = mihomo_dir / f"{name}-domain.yaml"
    domain_payload = to_mihomo_domain_payload(domains, suffixes)
    write_yaml_payload(mh_dom_yaml, domain_payload)

    mh_dom_mrs = mihomo_dir / f"{name}-domain.mrs"
    compile_mihomo_mrs(mh_dom_yaml, mh_dom_mrs, "domain")

    mh_ip_yaml = mihomo_dir / f"{name}-ip.yaml"
    write_yaml_payload(mh_ip_yaml, ip_cidrs)

    mh_ip_mrs = mihomo_dir / f"{name}-ip.mrs"
    compile_mihomo_mrs(mh_ip_yaml, mh_ip_mrs, "ipcidr")


def process_rules(name, parsed, singbox_dir, mihomo_dir):
    """Process a rule set, writing all formats."""
    print(f"\n{'='*50}")
    print(f"Processing: {name}")
    print(f"{'='*50}")

    domains = parsed["domain"]
    suffixes = parsed["domain_suffix"]
    ip_cidrs = parsed["ip_cidr"]

    print(f"  Domains: {len(domains)} | Suffixes: {len(suffixes)} | IPs: {len(ip_cidrs)}")

    # 1. sing-box JSON
    sb_json = singbox_dir / f"{name}.json"
    ruleset = build_singbox_ruleset(parsed)
    with open(sb_json, "w", encoding="utf-8") as f:
        json.dump(ruleset, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  📄 Written: {sb_json}")

    # 2. sing-box SRS
    sb_srs = singbox_dir / f"{name}.srs"
    compile_singbox_srs(sb_json, sb_srs)

    # 3. mihomo Domain/IP YAML + MRS
    write_mihomo_outputs(name, mihomo_dir, domains, suffixes, ip_cidrs)


def main():
    root_dir = Path(__file__).resolve().parent.parent
    source_dir = root_dir / "source"
    singbox_dir = root_dir / "sing-box"
    mihomo_dir = root_dir / "mihomo"

    singbox_dir.mkdir(exist_ok=True)
    mihomo_dir.mkdir(exist_ok=True)

    rule_sets = ["direct", "proxy", "crypto"]

    for name in rule_sets:
        source_path = source_dir / f"{name}.txt"
        parsed = parse_rule_file(source_path)
        process_rules(name, parsed, singbox_dir, mihomo_dir)

    print(f"\n{'='*50}")
    print("✅ All conversions complete.")
    print(f"  sing-box outputs: {singbox_dir}")
    print(f"  mihomo outputs:   {mihomo_dir}")


if __name__ == "__main__":
    main()
