import os
import anthropic
import requests

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
PR_NUMBER = os.environ["PR_NUMBER"]
REPO = os.environ["REPO"]

def get_pr_diff():
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    files = response.json()

    diff_text = ""
    for f in files:
        filename = f["filename"]
        patch = f.get("patch", "")
        if patch:
            diff_text += f"\n### {filename}\n```\n{patch}\n```\n"

    return diff_text


def post_comment(comment):
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(url, headers=headers, json={"body": comment})
    print(f"Comment posted: {response.status_code}")


def review_pr():
    diff = get_pr_diff()

    if not diff:
        print("No diff found")
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are an expert code reviewer. Review the following pull request diff and provide constructive feedback.

Focus on:
1. Code quality and best practices
2. Potential bugs or edge cases
3. Security concerns
4. Performance issues
5. Suggestions for improvement

Be concise and actionable. Format your review with clear sections.
Start with a brief summary, then list specific issues with file references.

PR DIFF:
{diff}

Provide your code review:"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    review = message.content[0].text
    comment = f"## 🤖 Claude AI Code Review\n\n{review}"
    post_comment(comment)


if __name__ == "__main__":
    review_pr()