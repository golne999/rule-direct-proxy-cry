# Custom Proxy Rules (other_rule)

A project for managing custom routing rules (direct, proxy, and crypto).

## Directory Structure

* `source/`: Contains raw rule files. Edit these to add/remove rules.
  * `direct.txt`: Domain and IP list for direct connections.
  * `proxy.txt`: Domain and IP list for proxied connections.
  * `crypto.txt`: Domain and IP list for cryptocurrency/blockchain connections.
* `sing-box/`: Output directory for sing-box rules.
  * `direct.json` / `direct.srs`
  * `proxy.json` / `proxy.srs`
  * `crypto.json` / `crypto.srs`
* `mihomo/`: Output directory for Mihomo (Clash Meta) rules.
  * `direct-domain.yaml` / `direct-domain.mrs`
  * `direct-ip.yaml` / `direct-ip.mrs`
  * `proxy-domain.yaml` / `proxy-domain.mrs`
  * `proxy-ip.yaml` / `proxy-ip.mrs`
  * `crypto-domain.yaml` / `crypto-domain.mrs`
  * `crypto-ip.yaml` / `crypto-ip.mrs`
* `scripts/`: Conversion utility scripts.
  * `convert.py`: Reads sources and compiles/writes rule-sets.

## How to use

1. Modify rules in `source/direct.txt`, `source/proxy.txt`, or `source/crypto.txt`.
   Supported formats:
   * **Exact domain**: `example.com`
   * **Domain suffix**: `*.example.com` or `+.example.com`
   * **IP CIDR**: `192.168.1.0/24` or `2001:db8::/32`
   * Lines starting with `#` are ignored as comments.

2. Run `convert.py` to regenerate output formats:
   ```bash
   python3 scripts/convert.py
   ```
   *If `sing-box` or `mihomo` CLIs are installed locally, binary format rules (`.srs` / `.mrs`) will also be compiled automatically.*
