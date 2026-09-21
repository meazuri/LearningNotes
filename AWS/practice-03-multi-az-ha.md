# Practice 03 — Multi-AZ High Availability (Phase 2, Stretch Goal)

> Only attempt this once `practice-02` feels comfortable. This promotes the industry-standard setup to survive an entire AZ outage. Region: `ap-southeast-1` (using AZs `1a` and `1b`).

## What changes from practice-02

```
1 VPC (10.0.0.0/16)
 ├─ Public subnet A  (10.0.1.0/24)  — AZ 1a — EC2 instance #1
 ├─ Public subnet B  (10.0.2.0/24)  — AZ 1b — EC2 instance #2
 ├─ Private subnet A (10.0.11.0/24) — AZ 1a — RDS primary
 ├─ Private subnet B (10.0.12.0/24) — AZ 1b — RDS standby (Multi-AZ deployment)
 ├─ Application Load Balancer — spans both public subnets, distributes traffic to both EC2 instances
 └─ NAT Gateway — one per AZ is the real best practice (two NAT Gateways), though a single shared one also works for practice/cost reasons
```

## Step-by-step (delta from practice-02)

### 1. Add a second public and private subnet in AZ `1b`
- Public: `10.0.2.0/24`
- Private: `10.0.12.0/24`

### 2. Launch a second EC2 instance identical to the first
- Same AMI/setup as the `practice-02` instance, placed in the new public subnet (AZ `1b`)

### 3. Create an Application Load Balancer (ALB)
- Attach it across **both** public subnets
- Target group: both EC2 instances
- This becomes the single public entry point — users hit the ALB's DNS name, not either EC2 instance directly

### 4. Enable Multi-AZ on the RDS instance
- When creating (or modifying) the RDS instance, enable **Multi-AZ deployment**
- AWS automatically provisions a standby replica in the second private subnet and handles failover — you don't manually configure the replica's contents, AWS syncs it

### 5. (Optional, cost-aware) NAT Gateway per AZ
- True best practice: one NAT Gateway per AZ, so an AZ outage doesn't also kill the other AZ's outbound internet access
- For practice purposes, one shared NAT Gateway is acceptable to save cost — just note this as a deliberate simplification, not an oversight

## What to verify once it's running

- Traffic through the ALB's DNS name reaches either EC2 instance (refresh a few times, or check ALB target group health)
- In the RDS console, confirm "Multi-AZ" shows as enabled and a standby AZ is listed
- Conceptually: if AZ `1a` went down right now, AZ `1b` still has a working EC2 instance and RDS would fail over to its standby — the app stays up

## Cost warning
This is the most expensive setup in the series to run: 2 EC2 instances, Multi-AZ RDS (roughly double the cost of single-AZ RDS), an ALB (hourly + per-request charges), and NAT Gateway(s). Keep this session especially short, and go straight to teardown afterward.

## Teardown
Follow `teardown-checklist.md` — this setup has the most resources, so double-check nothing is missed (especially the ALB and the second NAT Gateway if you created one).
