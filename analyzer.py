import os
import json
from openai import OpenAI


try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Make sure OPENAI_API_KEY is set in your .env file.")
    client = None

def analyze_comment_intent(comment_body):
    """
    NEW: Uses OpenAI to determine if a comment shows "intent to solve"
    or is just a simple request.
    """
    if not client:
        raise Exception("OpenAI client is not initialized.")
        
    system_prompt = """
    You are an AI assistant analyzing GitHub comments. Your task is to
    determine if a user's comment shows a genuine "intent to solve" an issue
    (e.g., they propose a solution, ask a clarifying question about the code,
    or state they are working on it) OR if it's a simple "request to be assigned"
    (e.g., "please assign me", "can i work on this?", "assign").
    
    Respond *only* with a JSON object with one boolean key: "wants_to_solve".
    Set it to true for "intent to solve", false for a simple request.
    
    - "please assign me" -> {"wants_to_solve": true}
    - "can i take this?" -> {"wants_to_solve": true}
    - "i think the bug is in the login.js file" -> {"wants_to_solve": true}
    - "what is this repo for?" -> {"wants_to_solve": false}
    - "great issue!" -> {"wants_to_solve": false}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": comment_body}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        result = json.loads(response.choices[0].message.content)
        return result.get('wants_to_solve', False)
        
    except Exception as e:
        print(f"Error in OpenAI call (analyze_comment_intent): {e}")
        return False


def analyze_issue_and_repo(issue_data, repo_data):
    """
    Uses OpenAI to analyze the issue and repo to determine the required tech stack.
    """
    if not client:
        raise Exception("OpenAI client is not initialized.")

    system_prompt = """
    You are an expert code analyst. Your task is to analyze an issue description,
    its labels, and a repository's README/language to determine the skills and
    technologies required to solve the issue.
    
    Pay close attention to file paths in the issue body and the labels
    (e.g., 'frontend', 'database', 'bug') as they are strong clues.
    
    Respond *only* with a JSON object containing one key: "tech_stack",
    which is an array of strings.
    
    Example:
    {
      "tech_stack": ["python", "flask", "api", "react", "css"]
    }
    """
    
    user_content = f"""
    Repository Language: {repo_data.get('language')}
    
    Repository README (snippet):
    ---
    {repo_data.get('readme', '')[:2000]}
    ---
    
    Issue Title: {issue_data.get('title')}
    
    Issue Labels: {", ".join(issue_data.get('labels', []))}
    
    Issue Body:
    ---
    {issue_data.get('body')}
    ---
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        return json.loads(result_text)
        
    except Exception as e:
        print(f"Error in OpenAI call (analyze_issue_and_repo): {e}")
        return {"tech_stack": []}

def analyze_user(user_data, user_comment):
    """
    Uses OpenAI to analyze a user's profile and their issue comment
    to determine their skills and the quality of their explanation.
    """
    if not client:
        raise Exception("OpenAI client is not initialized.")

    system_prompt = """
    You are a hiring manager for a software company. Your task is to evaluate
    a candidate based on their GitHub profile and their comment on an issue.
    
    Infer their skills from their bio, their recent PR titles, and
    especially the languages of their public repositories.
    
    Respond *only* with a JSON object with three keys:
    1. "user_skills": An array of strings representing their stated or implied skills.
    2. "explanation_quality": A score from 0 to 10 assessing the quality of their
       comment (Did they explain *how* they would solve it, or just ask to be assigned?).
       0 = just asking, 10 = detailed plan.
    3. "explanation_summary": A brief one-sentence summary of their comment quality.
    
    Example:
    {
      "user_skills": ["javascript", "react", "python", "data-visualization"],
      "explanation_quality": 1,
      "explanation_summary": "User only asked to be assigned, providing no plan."
    }
    """
    
    user_content = f"""
    User's GitHub Bio:
    ---
    {user_data.get('bio')}
    ---
    
    User's Recent PRs (titles):
    ---
    {user_data.get('recent_prs')}
    ---
    
    User's Public Repo Languages (from last 10 updated repos):
    ---
    {", ".join(user_data.get('repo_languages', []))}
    ---

    User's Comment on Issue:
    ---
    {user_comment}
    ---
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        return json.loads(result_text)
        
    except Exception as e:
        print(f"Error in OpenAI call (analyze_user): {e}")
        return {"user_skills": [], "explanation_quality": 0, "explanation_summary": "Error during analysis."}
    
def analyze_contribution_quality(pr_diffs):
    """
    Uses OpenAI to analyze the quality/complexity of past PR diffs.
    """
    if not client:
        raise Exception("OpenAI client is not initialized.")
        
    if not pr_diffs:
        return {"average_complexity": 0, "summary": "No past PRs in this repo to analyze."}

    system_prompt = """
    You are a senior software engineer. Analyze the provided code diffs from a
    user's past pull requests. Your task is to determine the average complexity
    of their work. A "1" is a simple typo or doc update. A "10" is a
    complex new feature, major refactor, or difficult bug fix.
    
    Respond *only* with a JSON object with two keys:
    1. "average_complexity": A single number from 1 to 10.
    2. "summary": A one-sentence summary of their past work quality.
    
    Example:
    {
      "average_complexity": 7.5,
      "summary": "User has experience with significant feature work and bug fixes."
    }
    """
    
    user_content = f"""
    Please analyze the following code diffs (up to 3):
    
    --- DIFF 1 ---
    {pr_diffs[0]}
    
    --- DIFF 2 ---
    {pr_diffs[1] if len(pr_diffs) > 1 else "N/A"}
    
    --- DIFF 3 ---
    {pr_diffs[2] if len(pr_diffs) > 2 else "N/A"}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        return json.loads(result_text)
        
    except Exception as e:
        print(f"Error in OpenAI call (analyze_contribution_quality): {e}")
        return {"average_complexity": 0, "summary": "Error analyzing PR diffs."}