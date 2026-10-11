# Practice-02 (Industry Standard) — Beginner Step-by-Step Guide

Written for someone doing this for the first time. Every step says WHERE to click, WHAT to fill in, and WHAT you should see. Follow it top to bottom. Do not skip steps.

Region: **Asia Pacific (Singapore) ap-southeast-1**. Check the region name in the top-right of the AWS console before every session.

Pairs with: `practice-01-run-log.md` (SSH, app deploy commands) and `practice-02-industry-standard.md` (the concept notes).

---

## 0. The big picture (read once)

```
VPC 10.0.0.0/16
 ├─ Public subnet   10.0.1.0/24   (AZ 1a)  → EC2 web/API server
 ├─ Private subnet  10.0.11.0/24  (AZ 1a)  → RDS database lives here
 ├─ Private subnet  10.0.12.0/24  (AZ 1b)  → EMPTY. Only there because RDS demands 2 AZs
 ├─ Internet Gateway                        → door to the internet
 └─ NAT Gateway (in public subnet)          → lets private things go OUT only
```

Words you will see:
- **Public subnet** = its route table sends internet traffic to the Internet Gateway.
- **Private subnet** = its route table does NOT go to the Internet Gateway. Nothing from outside can reach it.
- **DB subnet group** = a list of subnets that RDS is allowed to use. RDS has NO "pick a subnet" box. It only accepts this list. This is how your private subnet gets connected to RDS.
- **Security group (SG)** = a firewall around one resource.

Money warning: **NAT Gateway (~$0.045/hour)** and **RDS** bill while they exist. Plan to finish and tear down in one session.

---

## 1. Create the VPC

1. Console search bar → type **VPC** → open it.
2. Left menu → **Your VPCs** → **Create VPC**.
3. Choose **VPC only** (not "VPC and more").
4. Name tag: `practice-02-vpc`
5. IPv4 CIDR: choose **IPv4 CIDR manual input** → type `10.0.0.0/16`
6. IPv6: **No IPv6 CIDR block**. Tenancy: **Default**.
7. Click **Create VPC**.

You should see a green "created" banner.

## 2. Create three subnets

1. Left menu → **Subnets** → **Create subnet**.
2. VPC ID: choose `practice-02-vpc`.
3. Fill in subnet 1:
   - Subnet name: `public-1a`
   - Availability Zone: `ap-southeast-1a`
   - IPv4 subnet CIDR block: `10.0.1.0/24`
4. Click **Add new subnet** and fill in subnet 2:
   - Name: `private-1a`, AZ: `ap-southeast-1a`, CIDR: `10.0.11.0/24`
5. Click **Add new subnet** again and fill in subnet 3:
   - Name: `private-1b`, AZ: `ap-southeast-1b`, CIDR: `10.0.12.0/24`
6. Click **Create subnet**.

Note: nothing makes a subnet "public" or "private" yet. The names are only labels. The route tables in step 5 decide it.

## 3. Create and attach the Internet Gateway

1. Left menu → **Internet gateways** → **Create internet gateway**.
2. Name: `practice-02-igw` → **Create**.
3. On the next page, click **Actions → Attach to VPC**.
4. Choose `practice-02-vpc` → **Attach internet gateway**.

Status should change from "Detached" to "Attached".

## 4. Create the NAT Gateway

(Skip this step if you only want to practise RDS. RDS does not need it. The EC2 server only needs it if it must reach the internet from a private subnet. Our EC2 is public, so it is optional for the minimum test. Build it only if you want to practise it.)

1. Left menu → **NAT gateways** → **Create NAT gateway**.
2. Name: `practice-02-nat`
3. **Availability mode: choose Zonal.** (If you pick "Regional" there is no subnet box. Regional is not what we want.)
4. **Subnet: choose `public-1a`.** The NAT Gateway always lives in a PUBLIC subnet, even though it serves the private one.
5. Connectivity type: **Public**.
6. Elastic IP allocation: click **Allocate Elastic IP**. This creates an IP and fills the box.
7. Click **Create NAT gateway**.
8. Wait until Status shows **Available** (a few minutes).

## 5. Create two route tables

Your VPC already has one automatic "Main" route table. Leave it alone. Create two new ones.

**Public route table**
1. Left menu → **Route tables** → **Create route table**.
2. Name: `public-rt`, VPC: `practice-02-vpc` → **Create**.
3. Click the **Routes** tab → **Edit routes** → **Add route**:
   - Destination: `0.0.0.0/0`
   - Target: **Internet Gateway** → choose `practice-02-igw`
   - **Save changes**.
4. Click the **Subnet associations** tab → **Edit subnet associations**.
5. Tick **only `public-1a`** → **Save associations**.

**Private route table**
1. **Create route table** again. Name: `private-rt`, VPC: `practice-02-vpc` → **Create**.
2. **Routes** tab → **Edit routes** → **Add route**:
   - Destination: `0.0.0.0/0`
   - Target: **NAT Gateway** → choose `practice-02-nat`
   - **Save changes**. (If you skipped step 4, skip this route. The table just has the local route.)
3. **Subnet associations** tab → **Edit subnet associations**.
4. Tick **both `private-1a` and `private-1b`** → **Save associations**.

## 6. Create two security groups

Go to **EC2** (console search) → left menu → **Security Groups** → **Create security group**.

**A. Web security group**
- Name: `web-sg`, Description: `web tier`, VPC: `practice-02-vpc`
- Inbound rules → **Add rule** (one per line):
  - Type **HTTP**, Source **Anywhere-IPv4** (port 80)
  - Type **HTTPS**, Source **Anywhere-IPv4** (port 443)
  - Type **SSH**, Source **My IP** (port 22)
  - Type **Custom TCP**, Port range `5000`, Source **My IP** (this is for our test app, which listens on 5000)
- Outbound rules: leave the default.
- **Create security group.**

Notes:
- "My IP" fills in your current public IP. If you change Wi-Fi later and SSH times out, edit this rule and pick My IP again.
- Port 5000 is only a practice shortcut. A real setup puts a web server on 80/443.

**B. Database security group**
- Name: `db-sg`, Description: `db tier`, VPC: `practice-02-vpc`
- Inbound rules → **Add rule**:
  - Type **PostgreSQL** (port 5432 fills in automatically)
  - Source: choose **Custom**, then click the box and type `web-sg`. Pick the `web-sg` entry from the list. Do NOT type an IP address.
- Outbound rules: leave the default.
- **Create security group.**

Meaning: only things wearing `web-sg` can talk to the database.

## 7. Create the DB subnet group (do this BEFORE RDS)

This is the step that connects RDS to your private subnets.

1. Console search → **RDS** → left menu → **Subnet groups** → **Create DB subnet group**.
2. Name: `private-db-group`
3. Description: `private subnets for practice-02`
4. VPC: `practice-02-vpc`
5. Availability Zones: tick `ap-southeast-1a` and `ap-southeast-1b`.
6. Subnets: tick **only** `10.0.11.0/24` and `10.0.12.0/24`. Do NOT tick `10.0.1.0/24`.
7. **Create.**

You should see `private-db-group` in the list with status "Complete".

## 8. Create the RDS database

1. RDS → left menu → **Databases** → **Create database**.
2. Choose **Standard create** (not "Easy create". Easy create hides the options we need).
3. Engine type: **PostgreSQL**. Engine version: leave the default.
4. Templates: **Free tier** if offered, otherwise **Dev/Test**.
5. Availability and durability: **Single-AZ DB instance** (no standby. That is practice-03).
6. Settings:
   - DB instance identifier: `practice-02-database`
   - Master username: `postgres`
   - Credentials management: **Self managed**
   - Master password: pick one and **write it down**. You need it later. (Example for practice: `Test12345`)
7. Instance configuration: **db.t3.micro**.
8. Storage: leave defaults (20 GiB).
9. **Connectivity** (the part that went wrong before):
   - Compute resource: **Don't connect to an EC2 compute resource**. (If you pick "Connect to an EC2 compute resource", RDS takes over setup, builds its own subnet group, and creates extra `ec2-rds-N` / `rds-ec2-N` security groups that are hard to delete.)
   - Virtual private cloud (VPC): `practice-02-vpc`. The list only shows VPCs that already have a DB subnet group, so step 7 must be done first. Click the circular refresh icon if it is missing.
   - DB subnet group: `private-db-group`
   - Public access: **No**
   - VPC security group: **Choose existing**. Add `db-sg` and **remove the "default" one**.
   - Availability Zone: `ap-southeast-1a`
10. Scroll down: make sure **Deletion protection is NOT ticked** (otherwise teardown is blocked).
11. Click **Create database**.

It shows "Creating". This takes about 5–10 minutes. Keep going with step 9 while you wait.

If creation fails, read the red message. The most common cause is the VPC or subnet group dropdown pointing at something old. Fix that and click Create again.

## 9. Launch the EC2 web server

1. EC2 → **Instances** → **Launch instances**.
2. Name: `web-server`
3. AMI: **Amazon Linux 2023**.
4. Instance type: **t2.micro** or **t3.micro** (whichever says Free tier eligible).
5. Key pair: choose your existing `was-101` (or create a new .pem one).
6. Network settings → click **Edit**:
   - VPC: `practice-02-vpc`
   - Subnet: `public-1a`
   - **Auto-assign public IP: Enable**
   - Firewall: **Select existing security group** → `web-sg`
7. Storage: leave default.
8. Click **Launch instance**.
9. Wait for Instance state **Running** and a **Public IPv4 address** to appear.

## 10. Get the RDS endpoint

1. RDS → **Databases** → click `practice-02-database`. Wait until Status is **Available**.
2. Open the **Connectivity & security** tab.
3. Copy the **Endpoint**. It looks like `practice-02-database.xxxxxxxx.ap-southeast-1.rds.amazonaws.com`.
4. On the same tab, find **Subnets**. It should list your two private subnets. That confirms the database is in your private network.

## 11. Connect to EC2 and put the app on it

On your Mac, in the folder with `was-101.pem` (same as practice-01):
```
chmod 400 was-101.pem
ssh -i was-101.pem ec2-user@<EC2_PUBLIC_IP>
```
Open a second Mac terminal and copy the app up:
```
scp -i was-101.pem -r <path-to-publish-folder> ec2-user@<EC2_PUBLIC_IP>:~/app
```
Back in the SSH window:
```
cd ~/app
chmod +x VpcPractice
```

## 12. Check the database is reachable from EC2

Still in the SSH window. Install the small PostgreSQL client (not the server):
```
sudo dnf install -y postgresql15
```
Then connect to RDS:
```
psql -h <RDS_ENDPOINT> -U postgres -d postgres
```
Type your master password. If you get a `postgres=>` prompt, the whole path works. Type `\q` to leave.

If it hangs: check the database security group rule uses `web-sg` as its source, and that EC2 uses `web-sg`.

## 13. Run the app against RDS

Run this as ONE line in the SSH window (replace the two placeholders). There is no PostgreSQL install on this server this time, because the database is on RDS:
```
export DB_CONNECTION_STRING="Host=<RDS_ENDPOINT>;Port=5432;Database=postgres;Username=postgres;Password=<your-master-password>;SSL Mode=Require;Trust Server Certificate=true" && cd ~/app && ./VpcPractice
```
`SSL Mode=Require` is needed because newer RDS PostgreSQL refuses connections that are not encrypted. If `/time` shows an error about "no encryption", this is why.

Test in your browser:
- `http://<EC2_PUBLIC_IP>:5000/health` → `{"status":"ok"}`
- `http://<EC2_PUBLIC_IP>:5000/time` → a real timestamp

## 14. Prove the database is locked down

On your Mac (not on the server):
```
nc -vz -w 5 <RDS_ENDPOINT> 5432
```
It should time out or fail. That proves the internet cannot reach your database. (In practice-01 the same test connected.)

---

## Common problems

- **`/time` says DB_CONNECTION_STRING is not set**: `export` and `./VpcPractice` must run in the same terminal, back to back (the one-line command in step 13).
- **SSH times out**: your IP changed. Edit `web-sg`, SSH rule, choose My IP again.
- **Can't see the private subnet in RDS**: normal. RDS only shows the DB subnet group (step 7).
- **RDS creation fails with "default subnet group" error**: the form is using an old group. Pick `private-db-group` and make sure the VPC is `practice-02-vpc`.
- **Extra `ec2-rds-N` / `rds-ec2-N` security groups appear**: you chose "Connect to an EC2 compute resource". Next time choose "Don't connect".

---

## Teardown (in this exact order)

Delete in this order. Each item blocks the next if you skip ahead.

1. **EC2**: Instances → select → **Instance state → Terminate instance**.
2. **RDS**: Databases → select → **Actions → Delete**.
   - Untick **Create final snapshot**.
   - Untick **Retain automated backups**.
   - Tick the acknowledgement box, type `delete me`, confirm.
   - Wait until it disappears from the list (several minutes).
3. **NAT Gateway** (if you made one): VPC → NAT gateways → **Actions → Delete NAT gateway**. Wait for **Deleted**.
4. **Elastic IP**: EC2 → Elastic IPs → select the NAT's IP → **Actions → Release Elastic IP address**. It bills if left behind.
5. **DB subnet group**: RDS → Subnet groups → select `private-db-group` → **Delete**.
6. **Security groups**: delete `db-sg` first, then `web-sg`. (`db-sg` points at `web-sg`, so `web-sg` is blocked until `db-sg` is gone.)
7. **Internet gateway**: VPC → Internet gateways → **Actions → Detach from VPC**, then **Actions → Delete internet gateway**.
8. **Subnets**: delete all three.
9. **Route tables**: delete `public-rt` and `private-rt`. (Never the "Main" one. It goes away with the VPC.)
10. **VPC**: Your VPCs → select → **Actions → Delete VPC**.

Final check: EC2 → Elastic IPs is empty, VPC → NAT gateways shows Deleted, RDS → Databases is empty.
