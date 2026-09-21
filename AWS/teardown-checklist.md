# Teardown Checklist — Run After Every Practice Session

> AWS won't stop billing just because you're done practicing for the night. Some things (NAT Gateway, RDS, unattached Elastic IPs) charge per hour regardless of use. Delete in this order — some resources block deletion of others if done out of sequence.

## Deletion order (do NOT skip steps or reorder)

1. **Terminate EC2 instance(s)**
   - EC2 console → Instances → select → Terminate
   - Wait until state shows "Terminated" before continuing

2. **Delete RDS instance(s)**
   - RDS console → Databases → select → Delete
   - Uncheck "create final snapshot" for practice work (you don't need to keep it)
   - This step can take several minutes — wait for it to fully disappear from the list

3. **Delete the Application Load Balancer** (only if you did `practice-03`)
   - EC2 console → Load Balancers → select → Delete
   - Also delete its associated Target Group afterward

4. **Delete the NAT Gateway(s)**
   - VPC console → NAT Gateways → select → Delete
   - **This is the one most likely to get forgotten and keep billing.** Double-check this step every single time.

5. **Release the Elastic IP(s)**
   - VPC console → Elastic IPs → select → Release
   - An Elastic IP not attached to anything **still bills** — releasing it stops that
   - The NAT Gateway's EIP is only releasable after step 4 completes

6. **Delete the Security Groups** (optional cleanup, no cost, but keeps your account tidy)
   - VPC console → Security Groups → delete the custom ones you made (not the default one, which can't be deleted)

7. **Detach and delete the Internet Gateway**
   - VPC console → Internet Gateways → select → Detach from VPC → then Delete

8. **Delete the subnets**
   - VPC console → Subnets → select each → Delete

9. **Delete the route tables** (the custom ones you made — the default "main" route table is deleted automatically with the VPC)

10. **Delete the VPC itself**
    - VPC console → Your VPCs → select → Delete
    - If this fails, it usually means something above wasn't fully deleted yet — check the error message, it names the blocking resource

## Quick sanity check after teardown

Go to **Billing → Cost Explorer** (or just the main Billing dashboard) and confirm no NAT Gateway, RDS, EC2, or ALB charges are still accruing for the current day. This takes 30 seconds and is worth doing every time — it's the only way to be sure nothing was missed.

## Fastest option: delete the whole VPC via "VPC and more" cleanup
If you created the VPC using the **"VPC and more"** wizard (not step-by-step manually), the VPC console has a single **"Delete VPC"** action that cascades through subnets, route tables, and the IGW automatically — but it will **not** delete EC2 instances, RDS instances, NAT Gateways, ALBs, or Elastic IPs. Those five must still be deleted manually first (steps 1–5 above) before the cascading delete will succeed.
