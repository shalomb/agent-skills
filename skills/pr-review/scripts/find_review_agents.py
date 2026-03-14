#!/usr/bin/env python3
"""
Search a repository for review agents/skills.

Looks for agent definitions in patterns like:
- .github/agents/*.md
- .claude/agents/*.md
- .gemini/agents/*.md
- .agents/*.md
- docs/agents/*.md
- etc.

Usage:
    find_review_agents.py <repo_dir> [--patterns <pattern1,pattern2>]

Output: JSON with list of found agent files and their content
"""

import sys
import json
from pathlib import Path
from typing import Optional

def find_review_agents(repo_dir: str, patterns: Optional[list] = None) -> dict:
    """
    Find review agents in the repository.
    
    Args:
        repo_dir: Path to repository root
        patterns: Optional list of glob patterns to search
    
    Returns:
        dict with found_agents list (file path, agent name, content snippet)
    """
    
    repo_path = Path(repo_dir)
    
    if not repo_path.exists():
        raise ValueError(f"Repository directory not found: {repo_dir}")
    
    # Default patterns to search
    if patterns is None:
        patterns = [
            '.github/agents/*.md',
            '.github/agents/**/*.md',
            '.claude/agents/*.md',
            '.claude/agents/**/*.md',
            '.gemini/agents/*.md',
            '.gemini/agents/**/*.md',
            '.agents/*.md',
            '.agents/**/*.md',
            'docs/agents/*.md',
            'docs/agents/**/*.md',
            '.github/REVIEW*.md',
            '.claude/REVIEW*.md',
            'AGENTS.md',
            'CLAUDE.md',
        ]
    
    found_agents = []
    seen = set()
    
    for pattern in patterns:
        for file_path in repo_path.glob(pattern):
            if not file_path.is_file():
                continue
            
            rel_path = str(file_path.relative_to(repo_path))
            
            # Avoid duplicates
            if rel_path in seen:
                continue
            seen.add(rel_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract agent name from filename or frontmatter
                agent_name = file_path.stem
                
                # Try to parse YAML frontmatter if present
                if content.startswith('---'):
                    end_marker = content.find('\n---', 3)
                    if end_marker > 0:
                        frontmatter = content[3:end_marker]
                        # Extract name: field
                        for line in frontmatter.split('\n'):
                            if line.startswith('name:'):
                                agent_name = line.split(':', 1)[1].strip()
                                break
                
                # Get first 1000 chars as preview
                content_preview = content[:1000]
                
                found_agents.append({
                    'path': rel_path,
                    'name': agent_name,
                    'file': file_path.name,
                    'size_bytes': len(content),
                    'content_preview': content_preview,
                    'full_path': str(file_path)
                })
            
            except Exception as e:
                found_agents.append({
                    'path': rel_path,
                    'error': str(e),
                    'full_path': str(file_path)
                })
    
    return {
        'found_agents': found_agents,
        'count': len(found_agents),
        'repo_path': str(repo_path)
    }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: find_review_agents.py <repo_dir> [--patterns <pattern1,pattern2>]", file=sys.stderr)
        sys.exit(1)
    
    repo_dir = sys.argv[1]
    patterns = None
    
    if len(sys.argv) > 3 and sys.argv[2] == '--patterns':
        patterns = sys.argv[3].split(',')
    
    try:
        result = find_review_agents(repo_dir, patterns)
        print(json.dumps(result, indent=2))
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
