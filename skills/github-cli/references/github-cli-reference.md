---
name: github-cli
description: Execute GitHub CLI (gh) commands for repository management, issues, pull requests, workflows, releases, and API interactions (REST & GraphQL). Covers REST API calls, GraphQL queries/mutations, solo developer workflows, and team collaboration patterns.
---

# GitHub CLI (gh) Skill

This skill provides comprehensive GitHub CLI integration for managing repositories, issues, pull requests, workflows, releases, and API interactions (both REST and GraphQL).

## Prerequisites

- GitHub CLI (`gh`) must be installed and authenticated
- `gh auth login` successfully completed
- Active internet connection for GitHub API access
- Appropriate repository permissions for target operations

## Quick Reference: Core Commands

### Repository Operations
```bash
gh repo view [owner/repo]                    # View repository details
gh repo clone <owner/repo>                   # Clone a repository
gh repo fork <owner/repo>                    # Fork a repository
gh repo create [name]                        # Create a new repository
gh repo list                                 # List repositories (filtering options available)
```

### Issue Operations
```bash
gh issue list                                # List issues (filterable)
gh issue view <number>                       # View issue details
gh issue create                              # Create an issue (interactive)
gh issue comment <number> -b "message"       # Add a comment
gh issue close <number>                      # Close an issue
gh issue edit <number> --add-label "bug"     # Edit issues and labels
```

### Pull Request Operations
```bash
gh pr list                                   # List pull requests
gh pr view <number>                          # View PR details
gh pr create                                 # Create a PR (interactive)
gh pr checkout <number>                      # Check out a PR locally
gh pr merge <number>                         # Merge a pull request
gh pr review <number>                        # Review a pull request
gh pr comment <number> -b "message"          # Add review comment
gh pr diff <number>                          # View PR changes
```

### Workflow & Actions Operations
```bash
gh workflow list                             # List workflows
gh workflow view <workflow>                  # View workflow details
gh workflow run <workflow>                   # Trigger a workflow
gh run list                                  # List workflow runs
gh run view <run-id>                         # View run details
gh run watch <run-id>                        # Watch a run in real-time
gh run logs <run-id>                         # Fetch run logs
```

### Release Operations
```bash
gh release list                              # List releases
gh release view <tag>                        # View release details
gh release create <tag>                      # Create a release
gh release upload <tag> <files>              # Upload release assets
gh release delete <tag>                      # Delete a release
```

## REST API Operations (`gh api`)

The `gh api` command provides authenticated access to GitHub's REST API with automatic authentication and flexible output formatting.

### Basic REST API Syntax

```bash
# Simple GET request
gh api /repos/{owner}/{repo}/issues

# Specify HTTP method
gh api --method POST /repos/{owner}/{repo}/issues \
  -f title="New issue" \
  -f body="Description here"

# Add query parameters
gh api -X GET search/issues \
  -f q='repo:owner/repo is:open label:bug'

# Paginate through results
gh api repos/{owner}/{repo}/issues --paginate

# Format output with jq
gh api /repos/{owner}/{repo}/issues --jq '.[].title'

# Use templates
gh api repos/{owner}/{repo}/issues \
  --template '{{range .}}{{.number}}: {{.title}}{{"\n"}}{{end}}'
```

### REST API Field Flags

- `-f, --raw-field key=value` — Add a string parameter
- `-F, --field key=value` — Add a typed parameter (auto-detects type: `true`/`false`/`null`/numbers)
- `-H, --header key:value` — Add custom HTTP headers
- `--input file` — Use a file as the request body
- `--cache duration` — Cache the response (e.g., `3600s`, `60m`, `1h`)

### REST API Examples

```bash
# List issues in JSON format
gh api repos/{owner}/{repo}/issues --json number,title,state,labels

# Create an issue
gh api repos/{owner}/{repo}/issues \
  -f title="Bug: Something broken" \
  -f body="Steps to reproduce..."

# Add a comment to an issue
gh api repos/{owner}/{repo}/issues/123/comments \
  -f body="Great catch!"

# Update an issue
gh api repos/{owner}/{repo}/issues/123 \
  -f title="Updated title" \
  --method PATCH

# List team members
gh api orgs/{org}/teams/{team}/members -F per_page=100 --paginate

# Construct dynamic searches
team-members=$(gh api orgs/$ORG/teams/$TEAM/members --paginate --jq '[.[].login] | map("involves:\(.)") | join(" ")')
gh api search/issues -f q="repo:$ORG/$REPO is:open $team_members"
```

## Advanced Pull Request Operations

### Marking a PR as Draft

To convert a pull request to draft status (or from draft to ready), use the REST API via `gh api`:

```bash
# Mark an existing PR as draft
gh api repos/{owner}/{repo}/pulls/{pr_number} \
  --input /dev/stdin \
  --method PATCH << 'EOF'
{
  "draft": true
}
EOF

# Example in practice:
gh api repos/oneTakeda/gmsgq-dad-10345-fusion-platform-control-tower/pulls/80 \
  --input /dev/stdin \
  --method PATCH << 'EOF'
{
  "draft": true
}
EOF

# Mark a PR as ready for review (draft=false)
gh api repos/{owner}/{repo}/pulls/{pr_number} \
  --input /dev/stdin \
  --method PATCH << 'EOF'
{
  "draft": false
}
EOF
```

### Adding Comments to Pull Requests

Comment on a PR using the built-in `gh pr comment` command:

```bash
# Add a simple comment
gh pr comment {pr_number} -b "Your comment text here"

# Add a multi-line comment
gh pr comment {pr_number} -b "First line
Second line
Third line"

# Use a file for comment body (useful for long comments)
gh pr comment {pr_number} --body-file path/to/file.md

# Example: Add status comment to PR #80
gh pr comment 80 -b "Converting to draft — this PR requires PR #101 to be merged first.

**Rationale:**
- PR #101 contains foundational refactoring
- This PR is based on older code with broken paths
- After #101 merges, we'll rebase this branch and it should be ready"
```

### Querying PR Status

```bash
# View a PR in JSON format with specific fields
gh pr view {pr_number} --json isDraft,state,title,number

# Check if a PR is in draft status
is_draft=$(gh pr view {pr_number} --json isDraft -q '.isDraft')
if [ "$is_draft" = "true" ]; then
  echo "PR is in draft status"
else
  echo "PR is ready for review"
fi

# List only draft PRs
gh pr list --state open --json number,title,isDraft \
  --jq '.[] | select(.isDraft == true) | {number, title}'

### Converting a PR to/from Draft using GraphQL

The REST API approach (`--method PATCH` with `draft: true`) does not work reliably. **Use GraphQL mutations instead:**

```bash
# Get the PR Node ID (required for GraphQL mutation)
PR_ID=$(gh pr view {pr_number} --json id -q '.id')

# Mark PR as draft
gh api graphql -f query='mutation {
  convertPullRequestToDraft(input: {pullRequestId: "'$PR_ID'"}) {
    pullRequest {
      isDraft
      title
    }
  }
}'

# Mark PR as ready for review (from draft)
gh api graphql -f query='mutation {
  markPullRequestAsReady(input: {pullRequestId: "'$PR_ID'"}) {
    pullRequest {
      isDraft
      title
    }
  }
}'

# Practical example: Mark PR #80 as draft
PR_ID=$(gh pr view 80 --json id -q '.id')
gh api graphql -f query='mutation {
  convertPullRequestToDraft(input: {pullRequestId: "'$PR_ID'"}) {
    pullRequest {
      isDraft
      title
    }
  }
}'
```

### Real-World Workflow: Draft and Comment

```bash
#!/bin/bash
# Mark a PR as draft and add an explanatory comment

PR_NUMBER=80
REPO="oneTakeda/gmsgq-dad-10345-fusion-platform-control-tower"
COMMENT_FILE="pr_comment.md"

# Create comment file
cat > "$COMMENT_FILE" << 'COMMENT_EOF'
Converting to draft — this PR requires PR #101 (adr-improvements) to be merged first.

**Rationale:**
- PR #101 contains foundational refactoring that moves ADR paths from the deleted `docs/` directory
- This PR is based on older code and references now-nonexistent paths
- After PR #101 merges to main, we'll rebase this branch

**Plan:**
1. Merge PR #101
2. Rebase this PR onto updated main
3. Move back to ready for review
COMMENT_EOF

# Mark PR as draft
gh api repos/$REPO/pulls/$PR_NUMBER \
  --input /dev/stdin \
  --method PATCH << 'EOF'
{
  "draft": true
}
EOF

# Add comment
gh pr comment $PR_NUMBER --body-file "$COMMENT_FILE"

# Verify status
echo "PR #$PR_NUMBER is now in draft status with explanatory comment"
rm "$COMMENT_FILE"
```

## GraphQL API Operations (`gh api graphql`)

GraphQL provides powerful query and mutation capabilities for complex data retrieval and modifications in a single request.

### Why Use GraphQL?

1. **Single request efficiency** — Fetch related data (issues + labels + assignees) in one call instead of multiple REST endpoints
2. **Rate limit advantages** — Complex GraphQL queries cost 5-10 points but can replace 5-10 separate REST calls
3. **Precise data selection** — Request only the fields you need; avoid over-fetching
4. **Relational queries** — Ideal for querying Projects, Issues, PRs with nested data
5. **Mutations** — Create/update/delete operations with controlled response fields

### GraphQL vs. REST: When to Use Which

| Use GraphQL | Use REST |
|-------------|----------|
| Querying relational objects (Projects + Issues) | Bulk data of one type (list all repos) |
| Complex nested data in one request | Single data points (get one issue) |
| Discrete number of items to fetch | Workflows, runners, logs |
| Want to minimize API calls | Need less complex queries |

### Basic GraphQL Syntax

```bash
# Simple query
gh api graphql -f query='
  query {
    viewer {
      login
      name
    }
  }
'

# Query with variables
gh api graphql -f query='
  query($owner:String!, $name:String!) {
    repository(owner: $owner, name: $name) {
      nameWithOwner
      description
      stargazerCount
    }
  }
' -f owner="cli" -f name="cli"

# Mutation (create, update, delete)
gh api graphql -f query='
  mutation($input:AddCommentInput!) {
    addComment(input: $input) {
      commentEdge {
        node {
          url
        }
      }
    }
  }
' -f input='{"subjectId":"MDU6SXNzdWUx","body":"Comment text"}'
```

### GraphQL Queries: Common Patterns

#### Get Repository Information with Issues
```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!) {
    repository(owner: $owner, name: $repo) {
      nameWithOwner
      description
      stargazerCount
      issues(first: 10, states: OPEN) {
        nodes {
          number
          title
          labels(first: 5) {
            nodes {
              name
            }
          }
          assignees(first: 5) {
            nodes {
              login
            }
          }
        }
      }
    }
  }
' -f owner="your-org" -f repo="your-repo"
```

#### List Pull Requests with Reviews
```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!) {
    repository(owner: $owner, name: $repo) {
      pullRequests(first: 10, states: OPEN) {
        nodes {
          number
          title
          author {
            login
          }
          reviews(first: 5) {
            nodes {
              state
              author {
                login
              }
            }
          }
        }
      }
    }
  }
' -f owner="your-org" -f repo="your-repo"
```

#### Query Discussions
```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!) {
    repository(owner: $owner, name: $repo) {
      discussions(first: 10) {
        nodes {
          number
          title
          author {
            login
          }
          comments(first: 5) {
            nodes {
              body
            }
          }
        }
      }
    }
  }
' -f owner="your-org" -f repo="your-repo"
```

### GraphQL Mutations: Common Patterns

#### Add a Comment
```bash
gh api graphql -f query='
  mutation($input:AddCommentInput!) {
    addComment(input: $input) {
      commentEdge {
        node {
          url
          body
        }
      }
    }
  }
' -f input='{"subjectId":"MDU6SXNzdWUxMjM0","body":"Great work!"}'
```

#### Create a Pull Request
```bash
gh api graphql -f query='
  mutation($input:CreatePullRequestInput!) {
    createPullRequest(input: $input) {
      pullRequest {
        number
        url
      }
    }
  }
' -f input='{"repositoryId":"MDEwOlJlcG9zaXRvcnkxMjM0","baseRefName":"main","headRefName":"feature-branch","title":"My feature"}'
```

### Rate Limiting & Cost

Every GraphQL query includes rate limit information. Add this to any query:
```bash
gh api graphql -f query='
  query {
    rateLimit {
      limit
      cost
      remaining
      resetAt
    }
    # ... your actual query ...
  }
'
```

## Command Execution Patterns

### 1. Check Context & Repository
```bash
# Verify you're in the correct repository
gh repo view

# Or explicitly specify a repo with -R flag
gh issue list -R owner/repo
```

### 2. Use Structured Output for Automation
```bash
# JSON output (parse with jq)
gh pr list --json number,title,state,author | jq '.[] | select(.state == "OPEN")'

# Template output (custom formatting)
gh issue list --template '{{range .}}{{.number}}: {{.title}}{{"\n"}}{{end}}'

# Plain text (human-readable)
gh pr list
```

### 3. Combine with Git Commands
```bash
# Create feature branch, push, and open PR
git checkout -b feature/awesome
git push -u origin feature/awesome
gh pr create --title "My Feature" --body "Description" --base main
```

### 4. Confirm Destructive Actions
```bash
# Always verify before deleting or merging
gh issue view 123 --web  # Review in browser first
gh pr merge 456  # Prompts for confirmation by default
```

## Error Handling & Troubleshooting

### Authentication Errors
```bash
# Check authentication status
gh auth status

# Re-authenticate
gh auth login

# Switch accounts
gh auth switch
```

### Permission Errors
- Verify you have write access to the repository
- Check if the repository is private
- Ensure your PAT (Personal Access Token) has required scopes

### Not in a Repository
```bash
# Specify repository explicitly with -R
gh issue list -R owner/repo

# Or navigate to the repository directory first
cd /path/to/repo && gh issue list
```

### API Rate Limits
```bash
# Check current rate limit status
gh api rate_limit  # REST API limits
gh api graphql -f query='{ rateLimit { remaining limit } }'  # GraphQL limits

# Use caching to reduce API calls
gh api repos/{owner}/{repo}/issues --cache 1h
```

## Output Formatting

### JSON Output
```bash
gh issue list --json number,title,state,author,labels
gh api /repos/{owner}/{repo}/issues --jq '.[] | {number: .number, title: .title}'
```

### Template Output (Go templates)
```bash
gh pr list --template '{{range .}}{{.number}}: {{.title}} ({{.author.login}}){{"\n"}}{{end}}'
gh issue list -t '{{range .}}{{.state | upper}} {{.number}}: {{.title}}{{"\n"}}{{end}}'
```

### Tab-Separated Values
```bash
gh issue list --json number,title,state --jq '.[] | [.number, .title, .state] | @tsv'
```

## Tips & Tricks

### 1. Create Aliases for Common Workflows
```bash
# Create a shortcut for PR creation with auto-fill
gh alias set prc 'pr create --fill'

# View PR in browser
gh alias set prv 'pr view --web'

# List my issues
gh alias set my-issues 'issue list --assignee=@me'
```

### 2. Batch Operations with Shell Loops
```bash
# Close all issues matching a label
for issue in $(gh issue list --label "wontfix" --json number -q '.[].number'); do
  gh issue close $issue
done

# Add a comment to all open PRs
gh pr list --state open --json number -q '.[].number' | \
  xargs -I {} gh pr comment {} -b "Reminder: please check tests"
```

### 3. Export Data
```bash
# Export issues to CSV
gh issue list --json number,title,state,labels \
  --jq '.[] | [.number, .title, .state, (.labels | map(.name) | join(","))] | @csv' > issues.csv

# Export PRs with review status
gh pr list --json number,title,author,reviews \
  --jq '.[] | [.number, .title, .author.login, (.reviews | length)] | @tsv'
```

### 4. Pagination with GraphQL
```bash
# GraphQL pagination requires cursor-based approach
gh api graphql -f query='
  query($cursor: String) {
    viewer {
      repositories(first: 10, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          name
        }
      }
    }
  }
' -f cursor="null"
```

### 5. Use Environment Variables in Scripts
```bash
export GITHUB_REPO="owner/repo"
gh issue list -R "$GITHUB_REPO"

# For API calls
export OWNER="cli"
export REPO="cli"
gh api repos/$OWNER/$REPO/issues
```

## When to Use This Skill

Use this skill when the user wants to:
- **Create/manage repositories** — Clone, fork, create, configure
- **Work with issues** — List, create, edit, comment, close, label
- **Manage pull requests** — Create, review, merge, checkout, comment
- **Trigger workflows** — List, view, run, watch, get logs
- **Manage releases** — Create, list, upload assets
- **Query GitHub data** — REST API calls with filtering/pagination
- **Execute GraphQL queries/mutations** — Complex data retrieval, relational queries
- **Automate GitHub workflows** — Batch operations, scripting
- **Solo development** — Quick issue/PR operations
- **Team collaboration** — Coordinating across developers

## When to Load Detailed Guides

For in-depth workflows, ask the user if they need guidance on:

- **Repository Management** — Setting up, protecting branches, configuring settings
- **Issue Workflow** — Labels, milestones, templates, automation
- **Pull Request Best Practices** — Review strategies, merge options, CI/CD integration
- **GitHub Actions Integration** — Triggering workflows, passing data, artifact handling
- **Release Automation** — Creating releases, managing versions, publishing
- **API Scripting** — Building automation, data extraction, integration patterns
- **Team Workflows** — Code review, branch strategies, permissions

## References

- **GitHub CLI Manual**: https://cli.github.com/manual
- **GitHub REST API**: https://docs.github.com/en/rest
- **GitHub GraphQL API**: https://docs.github.com/en/graphql
- **Scripting with GitHub CLI**: https://github.blog/engineering/engineering-principles/scripting-with-github-cli/
- **GraphQL API Guide**: https://github.blog/developer-skills/github/exploring-github-cli-how-to-interact-with-githubs-graphql-api-endpoint/
