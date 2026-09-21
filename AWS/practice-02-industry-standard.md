# Practice 02 — Industry Standard Setup (Phase 1: Single-AZ)

> Goal: rebuild the same app properly. Same functionality as `practice-01`, but with the separation and locked-down access that real production setups use. Region: `ap-southeast-1`.

## What we're building

```
1 VPC (10.0.0.0/16)
 ├─ Public subnet  (10.0.1.0/24)  — AZ 1a
 │    └─ EC2 instance: Web API + static frontend files
 │        Security Group: only 80/443 open to the world, 22 (SSH) restricted to your IP
 │
 ├─ Private subnet (10.0.11.0/24) — AZ 1a
 │    └─ RDS PostgreSQL instance (no public IP)
 │        Security Group: only port 5432, only FROM the web tier's Security Group
 │
 ├─ Internet Gateway (attached to VPC)
 └─ NAT Gateway (in the public subnet) — lets the private subnet reach the internet (e.g. patches) without being reachable from it
```

Still single-AZ (phase 1 — no multi-AZ redundancy yet, that's `practice-03`), but now properly separated and locked down.

## Step-by-step

### 1. Create the VPC
- CIDR: `10.0.0.0/16`

### 2. Create two subnets
- Public: `10.0.1.0/24`, AZ `ap-southeast-1a`
- Private: `10.0.11.0/24`, AZ `ap-southeast-1a`

### 3. Create and attach an Internet Gateway
- Attach to the VPC

### 4. Create a NAT Gateway
- Place it **inside the public subnet**
- Allocate a new Elastic IP for it during creation
- **This is the piece that costs money per hour even when idle — remember it for teardown.**

### 5. Set up two route tables

**Public route table** (attach to public subnet):
| Destination | Target |
|---|---|
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | Internet Gateway |

**Private route table** (attach to private subnet):
| Destination | Target |
|---|---|
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | NAT Gateway |

Notice the private subnet's default route goes to the **NAT Gateway**, not the IGW — outbound only, never inbound-initiated.

### 6. Create two Security Groups (not one shared "allow all")

**Web tier Security Group** (for the EC2 instance):
- Inbound: `80` and `443` from `0.0.0.0/0`
- Inbound: `22` (SSH) from **your own IP only**, not `0.0.0.0/0`
- Outbound: all (default)

**DB tier Security Group** (for RDS):
- Inbound: `5432` from **the Web tier Security Group** (reference the security group itself, not an IP range — this means only instances using that SG can ever reach the DB, regardless of what IP they get)
- No other inbound rules

### 7. Launch the EC2 instance (Web API + frontend)
- Subnet: public
- Auto-assign public IP: Yes
- Security Group: Web tier SG

### 8. Launch the RDS PostgreSQL instance
- Subnet group: private subnet only
- Public access: **No**
- Security Group: DB tier SG
- Store the master password in **AWS Secrets Manager** (or at minimum, an environment variable — never hardcoded in source)

### 9. Deploy the app
- Static frontend + Web API on the EC2 instance (same as before)
- Web API connects to RDS using its **private DNS endpoint** (something like `mydb.xxxxx.ap-southeast-1.rds.amazonaws.com`) — this only resolves/works from inside the VPC

## What to verify once it's running

- Try `telnet <rds-endpoint> 5432` from your own laptop — it should **time out**, proving the DB isn't reachable from outside the VPC.
- From the EC2 instance itself, the same connection should work fine — proving the Security Group rule (SG-to-SG reference) is doing its job.
- Compare this checklist against `practice-01`'s "what's wrong" list — each item should now be addressed:
  1. DB has no public IP, unreachable from internet ✓
  2. Security Groups scoped to only necessary ports/sources ✓
  3. DB and Web tier separated onto different resources ✓
  4. Credentials not hardcoded ✓
  5. NAT Gateway allows private subnet outbound access without exposing it ✓
  6. (Still single-AZ — that's addressed in `practice-03`)

## Teardown
Follow `teardown-checklist.md` immediately after — **remember the NAT Gateway specifically**, it's easy to forget and it bills continuously.
