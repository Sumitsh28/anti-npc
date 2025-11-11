import os
import json
from openai import OpenAI


try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Make sure OPENAI_API_KEY is set in your .env file.")
    client = None

def analyze_issue_and_repo(issue_data, repo_data):
    """
    Uses OpenAI to analyze the issue and repo to determine the required tech stack.
    """
    if not client:
        raise Exception("OpenAI client is not initialized.")

    system_prompt = """
    You are an expert code analyst. Your task is to analyze an issue description and a
    repository's README/language to determine the skills and technologies required
    to solve the issue.
    
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