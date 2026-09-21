# Core Networking Concepts — Study Notes

> General networking fundamentals (IP addressing, CIDR, ports). AWS-specific concepts (VPC, subnets, Availability Zones) live in a separate note.

---

## 1. CIDR Basics

- CIDR notation: `10.0.0.0/16` → the `/N` is the **network prefix**. Bits after it are **host bits**.
- Total addresses in a block = `2^(32-N)`.
  - `/16` → 65,536 addresses
  - `/24` → 256 addresses
- **Borrowing bits** to split a network into smaller ones:
  - Each bit borrowed **doubles** the number of subnets, and **halves** the addresses per subnet.
  - e.g. splitting a `/16` into `/24`s → borrowing 8 bits → 256 possible `/24` subnets.
- A "clean" network address has all host bits set to `0` (e.g. `10.0.1.0/24`, not `10.0.1.5/24`).
- Classic (non-cloud-specific) reservation: **2 addresses per block are always reserved** — the network address (all host bits `0`) and the broadcast address (all host bits `1`). So a `/24` = 256 total → 254 usable in traditional networking.

---

## 2. IP Address Classes (the older "classful" system)

Before CIDR existed, IP addresses were split into fixed **classes**, based on which octets are "network" vs "host". This is legacy, but it explains *why* the private ranges are shaped the way they are.

| Class | First octet range | Network portion | Host portion | Typical use |
|---|---|---|---|---|
| **A** | 0–127 | 1st octet | last 3 octets | Huge networks (e.g. `10.x.x.x`) |
| **B** | 128–191 | first 2 octets | last 2 octets | Medium networks (e.g. `172.16.x.x`) |
| **C** | 192–223 | first 3 octets | last octet | Small networks (e.g. `192.168.x.x`) |
| D | 224–239 | — | — | Multicast (not for regular hosts) |
| E | 240–255 | — | — | Reserved/experimental |

This is exactly why:
- `10.0.0.0/8` (Class A) is huge — only the first octet is "network," leaving 3 octets of host space.
- `192.168.0.0/16` (Class C-derived) is small — three octets are already "network," leaving just 1 octet of host space.

Modern networking uses CIDR (`/N` notation) instead of rigid classes, since CIDR lets you pick *any* split point, not just octet boundaries — but the class system is where these conventions originally came from.

---

## 3. Private IP ranges (RFC 1918)

Only these three slices are private — not entire octets like "all 192.x.x.x":

| Range | Size |
|---|---|
| `10.0.0.0/8` | ~16 million addresses — largest, most common for big internal networks |
| `172.16.0.0/12` | medium range (`172.16.x.x`–`172.31.x.x` only — **not** all `172.x.x.x`) |
| `192.168.0.0/16` | smaller — common for home routers, small offices |

---

## 4. IP Address Patterns — Private vs Public vs Loopback

Easy to mix these up since some ranges look similar. Quick reference:

| Category | Range | Used for |
|---|---|---|
| **Private** | `10.0.0.0/8` | Large internal networks |
| **Private** | `172.16.0.0/12` | Medium internal networks (`172.16.x.x`–`172.31.x.x` only) |
| **Private** | `192.168.0.0/16` | Small/home networks |
| **Loopback** | `127.0.0.0/8` (commonly `127.0.0.1`) | **localhost** — a machine talking to itself. Never leaves the device, never routed on any network. |
| **Public** | Everything not in the above reserved ranges | Routable on the open internet — e.g. `54.23.11.9`, `8.8.8.8` (Google DNS) |

**Common mix-up:** `127.0.0.1` (loopback/localhost) vs `172.16.0.0` (private range). They look similar at a glance but are completely different — `127.x` never touches a network at all, `172.16.x` is a real private network range.

**How to tell private vs public at a glance:**
- Starts with `10.` → private
- Starts with `172.` **and** the second number is 16–31 → private (e.g. `172.20.5.1`) — outside that range (e.g. `172.5.1.1`) is actually public
- Starts with `192.168.` → private
- Starts with `127.` → loopback, not a real network address
- Anything else → treat as public unless you know otherwise

---

## 5. Ports

A **port** identifies *which application* on a machine should receive the traffic. The IP address gets you to the machine; the port gets you to the specific service running on it.

### Total range
Ports run from **0 to 65535** (16-bit number, `2^16` = 65,536 total), split into 3 conventional ranges:

| Range | Name | Used for |
|---|---|---|
| 0–1023 | **Well-known ports** | Reserved for standard services (80, 443, 22, etc.) — usually need admin/root privilege to bind |
| 1024–49151 | **Registered ports** | Registered with IANA for specific software (3306 MySQL, 5432 PostgreSQL, 27017 MongoDB) |
| 49152–65535 | **Dynamic/private ports** | Ephemeral — used for temporary outgoing connections (e.g. your laptop picks a random port here when connecting out to a web server) |

### Common well-known ports
| Port | Convention for |
|---|---|
| 80 | HTTP (unencrypted web traffic) |
| 443 | HTTPS (encrypted web traffic) |
| 22 | SSH |
| 3306 | MySQL |
| 5432 | PostgreSQL |

Browsers auto-assume port 80 for `http://` and port 443 for `https://` — that's why URLs almost never show a port number. You *can* run a service on a non-standard port (e.g. `8080`), but then anyone connecting must type it explicitly (`http://example.com:8080`).

### Common dev ports
| Port | Used for |
|---|---|
| 3000 | Common default for Node/React/Angular dev servers |
| 8080 | Common alt-HTTP port (often used when 80 is taken, or for backend APIs) |
| 5000 | Common Flask/backend dev default |
| 6379 | Redis |
| 27017 | MongoDB |

### Android emulator ports
Each running emulator instance grabs a **pair of consecutive ports**, starting at `5554`:

- `5554` → console port (first emulator instance) — this is why device names look like `emulator-5554`
- `5555` → adb (Android Debug Bridge) port for that same instance

A second emulator instance takes `5556`/`5557`, a third `5558`/`5559`, and so on — each pair avoids conflicts.

Separately, the `adb` tool itself (on your machine, not the emulator) runs a server on port **5037** that all `adb` commands talk to.

---

## 6. Next topics to cover
- TCP vs UDP
- DNS resolution flow
- NAT (how private IPs reach the public internet)
- (AWS-specific topics — VPC, subnets, Security Groups, IGW, route tables — continue in the separate AWS notes file)
