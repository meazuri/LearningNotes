# AWS VPC Practice Series — Overview

> Goal: build the same small app (EduConnect-style — static frontend, Web API, PostgreSQL DB) two ways — once as an anti-pattern ("worst case"), once as industry-standard practice — so the contrast makes the *why* stick. Region: `ap-southeast-1`.

## Files in this series

| File | What it covers |
|---|---|
| `practice-01-worst-case.md` | Deliberately bad setup — everything on one public VM, DB exposed, no separation. Builds the mental "don't do this" list. |
| `practice-02-industry-standard.md` | Phase 1 proper setup — public/private subnet split, locked-down DB, single AZ. |
| `practice-03-multi-az-ha.md` | Phase 2 stretch goal — promoting the standard setup to span multiple AZs for high availability. |
| `teardown-checklist.md` | Exact order to delete everything after each practice session, so nothing keeps billing overnight. |

## Recommended order

1. Do `practice-01` first (worst case) — get it *working end to end*, notice how easy and fast it is.
2. Tear it down (`teardown-checklist.md`).
3. Do `practice-02` (industry standard) — notice it takes more steps, but see exactly *why* each extra step exists.
4. Tear it down again.
5. Once comfortable, attempt `practice-03` (multi-AZ) as a stretch session.

## Cost awareness — read before every session

These are the components in this series that **cost money per hour they exist**, even if idle:
- **EC2 instance** — use `t2.micro` or `t3.micro` (free-tier eligible, check your account's free tier status first)
- **NAT Gateway** — this is the one that surprises people. **~$0.045/hour + data processing charges**, and it bills whether you use it or not. Only appears in `practice-02` and `practice-03`.
- **RDS instance** — even `db.t3.micro` bills hourly while running. Can be stopped (not deleted) for up to 7 days to pause billing, but stopped RDS still restarts automatically after 7 days.
- **Elastic IP** — free while attached to a running instance, **billed if left unattached**.

**Rule for this whole series: tear everything down within the same session (aim for well under 24 hours) using `teardown-checklist.md`.** Don't leave a NAT Gateway or RDS instance running "for next time" — it's cheaper to just rebuild from these notes than to pay for idle infrastructure.

## Related notes
- General networking fundamentals (CIDR, IP classes, ports, TCP/UDP, DNS, NAT concept): `networking-concepts-notes.md`
- AWS-specific VPC/subnet/AZ concepts, Internet Gateway, Route Tables: `aws-vpc-notes.md` (to be created)
