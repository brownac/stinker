import re
from typing import List, Dict
from collections import Counter
from kiss.github_client import GitHubClient
from kiss.config import Config

class PatternAnalyzer:
    """Analyze codebase to learn patterns and conventions"""
    
    def __init__(self, github_client: GitHubClient):
        self.github_client = github_client
    
    def analyze_repository(self, repo_full_name: str, max_files: int = None) -> Dict:
        """
        Analyze repository to extract coding patterns
        Returns dict of discovered patterns
        """
        max_files = max_files or Config.PATTERN_ANALYSIS_DEPTH
        
        # Get repository files
        default_branch = self.github_client.get_default_branch(repo_full_name)
        files = self.github_client.list_repository_files(
            repo_full_name, 
            ref=default_branch, 
            max_files=max_files
        )
        
        patterns = {
            'naming_conventions': {},
            'import_patterns': {},
            'function_patterns': {},
            'class_patterns': {},
            'code_style': {},
            'common_libraries': Counter(),
            'file_structure': {},
            'total_files_analyzed': 0
        }
        
        for file_info in files[:max_files]:
            content = self.github_client.get_file_content(
                repo_full_name, 
                file_info['path'], 
                ref=default_branch
            )
            
            if content:
                self._analyze_file(content, file_info['path'], patterns)
                patterns['total_files_analyzed'] += 1
        
        # Convert Counters to dicts for JSON serialization
        patterns['common_libraries'] = dict(patterns['common_libraries'].most_common(20))
        
        return patterns
    
    def _analyze_file(self, content: str, filepath: str, patterns: Dict):
        """Analyze a single file for patterns"""
        lines = content.split('\n')
        
        # Detect language
        lang = self._get_language(filepath)
        
        if lang in ['Python', 'JavaScript', 'TypeScript', 'JavaScript React', 'TypeScript React']:
            self._analyze_naming(content, lang, patterns)
            self._analyze_imports(content, lang, patterns)
            self._analyze_functions(content, lang, patterns)
            self._analyze_classes(content, lang, patterns)
            self._analyze_style(content, lang, patterns)
    
    def _get_language(self, filepath: str) -> str:
        """Determine language from filepath"""
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript React',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript React'
        }
        
        for ext, lang in ext_map.items():
            if filepath.endswith(ext):
                return lang
        return 'Unknown'
    
    def _analyze_naming(self, content: str, lang: str, patterns: Dict):
        """Analyze naming conventions"""
        if lang not in patterns['naming_conventions']:
            patterns['naming_conventions'][lang] = {
                'variable_style': Counter(),
                'function_style': Counter(),
                'class_style': Counter()
            }
        
        # Variable names
        var_patterns = {
            'Python': r'\b([a-z_][a-z0-9_]*)\s*=',
            'JavaScript': r'(?:let|const|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
            'TypeScript': r'(?:let|const|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)'
        }
        
        if lang in var_patterns:
            variables = re.findall(var_patterns[lang], content)
            for var in variables:
                style = self._detect_naming_style(var)
                patterns['naming_conventions'][lang]['variable_style'][style] += 1
        
        # Function names
        func_patterns = {
            'Python': r'def\s+([a-z_][a-z0-9_]*)\s*\(',
            'JavaScript': r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(',
            'TypeScript': r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\('
        }
        
        if lang in func_patterns:
            functions = re.findall(func_patterns[lang], content)
            for func in functions:
                style = self._detect_naming_style(func)
                patterns['naming_conventions'][lang]['function_style'][style] += 1
        
        # Class names
        class_patterns = {
            'Python': r'class\s+([A-Z][a-zA-Z0-9]*)',
            'JavaScript': r'class\s+([A-Z][a-zA-Z0-9]*)',
            'TypeScript': r'class\s+([A-Z][a-zA-Z0-9]*)'
        }
        
        if lang in class_patterns:
            classes = re.findall(class_patterns[lang], content)
            for cls in classes:
                style = self._detect_naming_style(cls)
                patterns['naming_conventions'][lang]['class_style'][style] += 1
    
    def _detect_naming_style(self, name: str) -> str:
        """Detect naming style (snake_case, camelCase, PascalCase)"""
        if '_' in name and name.islower():
            return 'snake_case'
        elif name[0].isupper() and '_' not in name:
            return 'PascalCase'
        elif name[0].islower() and '_' not in name and any(c.isupper() for c in name):
            return 'camelCase'
        elif name.isupper():
            return 'SCREAMING_SNAKE_CASE'
        return 'other'
    
    def _analyze_imports(self, content: str, lang: str, patterns: Dict):
        """Analyze import patterns and common libraries"""
        import_patterns = {
            'Python': r'^(?:from\s+([\w.]+)\s+)?import\s+([\w., ]+)',
            'JavaScript': r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            'TypeScript': r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
        }
        
        if lang in import_patterns:
            matches = re.finditer(import_patterns[lang], content, re.MULTILINE)
            for match in matches:
                if lang == 'Python':
                    module = match.group(1) or match.group(2).split(',')[0].strip()
                    # Extract base library
                    base_lib = module.split('.')[0]
                    patterns['common_libraries'][base_lib] += 1
                else:
                    module = match.group(1)
                    # Extract package name
                    if not module.startswith('.'):
                        package = module.split('/')[0]
                        patterns['common_libraries'][package] += 1
    
    def _analyze_functions(self, content: str, lang: str, patterns: Dict):
        """Analyze function patterns"""
        if lang not in patterns['function_patterns']:
            patterns['function_patterns'][lang] = {
                'avg_lines': [],
                'has_docstrings': 0,
                'total_functions': 0
            }
        
        if lang == 'Python':
            # Find all function definitions
            func_pattern = r'def\s+\w+\([^)]*\):\s*\n((?:.*\n)*?)(?=\n(?:def|class|\Z))'
            functions = re.finditer(func_pattern, content, re.MULTILINE)
            
            for func in functions:
                func_body = func.group(1)
                lines = len([l for l in func_body.split('\n') if l.strip()])
                patterns['function_patterns'][lang]['avg_lines'].append(lines)
                patterns['function_patterns'][lang]['total_functions'] += 1
                
                # Check for docstring
                if '"""' in func_body[:100] or "'''" in func_body[:100]:
                    patterns['function_patterns'][lang]['has_docstrings'] += 1
    
    def _analyze_classes(self, content: str, lang: str, patterns: Dict):
        """Analyze class patterns"""
        if lang not in patterns['class_patterns']:
            patterns['class_patterns'][lang] = {
                'total_classes': 0,
                'has_docstrings': 0,
                'method_count': []
            }
        
        class_pattern = r'class\s+\w+.*?:'
        classes = re.finditer(class_pattern, content)
        
        for cls in classes:
            patterns['class_patterns'][lang]['total_classes'] += 1
    
    def _analyze_style(self, content: str, lang: str, patterns: Dict):
        """Analyze code style patterns"""
        if lang not in patterns['code_style']:
            patterns['code_style'][lang] = {
                'indent_style': Counter(),
                'quote_style': Counter(),
                'line_length': []
            }
        
        lines = content.split('\n')
        
        # Detect indentation
        for line in lines:
            if line and line[0] in [' ', '\t']:
                if line.startswith('    '):
                    patterns['code_style'][lang]['indent_style']['4_spaces'] += 1
                elif line.startswith('  '):
                    patterns['code_style'][lang]['indent_style']['2_spaces'] += 1
                elif line.startswith('\t'):
                    patterns['code_style'][lang]['indent_style']['tabs'] += 1
        
        # Detect quote style
        single_quotes = len(re.findall(r"'[^']*'", content))
        double_quotes = len(re.findall(r'"[^"]*"', content))
        
        patterns['code_style'][lang]['quote_style']['single'] += single_quotes
        patterns['code_style'][lang]['quote_style']['double'] += double_quotes
        
        # Line lengths (sample)
        for line in lines[:100]:
            if line.strip():
                patterns['code_style'][lang]['line_length'].append(len(line))
    
    def get_pattern_summary(self, patterns: Dict) -> str:
        """Generate human-readable summary of patterns"""
        summary = []
        summary.append(f"Analyzed {patterns['total_files_analyzed']} files\n")
        
        # Naming conventions
        summary.append("=== Naming Conventions ===")
        for lang, conventions in patterns['naming_conventions'].items():
            summary.append(f"\n{lang}:")
            for conv_type, styles in conventions.items():
                if isinstance(styles, Counter) and styles:
                    most_common = styles.most_common(1)[0]
                    summary.append(f"  {conv_type}: {most_common[0]} ({most_common[1]} occurrences)")
        
        # Common libraries
        if patterns['common_libraries']:
            summary.append("\n\n=== Most Used Libraries ===")
            for lib, count in list(patterns['common_libraries'].items())[:10]:
                summary.append(f"  {lib}: {count} imports")
        
        # Code style
        summary.append("\n\n=== Code Style ===")
        for lang, style in patterns['code_style'].items():
            summary.append(f"\n{lang}:")
            if style['indent_style']:
                most_common_indent = style['indent_style'].most_common(1)[0]
                summary.append(f"  Indentation: {most_common_indent[0]}")
            if style['quote_style']:
                most_common_quote = style['quote_style'].most_common(1)[0]
                quote_type = 'single quotes' if most_common_quote[0] == 'single' else 'double quotes'
                summary.append(f"  Quotes: {quote_type}")
        
        return '\n'.join(summary)
