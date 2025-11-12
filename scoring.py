def calculate_score(issue_tech_stack, user_analysis, user_github_data, contribution_analysis, repo_full_name):
    """
    Calculates a score and generates a dynamic, actionable report.
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
            stack_str = ", ".join(stack) if stack else "N/A"
            scores["tech_match"]["details"] = f"No skills match required stack: {stack_str}"

 
    exp_quality = user_analysis.get('explanation_quality', 0)
    scores["explanation"]["score"] = round((exp_quality / 10) * 3, 1)
    scores["explanation"]["details"] = user_analysis.get('explanation_summary', 'N/A')

  
    contribution_count = user_github_data.get('repo_contribution_count', 0)
    avg_complexity = contribution_analysis.get('average_complexity', 0)
    
    if contribution_count > 0:
        if avg_complexity >= 9:
            score = 2
        elif avg_complexity >= 7:
            score = 1.5
        elif avg_complexity >= 4:
            score = 1
        elif avg_complexity > 0:
            score = 0.5
        else:
            score = 0
            
        scores["repo_contributions"]["score"] = score
        scores["repo_contributions"]["details"] = contribution_analysis.get('summary', 'Analyzed past contributions.')
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
    
    
    username = user_github_data.get('username', 'user')
    required_skills = ", ".join(issue_tech_stack.get('tech_stack', ['N/A']))
    explanation_score = scores["explanation"]["score"]
    repo_score = scores["repo_contributions"]["score"]
    tech_score = scores["tech_match"]["score"]
    
    feedback_summary = ""
    
    if total_score > 8.0:
        feedback_summary = f"""
### 🚀 Assessment: Excellent Match
Hi @maintainer! This user looks like a **perfect fit** ({total_score:.1f}/10).
Their profile shows a strong skill match and high-quality past contributions relevant to this repo.
"""
    elif total_score >= 4.0:
        if tech_score < 1.0:
            feedback_summary = f"""
### ⚠️ Assessment: Potential Mismatch
Hi @{username} ({total_score:.1f}/10). Thanks for your interest! This issue seems to require skills in **{required_skills}**, which don't appear in your recent public profile. 
Could you clarify your experience with these technologies?
"""
        elif explanation_score < 1.0:
            feedback_summary = f"""
### 💡 Assessment: Good Profile, Needs Plan
Hi @{username} ({total_score:.1f}/10). You have a relevant profile! However, your comment didn't include a plan.
Could you briefly explain *how* you'd approach solving this issue?
"""
        else:
            feedback_summary = f"""
### 🤔 Assessment: Good Fit
Hi @{username}. You look like a good fit for this issue ({total_score:.1f}/10). 
@maintainer this user seems well-qualified.
"""
    else: 
        if total_score < 2.0 and explanation_score == 0 and repo_score == 0:
            feedback_summary = f"""
### 🚩 Assessment: Low-Effort Request
Hi @maintainer. **Warning:** This user's request ({total_score:.1f}/10) appears to be a low-effort comment.
There is no plan, no matching skills, and no past contribution history in this repo.
"""
        else:
            feedback_summary = f"""
### 📉 Assessment: Not a Strong Match
Hi @{username} ({total_score:.1f}/10). Thanks for your interest, but based on your public profile, this issue may not be the best fit.
It requires skills in **{required_skills}**, and your profile doesn't show a strong match.
"""

    report = f"""
{feedback_summary}

---

### 🤖 Detailed Analysis for @{username}

**Final Score: {total_score:.1f} / 10**

| Category | Score | Max | Details |
| :--- | :---: | :---: | :--- |
| **Tech Stack Match** | {scores['tech_match']['score']} | {scores['tech_match']['max']} | {scores['tech_match']['details']} |
| **Explanation Quality** | {scores['explanation']['score']} | {scores['explanation']['max']} | {scores['explanation']['details']} |
| **Repo Contribution Quality** | {scores['repo_contributions']['score']} | {scores['repo_contributions']['max']} | {scores['repo_contributions']['details']} |
| **Other Contributions** | {scores['other_contributions']['score']} | {scores['other_contributions']['max']} | {scores['other_contributions']['details']} |

---
*Disclaimer: This is an automated assessment. Maintainers should use this as a guide, not a final decision.*
"""
    
    return report