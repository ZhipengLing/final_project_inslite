# InstaLite: Instagram-Lite on AWS

A serverless social media application built for **CS6620 Cloud Computing** (Northeastern University). InstaLite delivers core Instagram functionality — posts, feeds, likes, comments, follows, and notifications — using a fully serverless architecture on AWS with Lambda, API Gateway, DynamoDB, S3, and CDK Python.

## Architecture Overview

The system is composed of 10 independent Lambda microservices behind a single API Gateway, with DynamoDB for data persistence and S3 for media storage and static frontend hosting. All infrastructure is defined as code using AWS CDK v2 in Python.

See [DESIGN_DOC_EN.md](DESIGN_DOC_EN.md) for the full architecture diagram and design details.

## Tech Stack

| Layer          | Technology                        |
|----------------|-----------------------------------|
| Language       | Python 3.12                       |
| IaC            | AWS CDK v2 (Python)               |
| Compute        | AWS Lambda                        |
| API            | Amazon API Gateway (REST)         |
| Database       | Amazon DynamoDB                   |
| Storage        | Amazon S3                         |
| Frontend       | Vanilla HTML / CSS / JS (SPA)     |

## Project Structure

```
final_project_inslite/
├── app.py                  # CDK app entry point
├── cdk.json                # CDK configuration
├── requirements.txt        # Python dependencies
├── stacks/                 # CDK stack definitions (5 stacks)
│   ├── api_stack.py        #   API Gateway + 10 Lambda integrations
│   ├── database_stack.py   #   6 DynamoDB tables with GSIs
│   ├── storage_stack.py    #   S3 media bucket with CORS + public read
│   ├── layer_stack.py      #   Shared Lambda layer (JWT, response, DB utils)
│   └── frontend_stack.py   #   S3 static website hosting
├── lambda_code/            # Lambda function source (10 microservices)
│   ├── auth/               #   Signup + Login (JWT)
│   ├── user_profile/       #   Get / Update profile
│   ├── post_create/        #   Create post
│   ├── post_read/          #   Get post / Get user's posts
│   ├── media/              #   Presigned URL for S3 upload
│   ├── like/               #   Like / Unlike / List likes
│   ├── comment/            #   Add / List comments
│   ├── follow/             #   Follow / Unfollow / List followers & following
│   ├── feed/               #   Feed (own + followed users' posts)
│   └── notification/       #   List / Mark-read notifications
├── layers/common/          # Shared Lambda layer
│   ├── build_layer.sh      #   Builds layer.zip
│   └── python/             #   auth_utils.py, response_utils.py, db_utils.py
├── frontend/               # Single-page application
│   ├── index.html
│   ├── css/style.css
│   └── js/                 #   config, api, router, components, auth, feed,
│                           #   post, profile, notifications
├── scripts/
│   ├── deploy.sh           #   One-command full deploy
│   ├── cleanup.sh          #   Tear down all resources
│   └── demo.sh             #   curl-based end-to-end demo
├── DESIGN_DOC_EN.md        # English design document
└── DESIGN_DOC_CN.md        # Chinese design document
```

## Prerequisites

- **Python 3.12**
- **AWS CLI** configured with valid credentials (`aws configure`)
- **AWS CDK v2** (`npm install -g aws-cdk`)
- **Node.js** (required by CDK)
- **conda** environment `cs6620` (recommended)

## Quick Start

```bash
conda activate cs6620
pip install -r requirements.txt
bash scripts/deploy.sh
```

The deploy script will:
1. Build the Lambda Layer (pip install + zip)
2. Bootstrap CDK (if needed)
3. Deploy all 5 stacks (DB, Storage, Layer, API, Frontend)
4. Extract the API URL and inject it into `frontend/js/config.js`
5. Upload the frontend to S3

After deploy, the script prints the **Frontend URL** and **API URL**.

## Re-upload Frontend

If you make changes to the frontend files only (no CDK changes), re-upload with:

```bash
aws s3 sync frontend/ s3://<frontend-bucket-name>/ --delete
```

The bucket name is printed at the end of `deploy.sh` or in `cdk-outputs.json`.

## Cleanup

```bash
bash scripts/cleanup.sh
```

This destroys all CDK stacks and removes all associated AWS resources.

---

## 10 Microservices

| # | Service | Endpoints | AWS Services |
|---|---------|-----------|--------------|
| 1 | **Auth** | `POST /auth/signup`, `POST /auth/login` | Lambda + API GW + DynamoDB |
| 2 | **User Profile** | `GET /users/{userId}`, `PUT /users/{userId}` | Lambda + API GW + DynamoDB |
| 3 | **Post Create** | `POST /posts` | Lambda + API GW + DynamoDB |
| 4 | **Post Read** | `GET /posts/{postId}`, `GET /users/{userId}/posts` | Lambda + API GW + DynamoDB |
| 5 | **Media Upload** | `POST /media/presign` | Lambda + API GW + S3 |
| 6 | **Like** | `POST /posts/{postId}/like`, `DELETE /posts/{postId}/like`, `GET /posts/{postId}/likes` | Lambda + API GW + DynamoDB |
| 7 | **Comment** | `POST /posts/{postId}/comments`, `GET /posts/{postId}/comments` | Lambda + API GW + DynamoDB |
| 8 | **Follow** | `POST /users/{userId}/follow`, `DELETE /users/{userId}/follow`, `GET /users/{userId}/followers`, `GET /users/{userId}/following` | Lambda + API GW + DynamoDB |
| 9 | **Feed** | `GET /feed` | Lambda + API GW + DynamoDB |
| 10 | **Notification** | `GET /notifications`, `PUT /notifications/{notifId}/read` | Lambda + API GW + DynamoDB |

---

## Team Assignment

| Member | Microservices | Key Work |
|--------|---------------|----------|
| Tian Yuan | Auth + User Profile | JWT authentication, user CRUD, Lambda Layer |
| Zhipeng Ling | Post Creation + Media Upload | S3 presigned URLs, post creation, image handling |
| Xijia Zeng | Post Read + Feed | Query patterns, feed aggregation, DynamoDB GSIs |
| Hailey Pang | Like + Comment | Social interactions, atomic counters, notification writes |
| Yuchong Zhang | Follow + Notification + Frontend | Follow graph, notification list, full frontend SPA |
---

## Live Demo Guide

### Step 0: Deploy

```bash
conda activate cs6620
pip install -r requirements.txt
bash scripts/deploy.sh
```

After deploy completes, open the **Frontend URL** printed in the terminal.

### Demo Flow (10 Steps)

| Step | Action | Expected Result |
|------|--------|-----------------|
| **1** | Open the website | InstaLite login page with Quick Demo Login buttons |
| **2** | Click **Alice** quick login | Toast: login success, redirected to Feed |
| **3** | Open an **incognito window**, open the same URL, click **Bob** quick login | Bob logged in, sees Feed |
| **4** | Bob: click **+** in navbar, select an image, write a caption, click **Share Post** | Toasts: presign 201, "Uploading to S3...", post 201. Redirected to Feed — post visible **with image** |
| **5** | Switch to Alice's window, click the **profile** icon in navbar, change URL to `#profile/<Bob's userId>`, click **Follow** | Button changes to "Following", follower count 0 -> 1 |
| **6** | Alice: click **Home** icon (house) in navbar | Bob's post with image appears in Alice's Feed |
| **7** | Alice: click the **heart** button on the post | Heart turns red, likes count 0 -> 1 |
| **8** | Alice: click **comment** icon to open post detail, type "Amazing view!", click **Post** | Comment appears below the post |
| **9** | Switch to Bob's window, click the **bell** icon | Notifications page shows: "alice started following you", "alice liked your post", "alice commented on your post" |
| **10** | Expand the **API Activity Log** panel at the bottom | See all API requests with method, path, status, and response time |

### How to Get Bob's userId

In Bob's browser, press `F12` to open DevTools, go to Console, and run:

```js
JSON.parse(localStorage.getItem("inslite_user")).userId
```

Copy the userId and use it in Alice's address bar: `#profile/<paste-userId-here>`

### Backup: curl-based Demo

If the frontend demo isn't working, run the CLI demo:

```bash
bash scripts/demo.sh <API_URL>
```

Example:

```bash
bash scripts/demo.sh https://xxxxx.execute-api.us-west-2.amazonaws.com/prod/
```

---

## Design Documents

- [English Design Document](DESIGN_DOC_EN.md) — Full architecture, API spec, data model, deployment guide
- [Chinese Design Document](DESIGN_DOC_CN.md) — Same content in Chinese for team reference
