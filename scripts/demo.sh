#!/bin/bash
set -euo pipefail

# ── InstaLite Demo Script (curl-based backup) ────────────
# Usage: ./scripts/demo.sh <API_URL>
# Example: ./scripts/demo.sh https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/

API_URL="${1:?Usage: $0 <API_URL>}"
API_URL="${API_URL%/}"

echo "========================================="
echo "  InstaLite — Demo Script"
echo "  API: ${API_URL}"
echo "========================================="

echo ""
echo "Step 1: Sign up Alice"
ALICE=$(curl -s -X POST "${API_URL}/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@demo.com","password":"password123"}')
echo "$ALICE" | python3 -m json.tool 2>/dev/null || echo "$ALICE"
ALICE_TOKEN=$(echo "$ALICE" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null || true)

echo ""
echo "Step 2: Sign up Bob"
BOB=$(curl -s -X POST "${API_URL}/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","email":"bob@demo.com","password":"password123"}')
echo "$BOB" | python3 -m json.tool 2>/dev/null || echo "$BOB"
BOB_TOKEN=$(echo "$BOB" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null || true)
BOB_ID=$(echo "$BOB" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['userId'])" 2>/dev/null || true)

echo ""
echo "Step 3: Bob creates a post"
POST=$(curl -s -X POST "${API_URL}/posts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${BOB_TOKEN}" \
  -d '{"imageUrl":"https://picsum.photos/600/400","caption":"Beautiful sunset!"}')
echo "$POST" | python3 -m json.tool 2>/dev/null || echo "$POST"
POST_ID=$(echo "$POST" | python3 -c "import sys,json; print(json.load(sys.stdin)['postId'])" 2>/dev/null || true)

echo ""
echo "Step 4: Alice searches for Bob"
SEARCH=$(curl -s -X GET "${API_URL}/search/users?q=bob" \
  -H "Authorization: Bearer ${ALICE_TOKEN}")
echo "$SEARCH" | python3 -m json.tool 2>/dev/null || echo "$SEARCH"

echo ""
echo "Step 5: Alice follows Bob"
curl -s -X POST "${API_URL}/users/${BOB_ID}/follow" \
  -H "Authorization: Bearer ${ALICE_TOKEN}" | python3 -m json.tool 2>/dev/null

echo ""
echo "Step 6: Alice views feed"
curl -s -X GET "${API_URL}/feed" \
  -H "Authorization: Bearer ${ALICE_TOKEN}" | python3 -m json.tool 2>/dev/null

echo ""
echo "Step 7: Alice likes Bob's post"
curl -s -X POST "${API_URL}/posts/${POST_ID}/like" \
  -H "Authorization: Bearer ${ALICE_TOKEN}" | python3 -m json.tool 2>/dev/null

echo ""
echo "Step 8: Alice comments on Bob's post"
COMMENT=$(curl -s -X POST "${API_URL}/posts/${POST_ID}/comments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ALICE_TOKEN}" \
  -d '{"text":"Amazing view!"}')
echo "$COMMENT" | python3 -m json.tool 2>/dev/null || echo "$COMMENT"
ALICE_COMMENT_ID=$(echo "$COMMENT" | python3 -c "import sys,json; print(json.load(sys.stdin)['commentId'])" 2>/dev/null || true)

echo ""
echo "Step 9: Bob replies to Alice's comment"
curl -s -X POST "${API_URL}/posts/${POST_ID}/comments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${BOB_TOKEN}" \
  -d "{\"text\":\"Thanks!\",\"parentCommentId\":\"${ALICE_COMMENT_ID}\"}" | python3 -m json.tool 2>/dev/null

echo ""
echo "Step 10: Bob checks notifications"
curl -s -X GET "${API_URL}/notifications" \
  -H "Authorization: Bearer ${BOB_TOKEN}" | python3 -m json.tool 2>/dev/null

echo ""
echo "Step 11: Get Bob's profile"
curl -s -X GET "${API_URL}/users/${BOB_ID}" | python3 -m json.tool 2>/dev/null

echo ""
echo "Step 12: Get post detail with comments"
curl -s -X GET "${API_URL}/posts/${POST_ID}" | python3 -m json.tool 2>/dev/null
curl -s -X GET "${API_URL}/posts/${POST_ID}/comments" | python3 -m json.tool 2>/dev/null

echo ""
echo "Step 13: Bob deletes his post"
curl -s -X DELETE "${API_URL}/posts/${POST_ID}" \
  -H "Authorization: Bearer ${BOB_TOKEN}" | python3 -m json.tool 2>/dev/null

echo ""
echo "Step 14: Alice checks feed after deletion"
curl -s -X GET "${API_URL}/feed" \
  -H "Authorization: Bearer ${ALICE_TOKEN}" | python3 -m json.tool 2>/dev/null

echo ""
echo "========================================="
echo "  Demo Complete!"
echo "========================================="
