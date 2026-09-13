import re
from typing import List, Dict, Tuple

class DiffParser:
    """Parse and analyze Git diff files"""
    
    def __init__(self):
        self.file_pattern = re.compile(r'^diff --git a/(.*) b/(.*)$')
        self.hunk_pattern = re.compile(r'^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@(.*)$')
    
    def parse_diff(self, diff_text: str) -> List[Dict]:
        """
        Parse a unified diff into structured data
        Returns list of file changes with hunks and lines
        """
        if not diff_text:
            return []
        
        files = []
        current_file = None
        current_hunk = None
        
        lines = diff_text.split('\n')
        
        for line in lines:
            # New file
            file_match = self.file_pattern.match(line)
            if file_match:
                if current_file:
                    files.append(current_file)
                
                current_file = {
                    'filename': file_match.group(2),
                    'old_filename': file_match.group(1),
                    'hunks': [],
                    'additions': 0,
                    'deletions': 0
                }
                current_hunk = None
                continue
            
            # New hunk
            hunk_match = self.hunk_pattern.match(line)
            if hunk_match and current_file:
                if current_hunk:
                    current_file['hunks'].append(current_hunk)
                
                current_hunk = {
                    'old_start': int(hunk_match.group(1)),
                    'old_lines': int(hunk_match.group(2)) if hunk_match.group(2) else 1,
                    'new_start': int(hunk_match.group(3)),
                    'new_lines': int(hunk_match.group(4)) if hunk_match.group(4) else 1,
                    'header': hunk_match.group(5).strip(),
                    'lines': []
                }
                continue
            
            # Hunk content
            if current_hunk is not None and current_file:
                if line.startswith('+') and not line.startswith('+++'):
                    current_hunk['lines'].append({
                        'type': 'addition',
                        'content': line[1:],
                        'line_number': current_hunk['new_start'] + len([l for l in current_hunk['lines'] if l['type'] in ['addition', 'context']])
                    })
                    current_file['additions'] += 1
                elif line.startswith('-') and not line.startswith('---'):
                    current_hunk['lines'].append({
                        'type': 'deletion',
                        'content': line[1:],
                        'line_number': current_hunk['old_start'] + len([l for l in current_hunk['lines'] if l['type'] in ['deletion', 'context']])
                    })
                    current_file['deletions'] += 1
                elif line.startswith(' '):
                    current_hunk['lines'].append({
                        'type': 'context',
                        'content': line[1:],
                        'line_number': current_hunk['new_start'] + len([l for l in current_hunk['lines'] if l['type'] in ['addition', 'context']])
                    })
        
        # Add last hunk and file
        if current_hunk and current_file:
            current_file['hunks'].append(current_hunk)
        if current_file:
            files.append(current_file)
        
        return files
    
    def extract_changed_code(self, parsed_diff: List[Dict]) -> List[Dict]:
        """
        Extract only the changed code sections with context
        Returns list of changes with filename, line numbers, and code
        """
        changes = []
        
        for file in parsed_diff:
            for hunk in file['hunks']:
                # Get additions with context
                additions = []
                context_before = []
                context_after = []
                
                for i, line in enumerate(hunk['lines']):
                    if line['type'] == 'addition':
                        # Get context before (up to 3 lines)
                        start_idx = max(0, i - 3)
                        context_before = [l for l in hunk['lines'][start_idx:i] if l['type'] == 'context']
                        
                        # Get context after (up to 3 lines)
                        end_idx = min(len(hunk['lines']), i + 4)
                        context_after = [l for l in hunk['lines'][i+1:end_idx] if l['type'] == 'context']
                        
                        additions.append({
                            'line_number': line['line_number'],
                            'content': line['content'],
                            'context_before': [l['content'] for l in context_before],
                            'context_after': [l['content'] for l in context_after]
                        })
                
                if additions:
                    changes.append({
                        'filename': file['filename'],
                        'hunk_header': hunk['header'],
                        'additions': additions,
                        'start_line': hunk['new_start'],
                        'total_additions': file['additions'],
                        'total_deletions': file['deletions']
                    })
        
        return changes
    
    def get_file_extension(self, filename: str) -> str:
        """Get file extension"""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return ''
    
    def get_language(self, filename: str) -> str:
        """Determine programming language from filename"""
        ext_map = {
            'py': 'Python',
            'js': 'JavaScript',
            'jsx': 'JavaScript React',
            'ts': 'TypeScript',
            'tsx': 'TypeScript React',
            'java': 'Java',
            'go': 'Go',
            'rb': 'Ruby',
            'php': 'PHP',
            'cs': 'C#',
            'cpp': 'C++',
            'c': 'C',
            'h': 'C/C++ Header',
            'rs': 'Rust',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'scala': 'Scala',
            'html': 'HTML',
            'css': 'CSS',
            'sql': 'SQL'
        }
        
        ext = self.get_file_extension(filename)
        return ext_map.get(ext, 'Unknown')
    
    def format_change_for_review(self, change: Dict) -> str:
        """Format a change into human-readable text for AI review"""
        output = []
        output.append(f"File: {change['filename']} ({self.get_language(change['filename'])})")
        output.append(f"Location: Line {change['start_line']}")
        
        if change['hunk_header']:
            output.append(f"Context: {change['hunk_header']}")
        
        output.append("\nChanged Code:")
        
        for addition in change['additions']:
            if addition['context_before']:
                output.append("\n  Context before:")
                for ctx in addition['context_before']:
                    output.append(f"    {ctx}")
            
            output.append(f"\n  + [Line {addition['line_number']}] {addition['content']}")
            
            if addition['context_after']:
                output.append("\n  Context after:")
                for ctx in addition['context_after']:
                    output.append(f"    {ctx}")
        
        return '\n'.join(output)
    
    def summarize_diff(self, parsed_diff: List[Dict]) -> Dict:
        """Generate summary statistics of the diff"""
        total_files = len(parsed_diff)
        total_additions = sum(f['additions'] for f in parsed_diff)
        total_deletions = sum(f['deletions'] for f in parsed_diff)
        
        languages = {}
        for file in parsed_diff:
            lang = self.get_language(file['filename'])
            languages[lang] = languages.get(lang, 0) + 1
        
        return {
            'total_files': total_files,
            'total_additions': total_additions,
            'total_deletions': total_deletions,
            'languages': languages,
            'files': [f['filename'] for f in parsed_diff]
        }
