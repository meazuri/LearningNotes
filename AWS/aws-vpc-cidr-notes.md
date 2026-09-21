# AWS VPC & CIDR — Study Notes

> Practice region: **ap-southeast-1 (Singapore)** — 3 AZs: `ap-southeast-1a`, `1b`, `1c`

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

### Private IP ranges (RFC 1918)
Only these three slices are private — not entire octets like "all 192.x.x.x":

| Range | Size |
|---|---|
| `10.0.0.0/8` | ~16 million addresses — most common for AWS VPCs |
| `172.16.0.0/12` | medium range |
| `192.168.0.0/16` | smaller — common for home routers |

AWS VPCs conventionally use `10.x.x.x` just because it's the largest range and easiest to plan big subnets from. `192.168.x.x` or `172.16.x.x` work too.

---

## 2. VPC & Availability Zone Structure

- **A VPC is regional, not per-AZ.** One VPC per region (e.g. one VPC for all of ap-southeast-1), and it spans all AZs in that region automatically.
- **Subnets are AZ-specific.** Each subnet you carve out of the VPC's CIDR block lives in exactly **one** AZ.

```
VPC (10.0.0.0/16) — spans ap-southeast-1
 ├─ Public subnet  10.0.1.0/24  → AZ 1a — web servers
 ├─ Public subnet  10.0.2.0/24  → AZ 1b
 ├─ Public subnet  10.0.3.0/24  → AZ 1c
 ├─ Private subnet 10.0.11.0/24 → AZ 1a — database
 ├─ Private subnet 10.0.12.0/24 → AZ 1b
 └─ Private subnet 10.0.13.0/24 → AZ 1c
```

So mentally: **VPC → contains subnets → each subnet pinned to one AZ.**

### AWS-specific reservation — the 5 reserved IPs

For a subnet like `10.0.1.0/24`, AWS reserves the **first 4** and the **last 1**:

| IP | Reserved for |
|---|---|
| `10.0.1.0` | Network address (standard, not AWS-specific) |
| `10.0.1.1` | Reserved by AWS for the **VPC router** |
| `10.0.1.2` | Reserved by AWS for **DNS** (Amazon-provided DNS server) |
| `10.0.1.3` | Reserved by AWS for **future use** |
| `10.0.1.255` | Network broadcast address (AWS doesn't support broadcast, but the address is still reserved) |

So a `/24` subnet (256 total) → only **251 usable** addresses in AWS (vs. 254 in classic non-AWS networking, which only reserves the first and last).

---

## 3. Public vs Private Subnet

This is a **routing** distinction, not an IP-type distinction:

- **Public subnet** → has a route to the internet via an **Internet Gateway (IGW)**.
- **Private subnet** → no direct internet route; stays internal.

Even in a public subnet, the instance's main address is still a **private IP** (e.g. `10.0.1.5`). AWS attaches a separate **public IP** on top (e.g. `54.23.11.9`) purely for internet reachability. Internally, AWS traffic always uses the private IP.

---

## 4. IP Address Patterns — Private vs Public vs Loopback

Easy to mix these up since some ranges look similar. Quick reference:

| Category | Range | Used for |
|---|---|---|
| **Private** | `10.0.0.0/8` | Large internal networks (AWS VPCs, big corp networks) |
| **Private** | `172.16.0.0/12` | Medium internal networks (this is `172.16.x.x`–`172.31.x.x`, **not** `172.0.x.x`) |
| **Private** | `192.168.0.0/16` | Small/home networks (home routers, small offices) |
| **Loopback** | `127.0.0.0/8` (commonly `127.0.0.1`) | **localhost** — a machine talking to itself. Never leaves the device, never routed on any network. |
| **Public** | Everything not in the above reserved ranges | Routable on the open internet — e.g. `54.23.11.9` (an AWS Elastic IP), `8.8.8.8` (Google DNS) |

**Common mix-up:** `127.0.0.1` (loopback/localhost) vs `172.16.0.0` (private range). They look similar at a glance but are completely different — `127.x` never touches a network at all, `172.16.x` is a real private network range.

**How to tell private vs public at a glance:**
- Starts with `10.` → private
- Starts with `172.` **and** the second number is 16–31 → private (e.g. `172.20.5.1`) — outside that range (e.g. `172.5.1.1`) is actually public
- Starts with `192.168.` → private
- Starts with `127.` → loopback, not a real network address
- Anything else → treat as public unless you know otherwise

---

## 5. Single-AZ vs Multi-AZ (design choice, not a technical requirement)

AWS does **not** force multi-AZ. You can absolutely put everything — web app + DB — into one AZ:

```
VPC (10.0.0.0/16)
 ├─ Public subnet  10.0.1.0/24  → AZ 1a — web app
 └─ Private subnet 10.0.11.0/24 → AZ 1a — database
```

**Trade-off:** if that one AZ has an outage, the whole stack goes down together — no redundancy.

**Why multi-AZ instead:** spreading subnets/resources across AZs means an AZ outage doesn't take down everything (e.g. RDS Multi-AZ deployment, EC2 across 1a/1b/1c behind a load balancer).

### Practice roadmap
1. **Phase 1 — Single-AZ:** build the full stack (VPC → subnet → IGW → route table → security groups → EC2 + RDS) in just `ap-southeast-1a`. Simpler, cheaper (no cross-AZ transfer costs, no NAT gateway per AZ needed).
2. **Phase 2 — Promote to Multi-AZ:** add subnets in `1b`/`1c`, move RDS to Multi-AZ deployment, add a load balancer across AZs.

---

## 6. Next topics to cover
- Internet Gateway + Route Tables (how the "route to internet" actually works)
- NAT Gateway (private subnet outbound internet access)
- Security Groups vs Network ACLs
- Subnet planning for a real project scenario
