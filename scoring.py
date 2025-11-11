def calculate_score(issue_tech_stack, user_analysis, user_github_data, repo_full_name):
    """
    Calculates a score out of 10 based on the defined criteria.
    
    issue_tech_stack: {"tech_stack": ["python", "flask"]}
    user_analysis: {"user_skills": ["python"], "explanation_quality": 5, "explanation_summary": "..."}
    user_github_data: PyGithub User object (or similar dict). We'll fake this for now.
    repo_full_name: "owner/repo"
    """
    
    scores = {
        "tech_match": {"score": 0, "max": 4, "details": "No matching skills found."},
        "explanation": {"score": 0, "max": 3, "details": "No explanation provided."},
        "repo_contributions": {"score": 0, "max": 2, "details": "No past contributions to this repo."},
        "other_contributions": {"score": 0, "max": 1, "details": "No recent public contributions."}
    }
    
    if issue_tech_stack.get('tech_stack') and user_analysis.get('user_skills'):
        stack = [s.lower() for s in issue_tech_stack['tech_stack']]
        skills = [s.lower() for s in user_analysis['user_skills']]
        
        matches = set(stack) & set(skills)
        
        if len(matches) > 0:
            match_percentage = len(matches) / len(stack) if len(stack) > 0 else 0
            scores["tech_match"]["score"] = round(match_percentage * 4, 1)
            scores["tech_match"]["details"] = f"Found {len(matches)} matching skills: {', '.join(matches)}"
        else:
            scores["tech_match"]["score"] = 0
            scores["tech_match"]["details"] = f"No skills match required stack: {', '.join(stack)}"

 
    exp_quality = user_analysis.get('explanation_quality', 0)
    scores["explanation"]["score"] = round((exp_quality / 10) * 3, 1)
    scores["explanation"]["details"] = user_analysis.get('explanation_summary', 'N/A')

  
    contribution_count = user_github_data.get('repo_contribution_count', 0)
    
    if contribution_count > 0:
        score = 2 if contribution_count >= 3 else 1
        scores["repo_contributions"]["score"] = score
        scores["repo_contributions"]["details"] = f"User has {contribution_count} merged PR(s) in this repository."
    else:
        scores["repo_contributions"]["score"] = 0 
        scores["repo_contributions"]["details"] = "No merged PRs found in this repository."


    if user_github_data.get('recent_prs') and len(user_github_data['recent_prs']) > 0:
        scores["other_contributions"]["score"] = 1
        scores["other_contributions"]["details"] = "User has recent public PRs."
    else:
        scores["other_contributions"]["score"] = 0
        scores["other_contributions"]["details"] = "No recent public PRs found in profile."
        
    total_score = sum(s['score'] for s in scores.values())
    
    report = f"""
### 🤖 Bot Analysis for @{user_github_data.get('username', 'user')}

Here's a quick assessment of this user's profile for this issue:

**Final Score: {total_score:.1f} / 10**

---

#### Score Breakdown

| Category | Score | Max | Details |
| :--- | :---: | :---: | :--- |
| **Tech Stack Match** | {scores['tech_match']['score']} | {scores['tech_match']['max']} | {scores['tech_match']['details']} |
| **Explanation Quality** | {scores['explanation']['score']} | {scores['explanation']['max']} | {scores['explanation']['details']} |
| **Repo Contributions** | {scores['repo_contributions']['score']} | {scores['repo_contributions']['max']} | {scores['repo_contributions']['details']} |
| **Other Contributions** | {scores['other_contributions']['score']} | {scores['other_contributions']['max']} | {scores['other_contributions']['details']} |

---
*Disclaimer: This is an automated assessment. Maintainers should use this as a guide, not a final decision.*
"""
    
    return report