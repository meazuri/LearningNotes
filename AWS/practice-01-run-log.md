# Practice-01 (Worst Case) — Full Run-Through Log

This is a step-by-step record of exactly how practice-01 was built, including every command used, so it can be repeated without re-asking. Pairs with `practice-01-worst-case.md` (the plan) and `teardown-checklist.md` (the cleanup order).

---

## 1. Networking setup (console)

- Create 1 **VPC**
- Create 1 **subnet** inside it (this will be the public subnet — the only subnet in this worst-case setup)
- Create 1 **Internet Gateway (IGW)**, attach it to the VPC
- Create 1 **Route Table**:
  - Add a route: destination `0.0.0.0/0` → target = the IGW
  - Associate this route table with the subnet (this is what makes it a "public" subnet)

## 2. Security Group (wide open — intentional anti-pattern)

- Create 1 Security Group, attached to the VPC
- **Inbound rules:** Allow **All traffic**, all ports, source `0.0.0.0/0` (open to the entire internet — this is the "worst case" part, never do this in real setups)
- **Outbound rules:** leave default (Allow all traffic, all ports, destination `0.0.0.0/0`) — this is AWS's default and is fine to leave as-is even in proper setups, since outbound-all is normal

## 3. Launch EC2 instance

- Choose Amazon Linux 2023 AMI
- Choose a key pair — created new one, type **.pem** (works with Mac/OpenSSH), named `was-101.pem`
- Network settings:
  - Select the VPC and public subnet created above
  - Select the wide-open security group
  - **Auto-assign public IP → set to "Enable"** ✅ (do this at launch — avoids the whole Elastic IP process below entirely; the only tradeoff is the IP changes if you stop/start the instance, which doesn't matter for teardown-each-time practice)
- Storage/file system prompt (EFS/S3/FSx): choose **None** — not needed for a single instance

> Note: the first time through, "Auto-assign public IP" wasn't enabled, so an Elastic IP had to be manually allocated and associated instead (EC2 console → Elastic IPs → Allocate → Associate → choose "Instance" as resource type, not "Network interface" → select the instance). Enabling auto-assign at launch skips all of this.

## 4. Connect via SSH

On your Mac, in the folder containing `was-101.pem`:

```
chmod 400 was-101.pem
```

(Required — AWS/SSH rejects key files that are readable by others. Only needs to be done once per key file.)

```
ssh -i was-101.pem ec2-user@<PUBLIC_IP>
```

## 5. Build and deploy the app

On your Mac, inside the project folder:

```
dotnet publish -c Release --self-contained -r linux-x64
```

Then copy the published output to the instance:

```
scp -i was-101.pem -r <path-to-publish-folder> ec2-user@<PUBLIC_IP>:~/app
```

On the EC2 instance:

```
cd ~/app
chmod +x VpcPractice
./VpcPractice
```

App listens on `0.0.0.0:5000`. Test in browser: `http://<PUBLIC_IP>:5000/health` → should return `{"status":"ok"}`.

⚠️ This runs in the foreground — closing the terminal stops the app. Open a **second SSH session** (new terminal, same `ssh -i was-101.pem ec2-user@<PUBLIC_IP>` command) for further setup work.

## 6. Install PostgreSQL

Check the OS first (determines install command):

```
cat /etc/os-release
```

For Amazon Linux 2023:

```
sudo dnf install -y postgresql15
sudo dnf install -y postgresql15-server
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl status postgresql
```

(Press `q` to exit the status screen.) Look for `active (running)`.

## 7. Set a password for the postgres user

```
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'test1234';"
```

Ending in `ALTER ROLE` = success. (An unrelated warning — `could not change directory to "/home/ec2-user": Permission denied` — always appears above it when running via `sudo`; this is harmless and can be ignored every time.)

## 8. Allow password login (edit pg_hba.conf)

Find the file:

```
sudo find / -name "pg_hba.conf" 2>/dev/null
```

Change the local IPv4/IPv6 `ident` lines to `scram-sha-256`:

```
sudo sed -i 's/127.0.0.1\/32            ident/127.0.0.1\/32            scram-sha-256/' /var/lib/pgsql/data/pg_hba.conf
```

Verify:

```
sudo cat /var/lib/pgsql/data/pg_hba.conf | grep 127.0.0.1
```

Restart PostgreSQL so the change takes effect:

```
sudo systemctl restart postgresql
```

(No output = success.)

## 9. Create the database

```
sudo -u postgres psql -c "CREATE DATABASE vpctest;"
```

Ending in `CREATE DATABASE` = success (same harmless permission warning above it as before).

## 10. Run the app with the DB connection string

⚠️ **Critical: the `export` and the app launch must happen in the same terminal session, back to back, or the app won't see the variable.** Run as one line:

```
export DB_CONNECTION_STRING="Host=127.0.0.1;Port=5432;Database=vpctest;Username=postgres;Password=test1234" && cd ~/app && ./VpcPractice
```

Test in browser: `http://<PUBLIC_IP>:5000/time` → should return a real timestamp.

## 11. Troubleshooting reference (if `/time` shows "DB_CONNECTION_STRING not set")

Check what's actually running:

```
ps aux | grep VpcPractice
```

Check whether that specific running process has the variable:

```
sudo cat /proc/<PID>/environ | tr '\0' '\n' | grep DB_CONNECTION
```

If empty, that process was started without the variable — kill it and restart using the combined command in step 10:

```
kill <PID>
```

## Key concepts for next time

- **SSH** = a remote-control text session into the instance over an encrypted connection. Everything typed after connecting runs on the EC2 instance, not your Mac.
- **`.pem` key** = a private key that pairs with a public key AWS stores on the instance — proves identity without ever sending a password over the network. Must stay `chmod 400` (only you can read it).
- **`ec2-user`** = AWS's default admin account on Amazon Linux. Fine for practice; real production setups often use named individual users or AWS Systems Manager Session Manager instead (no SSH keys/open ports needed).
- **No GUI** = normal for servers — saves cost/resources, and everything is meant to be scriptable/repeatable via commands rather than clicking.
- **Elastic IP vs Auto-assign public IP**: Elastic IP is a separate resource you manually attach, stays fixed even through stop/start, but bills if left unattached. Auto-assign gives a public IP automatically at launch but it changes on every stop/start. For short practice-and-teardown sessions, use auto-assign.
