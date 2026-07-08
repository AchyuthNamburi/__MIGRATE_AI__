# backend/tools/toolpipe_tool.py
"""ToolPipe - 238+ free developer tools API"""

import httpx
import json
from typing import Dict, Any, Optional


class ToolPipeTool:
    """
    ToolPipe provides 238+ free developer tools via REST API
    No API key required!
    """
    
    def __init__(self, base_url: str = "https://toolpipe.vercel.app/api"):
        self.base_url = base_url
        self.tools_used = []
    
    async def use_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a ToolPipe API endpoint"""
        self.tools_used.append({"tool": tool_name, "params": params})
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{tool_name}",
                    json=params,
                    timeout=30
                )
                response.raise_for_status()
                return {"success": True, "data": response.json()}
            except httpx.HTTPStatusError as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    async def validate_json(self, json_string: str) -> Dict:
        """Validate and format JSON"""
        return await self.use_tool("json-format", {"code": json_string})
    
    async def decode_jwt(self, token: str) -> Dict:
        """Decode a JWT token"""
        return await self.use_tool("jwt-decode", {"token": token})
    
    async def generate_qr(self, data: str) -> Dict:
        """Generate a QR code"""
        return await self.use_tool("qr-generate", {"data": data})
    
    async def validate_dns(self, domain: str) -> Dict:
        """Validate DNS records"""
        return await self.use_tool("dns-lookup", {"domain": domain})
    
    async def generate_hash(self, text: str, algorithm: str = "sha256") -> Dict:
        """Generate a hash of text"""
        return await self.use_tool("hash-generate", {
            "text": text,
            "algorithm": algorithm
        })
    
    async def format_sql(self, sql: str) -> Dict:
        """Format SQL code"""
        return await self.use_tool("sql-format", {"sql": sql})
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "total_tools_used": len(self.tools_used),
            "tools_used": self.tools_used
        }