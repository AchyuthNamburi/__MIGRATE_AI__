# backend/agents/repair_agent.py
from langchain.prompts import ChatPromptTemplate
import re

class RepairAgent:
    def __init__(self):
        self.llm = ChatGroq(model="llama-3.3-70b-versatile")
        self.repair_attempts = 0
        self.max_attempts = 5
        self.repair_history = []
    
    async def analyze_failures(self, verification_results: Dict) -> List[Dict]:
        """Analyze verification failures"""
        failures = []
        
        # Parse build failures
        if not verification_results['build']['success']:
            failures.extend(self.parse_errors(verification_results['build']['error']))
        
        # Parse test failures
        if verification_results['tests']['failed'] > 0:
            failures.extend(self.parse_test_failures(verification_results['tests']))
        
        return failures
    
    async def generate_fixes(self, failures: List[Dict]) -> List[Dict]:
        """Generate fixes for failures"""
        fixes = []
        
        for failure in failures:
            # Use LLM to generate fix
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a code migration repair expert"),
                ("user", "Fix this error: {error}\n\nContext: {context}")
            ])
            
            chain = prompt | self.llm
            fix = await chain.ainvoke({
                "error": failure['message'],
                "context": failure.get('context', '')
            })
            
            fixes.append({
                "failure": failure,
                "fix": fix,
                "confidence": self.assess_confidence(fix)
            })
        
        return fixes
    
    async def apply_fixes(self, repo_path: str, fixes: List[Dict]) -> bool:
        """Apply fixes to repository"""
        applied = 0
        for fix in fixes:
            if fix['confidence'] > 0.7:
                success = await self.apply_fix(repo_path, fix)
                if success:
                    applied += 1
        
        return applied > 0
    
    def assess_confidence(self, fix: str) -> float:
        """Assess confidence in fix"""
        # Heuristic confidence scoring
        confidence = 0.5
        
        # Check if fix has complete code
        if '```' in fix:
            confidence += 0.2
        
        # Check if fix includes imports
        if 'import' in fix or 'require' in fix:
            confidence += 0.1
        
        # Check if fix is specific
        if len(fix.split()) > 20:
            confidence += 0.1
        
        return min(confidence, 1.0)