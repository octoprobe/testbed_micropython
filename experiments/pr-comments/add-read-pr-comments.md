# Add and read comments on pr

Example PR to play with:

  * https://github.com/octoprobe/testbed_micropython/pull/75
  * https://github.com/micropython/micropython/pull/17782

```bash
REPO="micropython/micropython"
PR_NUMBER="17782"
BOT_LOGIN="octoprobe-bot"

REPO="octoprobe/testbed_micropython"
PR_NUMBER="75"
BOT_LOGIN="hmaerki"
MARKER='<!-- octoprobe-meta: '

gh pr view "$PR_NUMBER" --repo "$REPO" --json url,number,author,title,headRefOid,state,files,comments

gh pr list --repo octoprobe/testbed_micropython --json url,number,author,title,headRefOid,state,files

cat << EOF > comment.md
# octoprobe test result

The metadata is invisilbe:
<!-- octoprobe-meta: {"report":"v1","sha":"<full_sha>","status":"ok"} -->
EOF

gh pr comment "https://github.com/$REPO/pull/$PR_NUMBER" --body-file "comment.md"

gh pr view "https://github.com/$REPO/pull/$PR_NUMBER" --json comments --jq '.comments[] | select(.author.login == "hmaerki")'

gh pr view "https://github.com/$REPO/pull/$PR_NUMBER" --json comments --jq ".comments[] | select(.author.login == \"hmaerki\" and (.body | contains(\"$MARKER\")))"

```