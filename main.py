"""
FastAPI application with AI agentic chat capabilities.
Supports web search and page reading tools for enhanced responses.
"""

import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
from openai import OpenAI
from pydantic import BaseModel

# ============================================================================
# Configuration & Setup
# ============================================================================

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize FastAPI app
app = FastAPI(title="AI Architect Chat API", version="1.0.0")

# Serve static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Serve output directory for TTS audio files
output_path = Path(__file__).parent / "output"
output_path.mkdir(exist_ok=True)

# Initialize OpenAI client
# Support both AI_BUILDER_TOKEN (injected by platform) and SUPER_MIND_API_KEY (for local dev)
api_key = os.getenv("AI_BUILDER_TOKEN") or os.getenv("SUPER_MIND_API_KEY")
client = OpenAI(
    api_key=api_key,
    base_url="https://space.ai-builders.com/backend/v1"
)

# Initialize TTS (lazy loading)
_tts_instance = None
_tts_lock = False

def get_tts_instance():
    """Get or initialize TTS instance (singleton pattern)"""
    global _tts_instance, _tts_lock
    
    if _tts_instance is None and not _tts_lock:
        _tts_lock = True
        original_cwd = os.getcwd()  # Store original cwd before any operations
        try:
            # Get TTS base path from environment, default to project root
            tts_base_path = os.getenv("TTS_BASE_PATH")
            if not tts_base_path:
                # Default to project root (where main.py is located)
                tts_base_path = str(Path(__file__).parent)
                # Set it in environment for this process
                os.environ["TTS_BASE_PATH"] = tts_base_path
            
            # Add TTS module to path - need both tts_dir and GPT_SoVITS for relative imports
            tts_dir = Path(tts_base_path) / "tts-feature-architecture"
            if tts_dir.exists():
                # Change to tts_dir so that os.getcwd() in sv.py works correctly
                try:
                    os.chdir(str(tts_dir))
                    
                    # Add both the tts-feature-architecture directory and GPT_SoVITS subdirectory
                    sys.path.insert(0, str(tts_dir))
                    gpt_sovits_dir = tts_dir / "GPT_SoVITS"
                    if gpt_sovits_dir.exists():
                        sys.path.insert(0, str(gpt_sovits_dir))
                        # Also add eres2net directory for relative imports
                        eres2net_dir = gpt_sovits_dir / "eres2net"
                        if eres2net_dir.exists():
                            sys.path.insert(0, str(eres2net_dir))
                    
                    from inference import ChineseTTS
                    import torch
                    
                    # TTS configuration paths
                    gpt_path = tts_dir / "models" / "gpt_weights.ckpt"
                    sovits_path = tts_dir / "models" / "sovits_weights.pth"
                    ref_audio_path = tts_dir / "reference.wav"
                    prompt_semantic_cache = tts_dir / "reference_semantic.pt"
                    
                    if not gpt_path.exists() or not sovits_path.exists() or not ref_audio_path.exists():
                        logger.warning("TTS models not found. TTS functionality will be disabled.")
                        _tts_instance = None
                        _tts_lock = False
                        os.chdir(original_cwd)
                        return None
                    
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    logger.info(f"Initializing TTS on device: {device}")
                    
                    _tts_instance = ChineseTTS(
                        gpt_path=str(gpt_path),
                        sovits_path=str(sovits_path),
                        device=device,
                        is_half=(device == "cuda"),
                        version="v2ProPlus"
                    )
                    
                    # Set reference audio
                    if prompt_semantic_cache.exists():
                        logger.info("Loading cached prompt_semantic...")
                        _tts_instance.set_reference(
                            prompt_semantic=str(prompt_semantic_cache),
                            ref_audio_path=str(ref_audio_path)
                        )
                    else:
                        logger.info("Extracting prompt_semantic from reference audio...")
                        _tts_instance.set_reference(
                            prompt_semantic=None,
                            ref_audio_path=str(ref_audio_path)
                        )
                        # Cache prompt_semantic for next time
                        if "prompt_semantic" in _tts_instance.tts.prompt_cache:
                            prompt_semantic = _tts_instance.tts.prompt_cache["prompt_semantic"]
                            if isinstance(prompt_semantic, torch.Tensor):
                                prompt_semantic_cpu = prompt_semantic.cpu()
                            else:
                                prompt_semantic_cpu = prompt_semantic
                            torch.save(prompt_semantic_cpu, str(prompt_semantic_cache))
                            logger.info(f"Saved prompt_semantic to {prompt_semantic_cache}")
                    
                    logger.info("TTS initialized successfully")
                finally:
                    # Restore original working directory
                    os.chdir(original_cwd)
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            import traceback
            logger.error(traceback.format_exc())
            _tts_instance = None
            # Make sure to restore cwd even on error
            try:
                os.chdir(original_cwd)
            except:
                pass
        finally:
            _tts_lock = False
    
    return _tts_instance


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    user_message: str


class ToolCallRequest(BaseModel):
    """Request model for tool calling endpoint (alias for ChatRequest)."""
    user_message: str


class DebugRequest(BaseModel):
    """Request model for debug endpoint."""
    user_message: str
    include_tool_calls: bool = True


class TTSRequest(BaseModel):
    """Request model for TTS endpoint."""
    text: str


# ============================================================================
# Tool Functions
# ============================================================================

def web_search(query: str) -> Dict[str, Any]:
    """
    Search the web using the internal search API.
    
    Args:
        query: The search query string
        
    Returns:
        Dictionary containing search results
    """
    # Support both AI_BUILDER_TOKEN (injected by platform) and SUPER_MIND_API_KEY (for local dev)
    api_key = os.getenv("AI_BUILDER_TOKEN") or os.getenv("SUPER_MIND_API_KEY")
    search_url = "https://space.ai-builders.com/backend/v1/search/"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "keywords": [query],
        "max_results": 3
    }
    
    try:
        with httpx.Client() as http_client:
            response = http_client.post(search_url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        # Handle HTTP errors (like 502 Bad Gateway)
        status_code = e.response.status_code
        error_msg = f"Search API returned error {status_code}: {e.response.text[:200] if e.response.text else 'No error details'}"
        
        # Provide clear feedback for common errors
        if status_code == 502:
            return {
                "error": "Search service temporarily unavailable (502 Bad Gateway). The search API backend is down or experiencing issues. Please inform the user that you cannot perform web searches at this time and suggest they try again later, or use the read_page tool with a direct URL if they have one.",
                "status_code": status_code,
                "service_unavailable": True
            }
        elif status_code == 401:
            return {
                "error": "Search API authentication failed (401 Unauthorized). API key may be invalid or missing.",
                "status_code": status_code,
                "service_unavailable": False
            }
        else:
            return {
                "error": error_msg,
                "status_code": status_code,
                "service_unavailable": status_code >= 500
            }
    except httpx.TimeoutException:
        return {
            "error": "Search request timed out after 30 seconds. The search service may be slow or unavailable. Please inform the user and suggest trying again later.",
            "service_unavailable": True
        }
    except httpx.RequestError as e:
        return {
            "error": f"Network error connecting to search API: {str(e)}. The search service may be unreachable.",
            "service_unavailable": True
        }
    except Exception as e:
        return {
            "error": f"Unexpected error during search: {str(e)}",
            "service_unavailable": False
        }


def read_page(url: str) -> Dict[str, Any]:
    """
    Fetch a webpage and extract the main text content from HTML.
    Strips HTML tags, scripts, and styles.
    
    Args:
        url: The URL of the webpage to read
        
    Returns:
        Dictionary containing the extracted text content
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=30.0) as http_client:
            # Set a user agent to avoid being blocked
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = http_client.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "meta", "link", "noscript"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up excessive whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # For release notes/changelogs, try to prioritize breaking change sections
            # Check if this looks like a release notes page
            text_lower = text.lower()
            is_release_notes = any(keyword in text_lower for keyword in [
                "breaking change", "breaking", "deprecated", "changelog", 
                "release notes", "what's new", "migration"
            ])
            
            if is_release_notes and len(text) > 20000:
                # Try to find and prioritize breaking change sections
                # Split by common section markers
                sections = []
                current_section = ""
                
                # Look for sections containing breaking changes
                breaking_keywords = ["breaking change", "breaking", "deprecated", "removed", "migration"]
                for line in text.split('\n'):
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in breaking_keywords):
                        # This is a breaking change section - prioritize it
                        sections.insert(0, line)  # Add to beginning
                    else:
                        current_section += line + "\n"
                
                # Combine: breaking sections first, then rest
                if sections:
                    prioritized_text = "\n".join(sections) + "\n\n" + current_section
                    text = prioritized_text
            
            # Limit text length to avoid token limits (keep first 25000 characters for better context)
            if len(text) > 25000:
                text = text[:25000] + "... [content truncated - showing first 25000 characters]"
            
            return {
                "url": url,
                "title": soup.title.string if soup.title else "No title",
                "content": text
            }
    except httpx.HTTPError as e:
        return {"error": f"HTTP error: {str(e)}", "url": url}
    except Exception as e:
        return {"error": f"Error reading page: {str(e)}", "url": url}


# ============================================================================
# Tool Schemas (OpenAI Function Calling Format)
# ============================================================================

WEB_SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current information, news, facts, or any query. Use this tool when you need to find up-to-date information that you might not know. After getting search results, use read_page to read specific pages if needed. IMPORTANT: If the tool returns an error indicating the service is unavailable (like 502 Bad Gateway), do NOT retry the search tool multiple times. Instead, inform the user that the search service is temporarily unavailable and suggest alternatives like using read_page with a direct URL if available.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string to look up on the web (be specific, e.g., 'LangChain latest version PyPI' or 'LangChain release notes')"
                }
            },
            "required": ["query"]
        }
    }
}

READ_PAGE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_page",
        "description": "Read and extract the main text content from a webpage. Use this tool when you have a URL and need to read its content, such as documentation, articles, changelogs, or release notes. IMPORTANT: When looking for breaking changes, carefully read through the content and look for sections marked as 'Breaking Changes', 'BREAKING', 'Deprecated', 'Migration Guide', or similar. Extract specific details about what changed and how it affects users. After reading, analyze the content thoroughly and provide a detailed final answer to the user with specific breaking change information if found. Do not call this tool repeatedly on the same URL unless you need to verify information.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL of the webpage to read (must be a complete URL starting with http:// or https://). For release notes, prefer official GitHub releases or changelog pages."
                }
            },
            "required": ["url"]
        }
    }
}


# ============================================================================
# Helper Functions for Agent Loop
# ============================================================================

def execute_tool(function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool function based on its name and arguments.
    
    Args:
        function_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool
        
    Returns:
        Dictionary containing the tool execution result
    """
    if function_name == "web_search":
        query = arguments.get("query", "")
        logger.info(f"[System] Executing web_search with query: '{query}'")
        return web_search(query)
    elif function_name == "read_page":
        url = arguments.get("url", "")
        logger.info(f"[System] Executing read_page with URL: '{url}'")
        return read_page(url)
    else:
        logger.error(f"[System] Unknown tool: '{function_name}'")
        return {"error": f"Unknown tool: {function_name}"}


def format_tool_result_for_llm(tool_result: Dict[str, Any], function_name: str) -> str:
    """
    Format tool result for LLM consumption.
    
    Args:
        tool_result: Raw tool execution result
        function_name: Name of the tool that produced the result
        
    Returns:
        JSON string formatted for LLM
    """
    # Special formatting for read_page results
    if function_name == "read_page" and "content" in tool_result:
        formatted_result = {
            "url": tool_result.get("url", ""),
            "title": tool_result.get("title", ""),
            "content": tool_result.get("content", "")
        }
        tool_content = json.dumps(formatted_result, ensure_ascii=False)
    else:
        tool_content = json.dumps(tool_result, ensure_ascii=False)
    
    # Limit content size to avoid token limits
    if len(tool_content) > 15000:
        tool_content = tool_content[:15000] + "... [tool result truncated]"
    
    return tool_content


def log_tool_result(tool_result: Dict[str, Any], function_name: str) -> None:
    """
    Log tool execution result (truncated for readability).
    
    Args:
        tool_result: Tool execution result
        function_name: Name of the tool
    """
    if function_name == "read_page" and "content" in tool_result:
        log_result = tool_result.copy()
        if len(tool_result["content"]) > 200:
            log_result["content"] = tool_result["content"][:200] + "..."
        result_str = json.dumps(log_result, ensure_ascii=False)
    else:
        result_str = json.dumps(tool_result, ensure_ascii=False)
    
    if len(result_str) > 200:
        result_str = result_str[:200] + "..."
    logger.info(f"[System] Tool Output: '{result_str}'")


def run_agent_loop(
    user_message: str,
    max_turns: int = 8,
    debug_mode: bool = False
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Run the agentic loop with tool calling support.
    
    Args:
        user_message: User's input message
        max_turns: Maximum number of agent turns
        debug_mode: If True, return debug information
        
    Returns:
        Tuple of (final_response, debug_info)
        debug_info is None if debug_mode is False
    """
    messages = [{"role": "user", "content": user_message}]
    debug_info = {
        "turns": [],
        "final_response": None,
        "total_turns": 0
    } if debug_mode else None
    
    for turn in range(max_turns):
        logger.info(f"[Agent] Turn {turn + 1}/{max_turns}")
        
        # Prepare turn info for debug mode
        turn_info = None
        if debug_mode:
            turn_info = {
                "turn_number": turn + 1,
                "llm_input": messages.copy(),
                "tool_calls": [],
                "tool_results": [],
                "llm_response": None
            }
        
        # Call LLM with tools
        response = client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            tools=[WEB_SEARCH_TOOL_SCHEMA, READ_PAGE_TOOL_SCHEMA],
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Build assistant message
        assistant_msg = {
            "role": "assistant",
            "content": message.content
        }
        
        # Add tool calls if present
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
            
            # Store tool calls for debug
            if debug_mode and turn_info:
                for tool_call in message.tool_calls:
                    turn_info["tool_calls"].append({
                        "function": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    })
        
        # Store LLM response for debug
        if debug_mode and turn_info:
            turn_info["llm_response"] = {
                "content": message.content,
                "has_tool_calls": bool(message.tool_calls)
            }
        
        messages.append(assistant_msg)
        
        # Execute tools if requested
        if message.tool_calls:
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                logger.info(f"[Agent] Decided to call tool: '{function_name}'")
                
                # Parse tool arguments
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    logger.error(f"[System] Failed to parse tool arguments: {tool_call.function.arguments}")
                    tool_result = {"error": "Invalid JSON in tool arguments"}
                else:
                    # Execute the tool
                    tool_result = execute_tool(function_name, arguments)
                    log_tool_result(tool_result, function_name)
                    
                    # Store tool result for debug
                    if debug_mode and turn_info:
                        tool_result_summary = tool_result.copy()
                        if "content" in tool_result_summary:
                            content_str = str(tool_result_summary["content"])
                            if len(content_str) > 500:
                                tool_result_summary["content"] = content_str[:500] + "... [truncated]"
                        turn_info["tool_results"].append({
                            "function": function_name,
                            "result_summary": tool_result_summary
                        })
                
                # Format and add tool result to conversation
                tool_content = format_tool_result_for_llm(tool_result, function_name)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_content
                })
        else:
            # No tool calls - we have the final answer
            final_answer = message.content or "No response generated"
            logger.info(f"[Agent] Final Answer: '{final_answer[:200]}...'")
            
            if debug_mode:
                debug_info["final_response"] = final_answer
                debug_info["total_turns"] = turn + 1
            
            return final_answer, debug_info
        
        # Store turn info for debug
        if debug_mode and turn_info:
            debug_info["turns"].append(turn_info)
    
    # Max turns reached - find last assistant message with content
    final_answer = "Maximum turns reached. The agent may need more turns to complete this query."
    for msg in reversed(messages):
        if msg.get("role") == "assistant" and msg.get("content"):
            content = msg["content"]
            if content and content.strip():
                final_answer = content
                break
    
    logger.warning(f"[Agent] Max turns ({max_turns}) reached.")
    logger.info(f"[Agent] Final Answer (max turns reached): '{final_answer[:200]}...'")
    
    if debug_mode:
        debug_info["final_response"] = final_answer
        debug_info["total_turns"] = max_turns
    
    return final_answer, debug_info


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Serve the chat web application."""
    index_path = Path(__file__).parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Hello, World! Please create the static/index.html file."}


@app.get("/api/hello")
async def hello_world(input: str = "World"):
    """Health check endpoint."""
    return {"message": f"Hello, World {input}"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint with agentic loop and tool calling support.
    
    The agent can use web_search and read_page tools to enhance responses.
    Supports up to 8 turns of tool calling before returning a final answer.
    """
    final_answer, _ = run_agent_loop(request.user_message, max_turns=8, debug_mode=False)
    return {"response": final_answer}


@app.post("/chat-debug")
async def chat_debug(request: DebugRequest):
    """
    Debug endpoint that returns detailed information about agent execution.
    
    Shows all tool calls, tool results, and intermediate steps for debugging.
    Useful for understanding how the agent processes queries.
    """
    # Enhance user message for breaking change queries
    user_message = request.user_message
    if "breaking change" in user_message.lower():
        user_message += (
            "\n\nIMPORTANT: If the query asks for breaking changes, prioritize finding "
            "and reporting those over new features. Look specifically for sections marked "
            "as 'Breaking Changes', 'BREAKING', 'Deprecated', 'Removed', or 'Migration Guide' "
            "in the release notes."
        )
    
    final_answer, debug_info = run_agent_loop(user_message, max_turns=8, debug_mode=True)
    
    return {
        "response": final_answer,
        "debug": debug_info if request.include_tool_calls else None
    }


@app.post("/chat-with-tools")
async def chat_with_tools(request: ToolCallRequest):
    """
    Chat endpoint with tool calling (alias for /chat).
    
    Same functionality as /chat endpoint. Maintained for backward compatibility.
    """
    final_answer, _ = run_agent_loop(request.user_message, max_turns=8, debug_mode=False)
    return {"response": final_answer}


@app.post("/api/tts/generate")
async def generate_tts(request: TTSRequest):
    """
    Generate audio from Chinese text using TTS.
    
    Args:
        request: TTSRequest containing Chinese text to synthesize
        
    Returns:
        JSON response with audio file path and metadata
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    tts = get_tts_instance()
    if tts is None:
        raise HTTPException(status_code=503, detail="TTS service not available. Models may not be loaded.")
    
    try:
        # Create output directory if it doesn't exist
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        audio_filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
        output_path = output_dir / audio_filename
        
        logger.info(f"Generating TTS audio for text: {request.text[:50]}...")
        
        # Generate audio (this is a blocking call, but we'll add status updates)
        # Note: The actual TTS synthesis happens synchronously, so we can't stream
        # intermediate updates easily. We'll simulate progress updates.
        audio, sample_rate = tts.synthesize(
            text=request.text.strip(),
            prompt_text=None,
            output_path=str(output_path),
            top_k=20,
            top_p=0.6,
            temperature=0.8,
            speed=1.0
        )
        
        duration = len(audio) / sample_rate
        
        logger.info(f"TTS audio generated: {audio_filename} ({duration:.2f}s)")
        
        return JSONResponse({
            "success": True,
            "audio_url": f"/api/tts/audio/{audio_filename}",
            "filename": audio_filename,
            "duration": round(duration, 2),
            "sample_rate": sample_rate,
            "text": request.text
        })
        
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")


@app.get("/api/tts/audio/{filename}")
async def get_tts_audio(filename: str):
    """
    Serve generated TTS audio files.
    
    Args:
        filename: Name of the audio file to serve
        
    Returns:
        Audio file response
    """
    output_dir = Path(__file__).parent / "output"
    audio_path = output_dir / filename
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Security check: ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    return FileResponse(
        path=str(audio_path),
        media_type="audio/wav",
        filename=filename
    )
