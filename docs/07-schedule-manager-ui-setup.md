# Step 7: Schedule Manager UI Setup

This guide walks through deploying the PW3Mate web UI so you can view, add, edit, and delete Powerwall schedules from a browser.

**Time required:** ~30 minutes
**Cost:** ~$0.50/month (S3 + CloudFront + API Gateway + Lambda)

---

## Architecture Overview

```
Browser  →  CloudFront  →  S3 (static UI files)
Browser  →  API Gateway →  Lambda (schedule manager)  →  EventBridge (rules)
                                                       →  Parameter Store (auth)
```

---

## Prerequisites

- Steps 1–6 completed (Tesla API, Lambda functions, EventBridge rules working)
- AWS Console access
- The `ui/` folder from this repository (3 files: `index.html`, `styles.css`, `app.js`)

---

## 7.1 — Store the UI Password in Parameter Store

The UI uses a simple password for authentication.

1. Go to **AWS Systems Manager → Parameter Store**
2. Click **Create parameter**
3. Configure:
   - **Name:** `/tesla/powerwall/ui_password`
   - **Type:** SecureString
   - **Value:** Choose a strong password your brother will use to sign in

---

## 7.2 — Create the Schedule Manager Lambda

### Create the IAM Role

1. Go to **IAM → Roles → Create role**
2. **Trusted entity:** AWS service → Lambda
3. **Managed policies:** Add `AWSLambdaBasicExecutionRole`
4. **Role name:** `PW3Mate-Schedule-Manager-Role`
5. After creation, add this **inline policy** named `PW3Mate-Schedule-Manager-Access`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ParameterStoreAccess",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/tesla/powerwall/*"
        },
        {
            "Sid": "EventBridgeListRules",
            "Effect": "Allow",
            "Action": [
                "events:ListRules",
                "events:ListTargetsByRule"
            ],
            "Resource": "arn:aws:events:*:*:rule/*"
        },
        {
            "Sid": "EventBridgeManageRules",
            "Effect": "Allow",
            "Action": [
                "events:PutRule",
                "events:PutTargets",
                "events:RemoveTargets",
                "events:DeleteRule",
                "events:EnableRule",
                "events:DisableRule"
            ],
            "Resource": "arn:aws:events:*:*:rule/PW3Mate-*"
        }
    ]
}
```

### Create the Lambda Function

1. Go to **Lambda → Create function**
2. Configure:
   - **Function name:** `PW3Mate-Schedule-Manager`
   - **Runtime:** Python 3.11
   - **Architecture:** x86_64
   - **Execution role:** `PW3Mate-Schedule-Manager-Role`
3. Under **Configuration → General configuration:**
   - **Timeout:** 30 seconds
   - **Memory:** 256 MB
4. Under **Configuration → Environment variables**, add:
   - **Key:** `SCHEDULER_LAMBDA_ARN`
   - **Value:** The ARN of your `PW3Mate-Powerwall-Scheduler` Lambda
     (find it on the Lambda console, e.g. `arn:aws:lambda:eu-west-1:123456789012:function:PW3Mate-Powerwall-Scheduler`)
5. Copy the contents of `src/lambda/schedule_manager/lambda_function.py` into the code editor
6. Click **Deploy**

### Allow EventBridge to Invoke the Scheduler Lambda

New schedule rules created via the UI need permission to invoke the Powerwall Scheduler Lambda. Run this once (via CloudShell or CLI):

```bash
aws lambda add-permission \
    --function-name PW3Mate-Powerwall-Scheduler \
    --statement-id AllowEventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com
```

> **Note:** If you already have per-rule permissions from Step 3, this broader permission covers all future rules too.

---

## 7.3 — Create the API Gateway

1. Go to **API Gateway → Create API**
2. Choose **REST API** (not HTTP API) → **Build**
3. Configure:
   - **API name:** `PW3Mate-API`
   - **Endpoint type:** Regional
4. Click **Create API**

### Create the Proxy Resource

1. Click **Create Resource**
2. Check **Proxy resource**
3. **Resource path:** `/{proxy+}`
4. Check **Enable API Gateway CORS**
5. Click **Create Resource**

### Create the ANY Method

1. Select the `/{proxy+}` resource
2. Click **Create Method**
3. Configure:
   - **Method type:** ANY
   - **Integration type:** Lambda Function
   - **Lambda proxy integration:** Enabled (checked)
   - **Lambda function:** `PW3Mate-Schedule-Manager`
4. Click **Create Method**

### Enable CORS on Root

1. Select the `/` root resource
2. Click **Enable CORS**
3. Check all methods (GET, POST, PUT, DELETE, OPTIONS)
4. **Access-Control-Allow-Origin:** `*`
5. **Access-Control-Allow-Headers:** `Content-Type,Authorization`
6. Click **Save**

### Deploy the API

1. Click **Deploy API**
2. **Stage name:** `prod`
3. Click **Deploy**
4. Copy the **Invoke URL** — it looks like:
   `https://abc123def4.execute-api.eu-west-1.amazonaws.com/prod`

---

## 7.4 — Configure the Frontend

Before uploading to S3, set the API URL in `app.js`.

Open `ui/app.js` and find this line near the top:

```javascript
const API_BASE = window.PW3_API_BASE || '';
```

You have two options:

**Option A — Hardcode the URL** (simplest):
Replace the line with:
```javascript
const API_BASE = 'https://abc123def4.execute-api.eu-west-1.amazonaws.com/prod';
```

**Option B — Set it at load time** (more flexible):
Add a script tag in `index.html` before the `app.js` script:
```html
<script>window.PW3_API_BASE = 'https://abc123def4.execute-api.eu-west-1.amazonaws.com/prod';</script>
<script src="app.js"></script>
```

---

## 7.5 — Create the S3 Bucket

1. Go to **S3 → Create bucket**
2. Configure:
   - **Bucket name:** `pw3mate-ui` (must be globally unique — try `pw3mate-ui-yourname`)
   - **Region:** Same as your Lambda functions
   - **Block all public access:** Leave **checked** (CloudFront will access it)
3. Click **Create bucket**

### Upload the UI Files

1. Open the bucket
2. Click **Upload**
3. Add the three files from the `ui/` folder:
   - `index.html`
   - `styles.css`
   - `app.js`
4. Click **Upload**

---

## 7.6 — Create the CloudFront Distribution

1. Go to **CloudFront → Create distribution**
2. Configure:
   - **Origin domain:** Select your S3 bucket
   - **Origin access:** Origin access control settings (recommended)
   - Click **Create new OAC** → Use defaults → **Create**
   - **Default root object:** `index.html`
   - **Viewer protocol policy:** Redirect HTTP to HTTPS
   - **Price class:** Use only North America and Europe (cheapest)
3. Click **Create distribution**

### Update the S3 Bucket Policy

After creating the distribution, CloudFront will show a banner with the bucket policy. Click **Copy policy** and apply it:

1. Go to your S3 bucket → **Permissions → Bucket policy**
2. Paste the policy (it grants CloudFront read access)
3. Click **Save changes**

### Wait for Deployment

The CloudFront distribution takes 5–10 minutes to deploy. Once the status shows **Enabled**, your UI is live at:

```
https://d1234abcdef.cloudfront.net
```

---

## 7.7 — Test Everything

1. Open the CloudFront URL in your browser
2. Enter the password you stored in Parameter Store
3. You should see your existing Powerwall schedules
4. Try adding a test schedule, editing it, then deleting it
5. Verify in the AWS EventBridge console that rules are created/removed

---

## 7.8 — Optional: Custom Domain

If you want a friendly URL like `powerwall.yourdomain.com`:

1. Request an SSL certificate in **AWS Certificate Manager** (must be in `us-east-1` for CloudFront)
2. In CloudFront → **Edit distribution** → **Alternate domain name (CNAME):** `powerwall.yourdomain.com`
3. Select your certificate
4. Add a CNAME record in your DNS: `powerwall.yourdomain.com` → `d1234abcdef.cloudfront.net`

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Login fails with "UI password not configured" | Ensure `/tesla/powerwall/ui_password` exists in Parameter Store |
| Login fails with "Invalid password" | Check the password matches exactly (case-sensitive) |
| "Failed to load schedules" after login | Check the API Gateway URL is correct in `app.js` |
| CORS errors in browser console | Verify CORS is enabled on API Gateway and re-deploy the API |
| Schedules load but add/edit/delete fails | Check the Lambda IAM role has EventBridge permissions |
| New schedules don't trigger the Powerwall | Run the `aws lambda add-permission` command from Step 7.2 |

---

## Cost Breakdown

| Service | Monthly Cost |
|---|---|
| S3 (static hosting) | < $0.01 |
| CloudFront (CDN) | < $0.01 |
| API Gateway | < $0.01 |
| Lambda (schedule manager) | < $0.01 |
| **Total** | **~$0.01 – $0.50** |

The higher end accounts for CloudFront's minimum charge. Actual usage costs will be negligible.
