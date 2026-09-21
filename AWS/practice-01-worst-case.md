# Practice 01 — Worst Case (Anti-Pattern) Setup

> Goal: build this on purpose, see how "easy" it feels, then understand exactly why each shortcut is a real risk in production. Region: `ap-southeast-1`.

## What we're building

```
1 VPC
 └─ 1 public subnet (1 AZ only)
     └─ 1 EC2 instance running EVERYTHING:
         - Static frontend files
         - .NET Core Web API
         - PostgreSQL database (installed directly on the VM)
     └─ Security Group: wide open (all ports, 0.0.0.0/0)
```

No private subnet. No NAT Gateway. No separation. Everything public, everything on one machine, one Security Group letting all traffic through.

## Step-by-step

### 1. Create the VPC
- VPC CIDR: `10.0.0.0/16`
- No need to enable anything extra — default settings

### 2. Create one subnet
- CIDR: `10.0.1.0/24`
- AZ: `ap-southeast-1a` only
- **Anti-pattern flag:** single AZ, single subnet for everything — one outage takes down the whole app.

### 3. Create and attach an Internet Gateway
- Create IGW, attach to the VPC

### 4. Edit the route table
- Add route: `0.0.0.0/0 → Internet Gateway`
- Applied to the one subnet you made

### 5. Create a wide-open Security Group
- Inbound rule: **All traffic, All ports, Source: 0.0.0.0/0**
- **Anti-pattern flag:** this exposes literally every port (including PostgreSQL's `5432`) to the entire internet, not just the ports your app needs (80/443).

### 6. Launch one EC2 instance
- Type: `t2.micro` / `t3.micro`
- Subnet: the one you made
- Auto-assign public IP: **Yes**
- Attach the wide-open Security Group

### 7. Install everything on that one VM
- Install PostgreSQL directly on the VM (`sudo apt install postgresql`)
- Deploy the .NET Core Web API directly on the VM
- Serve the Angular static build from the same VM (e.g. via Nginx or `dotnet`'s static file serving)
- **Anti-pattern flag:** DB, API, and frontend all share the same compute — if one crashes or gets compromised, all three go down or are exposed together.

### 8. Configure PostgreSQL to accept remote connections
- Edit `postgresql.conf`: `listen_addresses = '*'`
- Edit `pg_hba.conf`: allow connections from `0.0.0.0/0`
- **Anti-pattern flag:** your database is now reachable directly from the internet, on its default port, from anywhere. This is one of the most common real-world breach vectors — automated bots scan the entire internet for exposed port `5432`/`3306` within minutes of it opening.

### 9. Use the DB's root/superuser credentials directly in the API's connection string, hardcoded in code
- **Anti-pattern flag:** no secrets manager, no environment variable separation, credentials committed to source control risk.

## What to notice once it's running

- It genuinely works end to end — that's exactly why this pattern is tempting.
- Test: from your own laptop, try `telnet <public-ip> 5432` — if it connects, your DB is exposed to the world right now.
- List out loud everything that's wrong before moving to `practice-02`:
  1. Single AZ — no redundancy
  2. Single VM — no blast-radius isolation between frontend/API/DB
  3. DB has a public IP and is reachable directly from the internet
  4. Security Group allows all ports from anywhere, not just what's needed
  5. No NAT Gateway concept applied — nothing is actually private
  6. Hardcoded DB credentials

## Teardown
Follow `teardown-checklist.md` immediately after this session — this setup is the most exposed one in the series, don't leave it running.
