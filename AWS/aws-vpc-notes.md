# AWS VPC — Study Notes

> AWS-specific networking concepts (VPC, subnets, AZs, IGW, route tables, security groups, NACLs). General networking fundamentals (CIDR, IP classes, ports, TCP/UDP, DNS, NAT concept) live in `networking-concepts-notes.md`. Practice region: **ap-southeast-1 (Singapore)**.

---

## 1. VPC & Availability Zone structure

- **A VPC is regional, not per-AZ.** One VPC per region — it spans all AZs in that region automatically.
- **Subnets are AZ-specific.** Each subnet lives in exactly one AZ.
- **1 region = 1 VPC.** Deploying to 3 regions means 3 separate, isolated VPCs. A VPC cannot span regions. Connecting them (if needed) requires VPC Peering or Transit Gateway.
- **1 VPC = 1 Internet Gateway.** So 3 regional VPCs also means 3 separate IGWs.

```
VPC (10.0.0.0/16) — spans ap-southeast-1
 ├─ Public subnet  10.0.1.0/24  → AZ 1a
 ├─ Private subnet 10.0.11.0/24 → AZ 1a
```

## 2. Public vs private subnet — a routing distinction, not an IP-type distinction

- **Public subnet** = its route table has a route `0.0.0.0/0 → Internet Gateway`.
- **Private subnet** = no such route. Traffic to an outside destination has nowhere to go — blocked by default.
- That's the *entire* difference. It's not a label you tick — it's just whether that one route exists.

## 3. AWS's 5 reserved IPs per subnet

For a subnet like `10.0.1.0/24`, AWS reserves:

| IP | Reserved for |
|---|---|
| `10.0.1.0` | Network address (standard) |
| `10.0.1.1` | VPC router |
| `10.0.1.2` | DNS (Amazon-provided) |
| `10.0.1.3` | Future use |
| `10.0.1.255` | Broadcast address (standard) |

So a `/24` (256 total) → **251 usable** addresses in AWS.

## 4. Single-AZ vs Multi-AZ

AWS doesn't force multi-AZ — it's a design choice:
- **Single-AZ**: simpler, cheaper (no cross-AZ transfer, no per-AZ NAT Gateway), but one AZ outage takes the whole app down.
- **Multi-AZ**: duplicate subnets across AZs (e.g. `1a` + `1b`), use RDS Multi-AZ deployment and a Load Balancer spanning both — survives a full AZ outage.

Practice roadmap: build single-AZ first end to end, then "promote" to multi-AZ once comfortable.

## 5. Internet Gateway & Route Tables

**Internet Gateway (IGW)** — the front door of the VPC:
- One IGW attached to one VPC (whole VPC, not per-subnet).
- Attaching it alone does nothing — it's just a door, nothing tells traffic to use it yet.

**Route Table** — a list of "if traffic wants to go to X, send it via Y":
- Every VPC gets a default rule: `10.0.0.0/16 → local` (stay inside the VPC).
- Add `0.0.0.0/0 → Internet Gateway` to a subnet's route table to make it public. `0.0.0.0/0` means "anything, any destination" — the catch-all.
- Public subnet = has that catch-all rule pointing at the IGW. Private subnet = doesn't.

**NAT Gateway** — lets a private subnet reach *out* to the internet (e.g. for OS patches) without being reachable *from* it:
- Sits inside a public subnet, gets its own Elastic IP.
- Private subnet's route table gets: `0.0.0.0/0 → NAT Gateway` (not the IGW directly).
- The asymmetry: outbound-initiated traffic can get a reply back in; nothing from the internet can initiate a new connection into the private subnet.
- **Costs money per hour it exists, even idle** — remember this for teardown.

## 6. Security Groups vs Network ACLs

Two layers of firewall, working at different levels:

| | Security Group (SG) | Network ACL (NACL) |
|---|---|---|
| Attaches to | An instance (EC2, RDS, etc.) | A subnet |
| State | **Stateful** — allow inbound, response is automatically allowed out | **Stateless** — inbound and outbound rules are separate, both must be written |
| Rule evaluation | All matching rules apply | Evaluated in numbered order, stops at first match |
| Scope | Fine-grained, per-resource | Coarse, subnet-wide backstop |

**Why each matters, concretely:**
- **Web tier SG**: open `80`/`443` to `0.0.0.0/0` (users need to reach it), but SSH (`22`) restricted to your own IP only — no reason to let the whole internet attempt logins.
- **DB tier SG**: allow `5432` **only from the Web tier SG itself** (reference the group, not an IP range) — the rule keeps working even if the web server's IP changes, and nothing else can ever reach the DB.
- **NACL**: most setups leave the default (allow everything) and rely on SGs for real filtering. A NACL becomes useful when you need to instantly block something at the whole-subnet level, regardless of any individual instance's SG rules.

**One-line difference:** SG = "can this instance be reached / can it reach out" (stateful, per-instance). NACL = "can anything cross this subnet's boundary at all" (stateless, per-subnet, evaluated first, before any SG is even checked).

## 7. How it all wires together

```
Internet
   │
   ▼
Internet Gateway  (attached to the VPC)
   │
   ▼
VPC (10.0.0.0/16)
 ├─ Public subnet (10.0.1.0/24) — route: 0.0.0.0/0 → IGW
 │    ├─ Network ACL (stateless, subnet-wide filter)
 │    ├─ EC2 instance — Security Group: stateful, per-instance filter
 │    └─ NAT Gateway — outbound path for the private subnet
 │
 └─ Private subnet (10.0.11.0/24) — route: 0.0.0.0/0 → NAT Gateway
      ├─ Network ACL (stateless, subnet-wide filter)
      └─ RDS PostgreSQL — Security Group: only allows traffic from the EC2 instance's SG
```

Traffic entering from the internet: **IGW → route table decides which subnet → NACL (subnet-wide check) → Security Group (instance-specific check) → instance.** Private subnet traffic going out: **instance → NAT Gateway → IGW → internet** (never the reverse).

## 8. Next topics to cover
- Secrets management (hardcoded vs environment variables vs AWS Secrets Manager)
- Load Balancers (ALB) and target groups
- VPC Peering / Transit Gateway (connecting multiple VPCs/regions)
