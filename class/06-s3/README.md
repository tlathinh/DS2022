# AWS S3 Storage

This session focuses on **S3**, object storage for datasets, backups, and pipeline I/O. You already covered [IAM](../06-iam/README.md); now you practice IAM in the AWS Academy **Learner Lab**, then use temporary lab credentials with the CLI and `boto3` to create buckets and move objects.

**You will:** start a Learner Lab, create an IAM group and user, configure the AWS CLI from **AWS Details**, practice `cp` / `sync` / `presign`, and run the numbered Python scripts in this folder. That workflow is what `Lab 6` builds on, and the same pattern of identity + storage you will reuse with **Amazon EC2** and **Amazon Lambda** in the coming weeks.

> Experiment with the commands and options. Errors are normal; ask for help and help each other when you can. Advanced topics (versioning, events, ACLs) are optional.



## In-class exercises

### Environment

The following exercises require a working Python 3 environment, the AWS CLI, and `boto3`. You will install the tools next, then start the Learner Lab and configure credentials.

1. Create a new folder and set up a new Python environment:
  ```bash
  mkdir -p ~/ds2022-fall-26/s3
  cd ~/ds2022-fall-26/s3
  uv init 
  ```
2. AWS CLI and Python packages
  We need two packages, installed in two different ways:
  - `awscli`: provides AWS CLI tools
  - `boto3`: package to connect to AWS in your Python scripts
  The AWS CLI is a command line tool, not a library your scripts import, so install it as a `uv` tool. That makes the `aws` command available in every terminal, independent of any project environment:
  ```bash
  uv tool install awscli
  ```
  `boto3` is imported by your Python scripts, so add it to the project:
  ```bash
  uv add boto3
  ```
  Confirm with
  ```bash
  aws --version
  uv tree
  uv run python -c "import boto3"
  ```
  If the shell reports `aws: command not found`, run `uv tool update-shell`, then open a new terminal so the `uv` tool directory is on your `PATH`.


### Start the AWS Academy Learner Lab

Work in the **AWS Academy Learner Lab** (same Academy course as [IAM](../06-iam/README.md)), not a shared course account from Canvas.

1. In AWS Academy Canvas, open the **Learner Lab** (or equivalent module) and click **Start Lab**.
2. Wait until the AWS indicator turns green, then open the AWS Management Console link.

> **Leave the lab running.** Do **not** click **End Lab** when you finish today’s exercises. Ending the lab destroys IAM users/groups and S3 buckets. You will reuse this setup later (EC2, serverless). Refresh credentials when they expire; do not tear down the lab.

### Create an IAM group and user (console)

The lab starts with no student users or groups. Create them in the console (this reinforces [IAM](../06-iam/README.md)):

1. Open **IAM** → **User groups** → **Create group**.
2. Group name: `ds2022`.
3. Attach these AWS managed policies to the group:
   - **AmazonS3FullAccess**: S3 practice (buckets, objects)
   - **IAMUserChangePassword**: so the user can sign in to the **AWS Management Console** and change their password
   - **AmazonEC2FullAccess**: manage EC2 in later weeks
   - **AWSLambda_FullAccess**: manage Lambda in later weeks
4. Create the group.
5. Open **IAM** → **Users** → **Create user**.
6. User name: your computing id (same as `$USER` in the terminal, e.g. `mst3k`).
7. Under **Provide user access to the AWS Management Console**, choose **I want to create an IAM user**, enable console access, and set a custom password (save it somewhere safe; you will need it to log in as this user).
8. Add the user to group `ds2022`, then create the user.

**Console login as your IAM user** (optional check after creation): use the account ID from **AWS Details** (or `aws sts get-caller-identity`), IAM user name = your computing id, and the password you set. Sign-in URL form: `https://ACCOUNT_ID.signin.aws.amazon.com/console`.

**Learner Lab role for EC2 and Lambda (do not skip):** Academy pre-creates a role named **`LabRole`** and an instance profile named **`LabInstanceProfile`**. When you launch EC2 or create Lambda later, attach these; do not invent new roles (Learner Lab IAM is restricted).

- **EC2:** assign instance profile **`LabInstanceProfile`** (so the instance uses **`LabRole`**). Needed for browser/SSM access and for apps on the instance to call other AWS services.
- **Lambda:** set the function’s execution role to **`LabRole`** so the function can reach S3, CloudWatch, and other services.

Confirm under **IAM** → **Roles** that **`LabRole`** exists (and **`LabInstanceProfile`** under instance profiles). You will reuse this in upcoming weeks.

For the CLI exercises below, use **AWS Details** session credentials (Access Key + Secret + Session Token), not long-lived access keys on this IAM user. Creating the group and user (with console access) is still required practice and keeps a named identity in the account for later work.

### AWS CLI configuration (temporary credentials)

Learner Lab CLI access comes from **AWS Details** on the lab page:

1. Click **AWS Details** → **Show** (or equivalent) to reveal credentials.
2. Copy **AWS Access Key ID**, **AWS Secret Access Key**, and **Session Token**.

> **Credentials expire after about 4 hours**, even while the lab stays running. When `aws` or `boto3` suddenly fail with expired-token errors, open **AWS Details** again, copy fresh values into `~/.aws/credentials` (or re-export env vars), and continue. Refreshing credentials does **not** recreate your IAM group, user, or buckets; **Ending Lab** does.

Configure the CLI:

```bash
aws configure
```

Enter:

- **AWS Access Key ID**: from AWS Details
- **AWS Secret Access Key**: from AWS Details
- **Default region name**: `us-east-1`
- **Default output format**: `json`

Then add the session token. Edit `~/.aws/credentials` so the `[default]` profile includes all three values:

```text
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
aws_session_token = YOUR_SESSION_TOKEN
```

Alternatively, export in the shell (include the session token):

```bash
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
export AWS_SESSION_TOKEN="YOUR_SESSION_TOKEN"
```

Upon completion you will have `~/.aws/config` and `~/.aws/credentials` (if you used `aws configure`).

**Verify**

```bash
cat ~/.aws/config
cat ~/.aws/credentials
aws sts get-caller-identity
```

`get-caller-identity` should succeed and show your Learner Lab account. The ARN reflects the lab session identity (not a permanent Canvas `ds2022` user).



### Access S3 using the AWS CLI

Now we can get busy!

#### `aws s3 ls` - List Buckets

```
aws s3 ls
```

You may see buckets you already created in this lab (for example `practice-mst3k`). The shared course materials live in `ds2022-fall26` in another account; that name may not appear in this list. Use the full `s3://ds2022-fall26/...` URIs below for download and sync.

#### `aws s3 mb` - Make a new bucket

```
echo $USER
aws s3 mb s3://practice-$USER
```

`$USER` expands to your computing id. Bucket names must be **globally unique** across all of AWS (a separate Learner Lab account does not give you a private name space). We use `practice-$USER` so the bucket is not confused with your IAM user name. You should see:

```
make_bucket: practice-mst3k
```

If the bucket name is already taken, retry `practice-$USER-1`, `practice-$USER-2`, etc.

Check the list of buckets again:
```
aws s3 ls
```
Your bucket should be in the list now. 

If the output is too long, pipe it into grep, like `aws s3 ls | grep $USER`.

**Optional:** In the Academy console (from Start Lab), open **S3** → **General Purpose buckets** and confirm `practice-$USER` appears.

#### `aws s3 cp` - Copy files

The syntax is `aws s3 cp SOURCE DESTINATION`, similar to the regular `cp` command you're familiar with already. You can copy between any source/destination so long as at least one of them is S3:

- Copy from local environment to S3
- Copy from S3 to local environment
- Copy from S3 bucket to another S3 bucket

**Download**, try this (`ds2022-fall26` is a shared course bucket with public read on teaching objects; `--no-sign-request` avoids needing cross-account IAM):
```
aws s3 cp s3://ds2022-fall26/cloud.jpg . --no-sign-request
```
This downloads `cloud.jpg` from `ds2022-fall26` to your computer. Remember, `.` is the shorthand for your current directory.

**Upload** (set content type so a later `presign` URL displays in the browser):
```
aws s3 cp cloud.jpg s3://practice-$USER/folder/in/bucket/cloud.jpg --content-type image/jpeg
```
Copies `cloud.jpg` into your bucket under the key `folder/in/bucket/cloud.jpg` (same path the Python scripts use). Confirm with `aws s3 ls s3://practice-$USER --recursive`.

Create another file on your computer, like `hello.txt`, add a message and save it. Then upload it into a new folder in S3.

**Another upload:**
```
aws s3 cp hello.txt s3://practice-$USER/new_folder/hello.txt
```
Notice that we don't have to create the `new_folder`.

**Folders in S3:** Contrary to how it appears, S3 is not a file system in the ordinary sense. It is object storage: each object has a **key** (name) and a **value** (the file contents). Keys can include `/`, which looks like folders (for example `folder/subfolder/filename.txt`), but those “folders” are only a naming convention (a mental convenience), not real directories you create ahead of time. The bucket name is not part of the key.

#### `aws s3 ls` - List the contents of a bucket

In the example below, replace `practice-mst3k` with your actual bucket name.

```
aws s3 ls s3://practice-mst3k/
                           PRE folder/
                           PRE new_folder/
```

`PRE folder/` and `PRE new_folder/` are the CLI’s way of showing key prefixes (the “folders”) after your uploads. Use `aws s3 ls s3://practice-mst3k/ --recursive` to see full keys such as `folder/in/bucket/cloud.jpg`.

#### `aws s3 sync` - Synchronize a folder

`cp` copies one object. `sync` copies a whole prefix (folder) and only transfers what is missing or changed. The shared course bucket has a read-only `data/` folder you can pull from.

**1. Sync from the course bucket to your computer**

```bash
mkdir -p data
aws s3 sync s3://ds2022-fall26/data/ ./data/ --no-sign-request
ls data
```

**2. Sync that folder up into your own bucket**

```bash
aws s3 sync ./data/ s3://practice-$USER/data/
aws s3 ls s3://practice-$USER/data/
```

You can sync in any direction as long as at least one side is S3 (local ↔ S3, or S3 ↔ S3).

#### `aws s3 mv` - Move (rename) an object in your bucket

`mv` renames or relocates an object. Practice on a file you just synced into your bucket (pick a real filename from `aws s3 ls s3://practice-$USER/data/`):

```bash
aws s3 mv s3://practice-$USER/data/notes.txt s3://practice-$USER/data/readme.txt
aws s3 ls s3://practice-$USER/data/
```

If `notes.txt` is not in that listing, use another name from the list.

#### `aws s3 presign` - Presign an S3 URL

In some cases you want to share a file for a limited time without creating access keys. `presign` creates a signed URL that expires after a set number of seconds (`--expires-in`).

```bash
aws s3 presign --expires-in 600 s3://practice-$USER/folder/in/bucket/cloud.jpg
```

You will receive a URL like this (yours will differ):

```text
https://practice-mst3k.s3.amazonaws.com/folder/in/bucket/cloud.jpg?AWSAccessKeyId=AKIA...&Signature=...&Expires=...
```

That URL works for 600 seconds (10 minutes). Open it in your web browser. After it expires, the link no longer grants access; the object is still in your bucket.

If the browser downloads the file instead of showing the image, the object was stored without a JPEG content type. Re-upload with `--content-type image/jpeg`, or use `06-presign.py`, which sets `ResponseContentType` / `ResponseContentDisposition` so the image opens inline.

#### `aws s3 rm` / `rb` - Optional cleanup

Keep the `practice-$USER` bucket for later weeks unless you intentionally want to delete it now. Deleting is an optional practice step.

**Delete one file**
```
aws s3 rm s3://practice-$USER/new_folder/hello.txt
```

**Empty the bucket, then you can delete it** (only if you are sure):
```
aws s3 rm --recursive s3://practice-$USER
aws s3 rb s3://practice-$USER
```

**Remember:** S3 buckets must be emptied before they can be removed. Once removed, the bucket name is available for other AWS customers.


### Access S3 using `boto3` in Python

The `boto3` package is the standard library enabling programmatic access to AWS using Python. `boto3` can access all AWS services and is helpful for creating,
managing, or removing remote resources and infrastructure dynamically. The steps below refer to using `boto3` for working with files in S3.

#### Install `boto3`

If you already ran `uv add boto3` in [Environment](#environment), you can skip this. If you skipped that section (or are in a different project folder), run:

```bash
uv add boto3
uv run python -c "import boto3"
```

#### Use `boto3`

By default, after you ran `aws configure`, `boto3` looks up credentials in `~/.aws/credentials` (and region settings in `~/.aws/config`). You do **not** need to pass keys into your code:

```python
import boto3

s3 = boto3.client('s3')
```

#### Optional: credentials via environment variables

If `~/.aws/credentials` is missing (or you prefer not to use it), you can set credentials in the shell as environment variables and read them in the script. That keeps secrets out of the source file; never hardcode keys in clear text (see [best practices](../../best-practices.md)).

In the shell:

```bash
export AWS_ACCESS_KEY_ID="YOUR_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET"
export AWS_SESSION_TOKEN="YOUR_SESSION_TOKEN"
```

In Python:

```python
import os
import boto3

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
)
```

For class, prefer putting the AWS Details values (including session token) in `~/.aws/credentials`, then use plain `boto3.client('s3')`. Refresh those values when the ~4 hour session expires.


#### Create a bucket

```python
import boto3

bucket_name = "practice-mst3k"  # replace with your bucket name
s3 = boto3.client("s3", region_name="us-east-1")
# For most regions you pass CreateBucketConfiguration={"LocationConstraint": "region-name"}.
# us-east-1 is special: omit LocationConstraint or create_bucket will fail.
s3.create_bucket(Bucket=bucket_name)
```


#### Upload a file to S3

```python
import boto3

bucket_name = "practice-mst3k"  # replace with your bucket name
local_file = "cloud.jpg"
key = "folder/in/bucket/cloud.jpg"  # same key as 04-upload-object.py / 06-presign.py

s3 = boto3.client("s3")
with open(local_file, "rb") as f:
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=f,
        ContentType="image/jpeg",
    )
```


#### Download a file from S3

Shared course image (see also `03-download-object.py`):

```python
import boto3

bucket_name = "ds2022-fall26"
key = "cloud.jpg"
local_file = "cloud.jpg"
s3 = boto3.client("s3")

obj = s3.get_object(Bucket=bucket_name, Key=key)
# save the object, "wb" stands for write binary
with open(local_file, "wb") as f:
    f.write(obj["Body"].read())
```


#### Deleting files in S3

```python
import boto3

s3 = boto3.client("s3")
bucket_name = "practice-mst3k"  # replace with your bucket name
key = "folder/in/bucket/cloud.jpg"

s3.delete_object(Bucket=bucket_name, Key=key)
```

To remove every object (empty the bucket), see `08-delete-all-objects.py`.


#### Delete a bucket

```python
import boto3

bucket_name = "practice-mst3k"  # replace with your bucket name
s3 = boto3.client("s3")
s3.delete_bucket(Bucket=bucket_name)
```

> **Note:** Optional cleanup only. Buckets must be empty before delete (`08-delete-all-objects.py`, then `09-delete-bucket.py`). Keep `practice-$USER` if you will reuse it later.

#### Catching boto exceptions

Most S3 errors show up as a `botocore.exceptions.ClientError`. For the simplest demos above, we omit error handling so you can focus on the API calls.

See the numbered scripts in this folder for runnable examples, including `try` / `except ClientError` patterns:

#### Python scripts

| Script | Purpose |
|--------|---------|
| `00-env-credentials.py` | Build S3 client from env vars (optional; default is `~/.aws`) |
| `01-make-bucket.py` | Create `practice-$USER` |
| `02-list-buckets.py` | List buckets |
| `03-download-object.py` | Download `cloud.jpg` from `s3://ds2022-fall26/` (public read) |
| `04-upload-object.py` | Upload to `folder/in/bucket/cloud.jpg` (`ContentType=image/jpeg`) |
| `05-list-objects.py` | List objects in a bucket |
| `06-presign.py` | Presign `folder/in/bucket/cloud.jpg` (inline display) |
| `07-delete-object.py` | Delete `folder/in/bucket/cloud.jpg` |
| `08-delete-all-objects.py` | Empty a bucket (recursive; optional cleanup) |
| `09-delete-bucket.py` | Delete the bucket (optional; must be empty) |

The scripts are short top-to-bottom demos with no helper functions or `if __name__ == "__main__"` guards, so each file is easy to read in one pass. Prefer keeping `practice-$USER` for later weeks; treat `08` / `09` as optional cleanup. For labs and production code, follow the course [best practices](../../best-practices.md).

### Instructor note: shared bucket `ds2022-fall26`

On the account that owns `ds2022-fall26`, teaching objects are **publicly readable** (not cross-account IAM):

- Allow `s3:GetObject` for `Principal: "*"` on `arn:aws:s3:::ds2022-fall26/*` (or only `cloud.jpg` and `data/*`).
- For `aws s3 sync .../data/`, also allow `s3:ListBucket` on the bucket with a prefix condition on `data/`.
- Adjust Block Public Access only as needed for this teaching bucket.
- Students must not have write access to `ds2022-fall26`.

## Advanced Concepts (Optional)


### Versioning + lifecycle policies

Example (lifecycle rules are configured as bucket lifecycle JSON). Common patterns:

- Delete incomplete multipart uploads after N days.
- Expire objects in a prefix after N days.
- Transition objects to cheaper storage classes after N days.



### S3 event notifications

Example (typical event-driven pipeline):

- S3 `ObjectCreated` event on a prefix (e.g., `book-analysis/`)
- Triggers one of: **Lambda**, **SQS**, or **SNS**
- Your handler reads the new object and runs processing



### Access logging & auditing

Examples:

- **CloudTrail data events** for S3: see who accessed which objects (read/write).
- **S3 server access logs**: deliver access logs to a separate logging bucket for analysis.

### Access control lists (ACLs)

An ACL is a per-object (or per-bucket) permission list: who can read or write that object. Newer accounts often have **Block Public Access** turned on, so public ACLs may be rejected until you change that setting (in class, prefer private objects + `presign` unless the lab asks for public access).

Upload with a canned ACL (example: public read):

```python
import boto3

bucket_name = "practice-mst3k"  # replace with your bucket name
s3 = boto3.client("s3")

with open("cloud.jpg", "rb") as f:
    s3.put_object(
        Bucket=bucket_name,
        Key="folder/in/bucket/cloud.jpg",
        Body=f,
        ContentType="image/jpeg",
        ACL="public-read",
    )
```

Change the ACL on an existing object:

```python
s3.put_object_acl(
    Bucket=bucket_name,
    Key="folder/in/bucket/cloud.jpg",
    ACL="private",
)
```

Common canned ACLs: `private`, `public-read`. For broader rules (whole prefix, many principals), use a **bucket policy** instead (see [IAM policies](../06-iam/README.md#policies)).

## Resources

- [Amazon S3 - Getting started](https://docs.aws.amazon.com/AmazonS3/latest/userguide/GetStartedWithS3.html)
- [AWS CLI - Getting started](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
- [Boto3 Documentation](https://docs.aws.amazon.com/boto3/latest/)
- [Boto3 and S3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [IAM](../06-iam/README.md)

