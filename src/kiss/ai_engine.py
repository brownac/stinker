import json
import requests
from kiss.config import Config

class AIEngine:
    """
    AI provider abstraction layer
    Supports OpenAI, Anthropic, and custom endpoints
    """
    
    def __init__(self, provider=None):
        self.provider = provider or Config.AI_PROVIDER
        self._validate_config()
    
    def _validate_config(self):
        """Validate AI provider configuration"""
        if self.provider == 'openai':
            if not Config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        elif self.provider == 'anthropic':
            if not Config.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
        elif self.provider == 'custom':
            if not Config.CUSTOM_AI_ENDPOINT:
                raise ValueError("CUSTOM_AI_ENDPOINT is required for custom provider")
    
    def review_code(self, changes: list, patterns: dict, repo_name: str) -> dict:
        """
        Review code changes and provide simplification suggestions
        
        Args:
            changes: List of code changes from diff parser
            patterns: Learned patterns from the codebase
            repo_name: Repository name for context
        
        Returns:
            dict with suggestions and analysis
        """
        # Build the prompt
        prompt = self._build_review_prompt(changes, patterns, repo_name)
        
        # Call appropriate AI provider
        if self.provider == 'openai':
            response = self._call_openai(prompt)
        elif self.provider == 'anthropic':
            response = self._call_anthropic(prompt)
        elif self.provider == 'custom':
            response = self._call_custom(prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        # Parse response into structured suggestions
        return self._parse_response(response, changes)
    
    def _build_review_prompt(self, changes: list, patterns: dict, repo_name: str) -> str:
        """Build the review prompt with context"""
        prompt_parts = []
        
        # System context
        prompt_parts.append("You are an expert code reviewer focused on simplification and maintainability.")
        prompt_parts.append(f"You are reviewing code for the repository: {repo_name}\n")
        
        # Codebase patterns context
        if patterns and patterns.get('total_files_analyzed', 0) > 0:
            prompt_parts.append("=== CODEBASE PATTERNS & CONVENTIONS ===")
            
            # Naming conventions
            if patterns.get('naming_conventions'):
                prompt_parts.append("\nNaming Conventions:")
                for lang, conventions in patterns['naming_conventions'].items():
                    prompt_parts.append(f"  {lang}:")
                    for conv_type, styles in conventions.items():
                        if styles:
                            most_common = max(styles.items(), key=lambda x: x[1])
                            prompt_parts.append(f"    {conv_type}: {most_common[0]}")
            
            # Common libraries
            if patterns.get('common_libraries'):
                prompt_parts.append("\nCommon Libraries Used:")
                for lib, count in list(patterns['common_libraries'].items())[:5]:
                    prompt_parts.append(f"  - {lib}")
            
            # Code style
            if patterns.get('code_style'):
                prompt_parts.append("\nCode Style:")
                for lang, style in patterns['code_style'].items():
                    if style.get('indent_style'):
                        most_common = max(style['indent_style'].items(), key=lambda x: x[1])
                        prompt_parts.append(f"  {lang} indentation: {most_common[0]}")
        
        prompt_parts.append("\n" + "="*50 + "\n")
        
        # Instructions
        prompt_parts.append("Review the following code changes and provide suggestions to:")
        prompt_parts.append("1. Simplify complex code")
        prompt_parts.append("2. Align with existing codebase patterns and conventions")
        prompt_parts.append("3. Reduce code duplication")
        prompt_parts.append("4. Improve readability and maintainability")
        prompt_parts.append("5. Suggest more idiomatic approaches\n")
        
        prompt_parts.append("For each suggestion, provide:")
        prompt_parts.append("- File path and line number")
        prompt_parts.append("- Clear explanation of the issue")
        prompt_parts.append("- Concrete code example of the improvement")
        prompt_parts.append("- Priority level (HIGH, MEDIUM, LOW)\n")
        
        # Code changes
        prompt_parts.append("=== CODE CHANGES TO REVIEW ===\n")
        
        for i, change in enumerate(changes, 1):
            prompt_parts.append(f"Change {i}:")
            prompt_parts.append(f"File: {change['filename']}")
            prompt_parts.append(f"Starting at line: {change['start_line']}")
            
            if change.get('hunk_header'):
                prompt_parts.append(f"Context: {change['hunk_header']}")
            
            prompt_parts.append("\nCode:")
            for addition in change['additions']:
                if addition.get('context_before'):
                    prompt_parts.append("  Context:")
                    for ctx in addition['context_before'][-2:]:
                        prompt_parts.append(f"    {ctx}")
                
                prompt_parts.append(f"  + {addition['content']}")
                
                if addition.get('context_after'):
                    for ctx in addition['context_after'][:2]:
                        prompt_parts.append(f"    {ctx}")
            
            prompt_parts.append("\n" + "-"*40 + "\n")
        
        prompt_parts.append("\nProvide your review in JSON format with this structure:")
        prompt_parts.append('''{
  "summary": "Brief overall assessment",
  "suggestions": [
    {
      "file": "path/to/file.py",
      "line": 42,
      "priority": "HIGH|MEDIUM|LOW",
      "issue": "Description of the issue",
      "suggestion": "How to improve it",
      "code_example": "Suggested code"
    }
  ],
  "positive_aspects": ["Things done well"]
}''')
        
        return '\n'.join(prompt_parts)
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=Config.OPENAI_API_KEY,
                base_url=Config.OPENAI_BASE_URL
            )
            
            response = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer focused on code simplification and maintainability."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return self._generate_fallback_response()
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            
            response = client.messages.create(
                model=Config.ANTHROPIC_MODEL,
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            print(f"Error calling Anthropic: {e}")
            return self._generate_fallback_response()
    
    def _call_custom(self, prompt: str) -> str:
        """Call custom AI endpoint (OpenAI-compatible)"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {Config.CUSTOM_AI_API_KEY}"
            }
            
            data = {
                "model": Config.CUSTOM_AI_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an expert code reviewer."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(
                Config.CUSTOM_AI_ENDPOINT,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"Custom API error: {response.status_code}")
                return self._generate_fallback_response()
        except Exception as e:
            print(f"Error calling custom endpoint: {e}")
            return self._generate_fallback_response()
    
    def _parse_response(self, response: str, changes: list) -> dict:
        """Parse AI response into structured format"""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return result
            else:
                # Fallback: create structured response from text
                return {
                    'summary': 'Review completed',
                    'suggestions': [],
                    'raw_response': response
                }
        except json.JSONDecodeError:
            return {
                'summary': 'Review completed',
                'suggestions': [],
                'raw_response': response
            }
    
    def _generate_fallback_response(self) -> str:
        """Generate fallback response when AI call fails"""
        return json.dumps({
            'summary': 'Code review could not be completed due to AI service error.',
            'suggestions': [],
            'positive_aspects': []
        })
    
    def format_review_comment(self, review_result: dict) -> str:
        """Format review result as GitHub comment"""
        lines = []
        lines.append("## 🤖 AI Code Review - Simplification Suggestions\n")
        
        if review_result.get('summary'):
            lines.append(f"**Summary:** {review_result['summary']}\n")
        
        suggestions = review_result.get('suggestions', [])
        
        if suggestions:
            # Group by priority
            high_priority = [s for s in suggestions if s.get('priority') == 'HIGH']
            medium_priority = [s for s in suggestions if s.get('priority') == 'MEDIUM']
            low_priority = [s for s in suggestions if s.get('priority') == 'LOW']
            
            if high_priority:
                lines.append("### 🔴 High Priority\n")
                for sug in high_priority:
                    lines.append(self._format_suggestion(sug))
            
            if medium_priority:
                lines.append("### 🟡 Medium Priority\n")
                for sug in medium_priority:
                    lines.append(self._format_suggestion(sug))
            
            if low_priority:
                lines.append("### 🟢 Low Priority\n")
                for sug in low_priority:
                    lines.append(self._format_suggestion(sug))
        else:
            lines.append("✅ No major simplification suggestions. Code looks good!\n")
        
        if review_result.get('positive_aspects'):
            lines.append("\n### ✨ Positive Aspects\n")
            for aspect in review_result['positive_aspects']:
                lines.append(f"- {aspect}")
        
        lines.append("\n---")
        lines.append("*Powered by AI Code Review Bot*")
        
        return '\n'.join(lines)
    
    def _format_suggestion(self, suggestion: dict) -> str:
        """Format a single suggestion"""
        lines = []
        lines.append(f"**📁 `{suggestion.get('file', 'unknown')}` (Line {suggestion.get('line', '?')})**")
        lines.append(f"\n{suggestion.get('issue', 'No description')}")
        lines.append(f"\n💡 **Suggestion:** {suggestion.get('suggestion', 'No suggestion')}")
        
        if suggestion.get('code_example'):
            lines.append("\n```")
            lines.append(suggestion['code_example'])
            lines.append("```")
        
        lines.append("\n")
        return '\n'.join(lines)
