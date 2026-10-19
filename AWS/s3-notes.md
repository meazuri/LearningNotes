# Amazon S3: Theory Notes

Theory only. Hands-on steps are in `s3-demo-steps.md`.

---

## 1. S3 Buckets and Regions

- S3 is object storage. A bucket is a container for objects.
- Bucket names are globally unique across all AWS accounts. 3 to 63 characters, lowercase, no underscores.
- A bucket lives in one Region. You choose it when you create the bucket.
- Data does not leave that Region unless you copy it or set up replication.
- Pick a Region by: latency to users, cost, legal rules (data residency), and which services you use.
- S3 has a flat structure. There are no real folders. A "folder" is just a prefix in the key (`photos/2026/a.jpg`).
- Default limit is 10,000 buckets per account. You can ask for more.
- Bucket types:
  - General purpose: the normal one.
  - Directory bucket: used with S3 Express One Zone. Single AZ, very low latency.
- Every bucket has an ARN: `arn:aws:s3:::bucket-name`.

## 2. S3 Objects

An object has:

- **Key**: the full name, including prefix. Up to 1,024 bytes.
- **Value**: the data. 0 bytes to 5 TB.
- **Version ID**: if versioning is on.
- **Metadata**: system metadata (Content-Type, size) and user metadata (`x-amz-meta-*`).
- **Tags**: up to 10 key-value pairs. Used for lifecycle, access control, and cost tracking.

Rules to remember:

- One PUT upload: up to 5 GB.
- Above 100 MB: use multipart upload. Required above 5 GB.
- S3 gives strong read-after-write consistency. After a successful write, the next read sees it.
- Objects are immutable. To "edit", you upload a new object with the same key.

## 3. S3 Storage Classes

| Class | Access | Min storage time | Notes |
|---|---|---|---|
| Standard | Frequent | None | Default. 3+ AZs |
| Intelligent-Tiering | Unknown or changing | None | Moves objects between tiers automatically. Small monitoring fee per object |
| Standard-IA | Rare, fast read | 30 days | Lower storage price, retrieval fee. Billed as at least 128 KB |
| One Zone-IA | Rare, can recreate data | 30 days | One AZ only. Data lost if that AZ is lost |
| Glacier Instant Retrieval | Archive, read in milliseconds | 90 days | Good for rarely read data that must be fast |
| Glacier Flexible Retrieval | Archive | 90 days | Retrieval: expedited 1-5 min, standard 3-5 hours, bulk 5-12 hours |
| Glacier Deep Archive | Long-term archive | 180 days | Cheapest. Retrieval: standard 12 hours, bulk 48 hours |
| Express One Zone | Very hot data | None | Single-digit millisecond. Directory buckets. One AZ |

Intelligent-Tiering tiers:

- Frequent Access (start)
- Infrequent Access (after 30 days with no access)
- Archive Instant Access (after 90 days)
- Optional: Archive Access (90+ days) and Deep Archive Access (180+ days)
- No retrieval fee. Object goes back to Frequent when accessed.

Exam shortcuts:

- "Unknown access pattern" → Intelligent-Tiering.
- "Cheapest, rarely read, can wait hours" → Glacier Deep Archive.
- "Can recreate data, save money" → One Zone-IA.
- "Archive but need milliseconds" → Glacier Instant Retrieval.

## 4. S3 Versioning

- Keeps every version of an object in the same bucket.
- Three states: **unversioned** (default), **enabled**, **suspended**.
- You can never go back to unversioned. Only enabled or suspended.
- Objects uploaded before versioning was on get version ID `null`.
- Suspended: new objects get version ID `null`. Old versions stay and still cost money.
- Every version is billed as a full object.
- Needed for: replication, Object Lock, and easy recovery.
- Protection add-ons:
  - **MFA Delete**: needs MFA to permanently delete a version or change versioning state.
  - **Object Lock**: WORM (write once, read many).
    - Governance mode: users with special permission can override.
    - Compliance mode: nobody can delete or change it, not even root.
    - Legal hold: lock with no end date, removed by someone with permission.

## 5. How to Delete and Recover a Deleted File

**Versioning off**

- Delete is permanent. No recovery (unless you have a backup or replica).

**Versioning on**

- Normal delete (no version ID): S3 adds a **delete marker**. The object looks gone, but all versions are still there.
- Delete with a version ID: that version is **permanently deleted**.

**Recover**

- Delete the delete marker. The latest real version shows again.
- Or copy an older version over itself. It becomes a new latest version.

**Safety tools**

- Lifecycle rule to expire old versions after N days (so storage does not grow forever).
- MFA Delete and Object Lock to prevent permanent deletion.
- Replication to another bucket as a second copy. (Version deletes are not replicated.)

## 6. S3 Object Lifecycle

A lifecycle configuration is a set of rules on a bucket. Each rule has:

- **Filter**: whole bucket, prefix, tags, or object size.
- **Actions**:
  - Transition current versions to another class.
  - Transition noncurrent (old) versions to another class.
  - Expire current versions. With versioning on, this adds a delete marker.
  - Permanently delete noncurrent versions after N days.
  - Remove expired delete markers.
  - Abort incomplete multipart uploads after N days.

How it works:

- Days are counted from object creation (or from when it became noncurrent).
- S3 runs lifecycle rules about once a day. Actions are not instant.
- You stop paying when an expiration completes.
- Rules apply to existing objects too, not only new ones.

## 7. Transitioning Objects with Lifecycle Policies

Transitions go **down** only. This is called the waterfall.

```
Standard → Intelligent-Tiering → Standard-IA → One Zone-IA
        → Glacier Instant → Glacier Flexible → Glacier Deep Archive
```

Rules:

- You cannot move back up (for example Standard-IA to Standard) with lifecycle. To go back up, copy the object.
- Standard to Standard-IA or One Zone-IA: object must be at least 30 days old.
- Objects under 128 KB are not transitioned to IA or Glacier by default. It would cost more.
- Each transition is a billed request. Many tiny objects can make transitions expensive.
- Minimum storage time still applies. Delete early and you pay for the full minimum.
- Archived objects (Glacier Flexible, Deep Archive) must be **restored** before reading. A restore makes a temporary copy.

Example plan for logs:

- Day 0: Standard
- Day 30: Standard-IA
- Day 90: Glacier Flexible
- Day 365: expire

## 8. S3 Bucket Replication

- Copies objects from a source bucket to a destination bucket, automatically and asynchronously.
- Two types: **CRR** (different Regions) and **SRR** (same Region).
- Requirements:
  - Versioning ON in both buckets.
  - An IAM role that S3 uses to copy.
  - Source and destination can be in different accounts. Then the destination bucket needs a policy that allows it.
- What gets replicated:
  - New objects after the rule is created.
  - Metadata, tags, and (optionally) ownership change to the destination owner.
- What does not:
  - Existing objects (use Batch Replication).
  - Version deletes (never).
  - Delete markers (not by default; can be turned on).
  - Objects that are themselves replicas. **No chaining**: A → B → C does not copy A's objects to C.
- Destination can use a different storage class (for example Glacier to save cost).
- Replication Time Control (RTC): paid option. 99.99% of objects in 15 minutes, with metrics and alerts.
- Two-way replication: make two rules (A → B and B → A) and turn on replica modification sync.
- Replication status on an object: PENDING, COMPLETED, FAILED, or REPLICA (on the destination).
- Use cases: SRR for log aggregation, prod and test sync, same-Region copy for another account. 

## 9. Cross-Region Replication (CRR)

CRR is replication between Regions.

- Why use it:
  - Compliance that needs data far apart.
  - Lower latency for users in another Region.
  - Disaster recovery.
- Costs: storage in both buckets, PUT requests, and **inter-Region data transfer**. This is often the biggest part.
- With KMS encryption: you must allow the replication role to use the KMS key in the source Region and the destination key in the destination Region.
- Multi-Region Access Points can route users to the closest bucket, and works well with CRR.
- For a stronger recovery target, use RTC (15 minutes).

## 10. S3 Batch Operations

- Run one action on **billions of objects** with a single job.
- You give S3 a **manifest**: an S3 Inventory report, or a CSV with `bucket,key` lines.
- Common actions:
  - Copy objects (for example to change class, encryption, or move to another bucket).
  - Replace tags or ACLs.
  - Restore objects from Glacier.
  - Invoke a Lambda function for each object.
  - Set Object Lock retention or legal hold.
  - Replicate existing objects (Batch Replication).
  - Compute checksums.
- Needs an IAM role that can read the manifest and act on the objects.
- Gives you a job status, priority, and a **completion report** with success and failure per object.
- Typical uses: encrypt old objects, fix tags, replicate old objects, restore lots of archives.

## 11. S3 Select and Glacier Select

- Run simple SQL on **one object**. S3 sends back only the rows and columns you need.
- Works on CSV, JSON, and Parquet (also compressed with GZIP or BZIP2 for CSV/JSON).
- Benefit: less data moved, so faster and cheaper than downloading the whole file.
- Glacier Select did the same for archived objects, without a full restore.
- Limits: one object per query, simple SQL only. No joins.
- Important: as far as I know, AWS closed S3 Select (and Glacier Select) to **new customers** in 2024. Existing users can still use it. Check the current AWS docs before relying on it.
- Alternative today: **Amazon Athena** (SQL across many objects) or S3 Object Lambda style processing.
- Exam note: older questions still expect S3 Select as the answer for "query part of an object".

## 12. S3 Storage Lens

- A dashboard for usage and activity across your S3 storage.
- Scope: whole AWS Organization, one account, one Region, or one bucket.
- There is a free default dashboard.
- **Free metrics**: usage metrics, data for 14 days.
- **Advanced metrics** (paid): activity metrics, prefix-level data, CloudWatch publishing, recommendations, data for 15 months.
- Metric groups: summary, cost optimization, data protection, access management, performance, events.
- Questions it answers:
  - Which buckets cost the most?
  - Which buckets have no versioning or encryption?
  - How much data is in incomplete multipart uploads?
  - Which prefixes are rarely accessed?
- You can export reports daily to an S3 bucket (CSV or Parquet).
- Data can take up to 48 hours to show after you create a dashboard.

## 13. S3 Event Notifications

S3 can tell other services when something happens in a bucket.

**Event types**

- Object created: Put, Post, Copy, CompleteMultipartUpload.
- Object removed: Delete, DeleteMarkerCreated.
- Object restore: restore started and restore completed.
- Replication events: failed, missed threshold, completed after threshold.
- Lifecycle events: transition and expiration.
- Intelligent-Tiering archive events.
- Object tagging and ACL events.

**Destinations**

| Destination | Notes |
|---|---|
| SNS topic | Fan out to many subscribers (email, SQS, Lambda) |
| SQS queue | Standard queue only. FIFO queues are not supported |
| Lambda function | Run code on each event |
| EventBridge | All event types, advanced filtering, many targets, archive and replay |

Rules:

- Filter by prefix and suffix (for example `images/` and `.jpg`).
- The destination must allow S3 to send to it, using a resource policy (SQS, SNS, Lambda) .
- Delivery is at least once. You can get duplicates, so make handlers safe to repeat.
- Do not write the output to the same prefix that triggers the event. You will make a loop.
- For object-level API audit logs, use CloudTrail data events instead.

---

## Extra: S3 Transfer Acceleration

- Speeds up uploads and downloads over long distances.
- Client sends data to the nearest CloudFront edge location. From there it travels on the AWS backbone network to the bucket.
- Turn it on per bucket. Use the endpoint `bucket-name.s3-accelerate.amazonaws.com`.
- Bucket name must be DNS compliant and must not contain dots.
- Extra fee per GB. AWS does not charge if it is not faster.
- Works well with multipart upload.
- Best for: users far from the bucket Region, large files, global uploads.

## Extra: Requester Pays

- Normally the bucket owner pays for storage, requests, and data transfer.
- With Requester Pays, the **requester** pays for requests and data transfer. The owner still pays for storage.
- Use case: sharing large public datasets without paying for everyone's downloads.
- Requirements:
  - The requester must be an authenticated AWS identity. Anonymous access is not allowed.
  - The requester must add the header `x-amz-request-payer: requester` (or `--request-payer requester` in the CLI). Without it, the request fails with 403.
- The bucket owner always pays for their own requests, even with the setting on.
- Not for: cases where you need to know who pays a flat fee, or use with Transfer Acceleration setups that need the owner to pay.
