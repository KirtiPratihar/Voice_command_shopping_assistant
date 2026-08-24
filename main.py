from __future__ import annotations
from fastapi.middleware.cors import CORSMiddleware
import random
import json
import os
import re
from collections.abc import MutableMapping
from typing import Any, Literal, TypedDict

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


APP_TITLE = "Voice Command Shopping Assistant"
APP_VERSION = "1.0.0"

app = FastAPI(title=APP_TITLE, version=APP_VERSION)
origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://voice-command-shopping-assistant-lyart.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from google import genai
except ImportError:  # pragma: no cover - optional dependency is installed via requirements.txt
    genai = None

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - optional dependency is installed via requirements.txt
    StateGraph = None
    END = None
    START = None

const [userId, setUserId] = useState<string>('');

useEffect(() => {
  let id = localStorage.getItem('vca-user-id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('vca-user-id', id);
  }
  setUserId(id);
}, []);

class ParsedIntent(BaseModel):
    action: Literal["add", "update", "remove", "search", "checkout"]
    item: str
    quantity: int = 1
    unit: str = "item"
    confidence: float = 0.8
    notes: str | None = None


class CartState(TypedDict):
    user_id: str
    cart: dict[str, int]
    raw_text: str
    memory: list[str]
    last_item: str | None
    last_action: str | None
    preference: str
    parsed_intent: dict[str, Any]
    search_result: dict[str, Any]
    response: dict[str, Any]


app.state.session_memory: dict[str, dict[str, Any]] = {}


def get_session_state(user_id: str) -> dict[str, Any]:
    store = app.state.session_memory
    if user_id not in store:
        store[user_id] = {
            "cart": {},
            "history": [],
            "last_item": None,
            "last_action": None,
        }
    return store[user_id]


WORD_TO_NUMBER = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "a": 1, "an": 1,
}

def extract_quantity(text: str) -> tuple[int, str]:
    lowered = text.lower()

    quantity_match = re.search(
        r"\b(\d+)\s*(carton|cartons|bottle|bottles|box|boxes|pack|packs|kg|lb|item|items|unit|units)\b",
        lowered,
    )
    if quantity_match:
        return int(quantity_match.group(1)), quantity_match.group(2)

    number_match = re.search(r"\b(\d+)\b", text)
    if number_match:
        return int(number_match.group(1)), "item"

    # NEW: fall back to spelled-out number words
    word_match = re.search(
        r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\b", lowered
    )
    if word_match:
        return WORD_TO_NUMBER[word_match.group(1)], "item"

    return 1, "item"

def extract_core_product(text: str) -> str:
    """Attempt to extract the core product name from conversational text.
    Removes common filler phrases, quantities, and trailing 'to my cart' style fragments.
    Falls back to a lightweight cleanup when patterns don't match.
    """
    t = text.strip()
    # Normalize spacing and remove polite phrases
    t = re.sub(r"\b(please|thanks|thank you|for me|could you|can you|i need)\b", "", t, flags=re.IGNORECASE).strip()
    # Remove written number words like 'one', 'two', 'a', 'an'
    t = re.sub(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|a|an)\b", "", t, flags=re.IGNORECASE).strip()
    # Remove common unit words (carton, bottles, pack, etc.) to reduce noise
    t = re.sub(r"\b(carton|cartons|bottle|bottles|box|boxes|pack|packs|kg|lb|item|items|unit|units|carton(s)?)\b", "", t, flags=re.IGNORECASE).strip()
    # Pattern: optional verb, optional quantity+unit, capture product, optional trailing phrase
    m = re.search(r"(?:\b(add|buy|get|grab|pick up|remove|delete|take out)\b\s*)?(?:\b(\d+)\b\s*(?:carton|cartons|bottle|bottles|box|boxes|pack|packs|kg|lb|item|items|unit|units)?\s*)?(?P<product>[\w\s'-]+?)(?:\s*(?:to my cart|to cart|in my cart|for me|please|now|thanks|thank you))?$", t, flags=re.IGNORECASE)
    if m:
        product = m.group('product') or ''
        product = re.sub(r"\b(\d+)\b", "", product).strip()
        product = re.sub(r"[^\w\s'-]", '', product).strip()
        return product

    # Fallback: remove known phrases and digits
    fallback = re.sub(r"\b(add|buy|get|grab|pick up|remove|delete|take out|to my cart|to cart|in my cart|i need)\b", "", t, flags=re.IGNORECASE)
    fallback = re.sub(r"\b(\d+)\b", "", fallback)
    fallback = re.sub(r"[^\w\s'-]", '', fallback).strip()
    return fallback


def local_intent_parser(text: str, last_item: str | None = None) -> ParsedIntent:
    normalized = text.strip()
    lowered = normalized.lower()

    if re.search(r"\b(remove|delete|take out)\b", lowered):
        action = "remove"
    elif re.search(r"\b(make it|change to|set it to|update to|increase to|make it\s*\d+)\b", lowered):
        action = "update"
    elif re.search(r"\b(add|buy|get|grab|pick up)\b", lowered):
        action = "add"
    elif re.search(r"\b(search|find|look up)\b", lowered):
        action = "search"
    else:
        action = "add"

    quantity, unit = extract_quantity(normalized)

    # Extract a clean product name (robust fallback) that strips fillers/quantities
    item_name = extract_core_product(normalized) or last_item

    if not item_name and last_item:
        item_name = last_item

    if not item_name:
        raise ValueError("Could not determine the product name from the voice command.")

    return ParsedIntent(
        action=action,
        item=item_name,
        quantity=quantity,
        unit=unit,
        confidence=0.86,
    )


def parse_with_llm(text: str, last_item: str | None = None, preference: str = "budget") -> ParsedIntent:
    # If the genai client isn't available, fall back to local parser
    if genai is None:
        return local_intent_parser(text, last_item)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return local_intent_parser(text, last_item)

    # Prompt instructs the LLM about how to treat items based on the user preference
    # and to strictly extract the core product name (no filler, no quantities).
    prompt = f"""
    You are an assistant that extracts shopping intents from transcribed voice commands.
    Strictly return valid JSON only with keys: action, item, quantity, unit, confidence, notes.
    - action must be one of: add, update, remove, search, checkout.
    - item must be the CORE product name only (no filler words, no quantities, no verbs). Examples: 'bread', 'organic whole milk', 'hass avocado'.
    - quantity must be an integer (default to 1 when not specified).

    Remove conversational filler like 'add', 'to my cart', 'please', 'I need', 'buy', 'for me', and strip numeric quantities/units.
    If the transcript is ambiguous about the product name, return the most concise product phrase (e.g., from 'add one bread to my cart' return 'bread').

    IMPORTANT: The user's preference is "{preference}".
    - If preference is 'budget', bias substitutions toward higher-rated items with lower price (respect the quality floor where possible).
    - If preference is 'premium', prefer items with tags: organic, artisanal, premium, high-quality.

    Good examples (input -> expected JSON):
    Input: "Add one bread to my cart"
    Output: {"action":"add","item":"bread","quantity":1,"unit":"item","confidence":0.95,"notes":"Stripped filler and quantity"}

    Input: "Please buy two cartons of almond milk"
    Output: {"action":"add","item":"almond milk","quantity":2,"unit":"carton","confidence":0.95,"notes":"Removed politeness and extracted quantity/unit"}

    Input: "Remove eggs"
    Output: {"action":"remove","item":"eggs","quantity":1,"unit":"item","confidence":0.9,"notes":"Remove action detected"}

    Bad examples (what NOT to return):
    Input: "Add one bread to my cart"
    Output (BAD): {"action":"add","item":"add one bread to my cart","quantity":1,"unit":"item","confidence":0.5}

    Input: "Add two milk cartons"
    Output (BAD): {"action":"add","item":"two milk cartons","quantity":1,"unit":"item","confidence":0.5}

    Always prefer the Good Output form. Return only a single JSON object and nothing else.
    """
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, text],
        )
        raw = getattr(response, "text", str(response))
        parsed = json.loads(raw)
        # Ensure extracted item is cleaned defensively
        parsed['item'] = parsed.get('item', '').strip()
        return ParsedIntent(**parsed)
    except Exception:
        return local_intent_parser(text, last_item)


# Load or generate a large MOCK_INVENTORY in a separate data file for easier inspection and maintenance.
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MOCK_FILE = DATA_DIR / "mock_inventory.json"

if MOCK_FILE.exists():
    try:
        with MOCK_FILE.open('r', encoding='utf-8') as f:
            MOCK_INVENTORY = json.load(f)
    except Exception:
        MOCK_INVENTORY = []
else:
    # Generate and write the inventory file once
    seeds = [
        ("Whole Wheat Bread", "bakery", ["standard"] , 2.5, 4.4),
        ("Store Brand Bread", "bakery", ["budget"], 1.5, 2.6),
        ("Artisanal Sourdough", "bakery", ["artisanal", "premium"], 5.5, 4.8),
        ("Organic Whole Milk", "dairy", ["organic", "premium"], 3.5, 4.6),
        ("Whole Milk", "dairy", ["standard"], 2.3, 4.1),
        ("Almond Milk", "beverages", ["standard"], 3.9, 4.0),
        ("Farm Fresh Eggs", "dairy", ["free-range", "premium"], 4.2, 4.5),
        ("Greek Yogurt", "dairy", ["premium"], 5.1, 4.7),
        ("Hass Avocado", "produce", ["standard"], 1.5, 4.3),
        ("Bananas", "produce", ["standard"], 0.99, 4.2),
        ("Organic Strawberries", "produce", ["organic", "premium"], 4.99, 4.6),
        ("Cheddar Cheese", "dairy", ["standard"], 3.5, 4.0),
        ("Artisan Olive Oil", "pantry", ["premium"], 12.0, 4.9),
    ]
    inventory = []
    brands = ["Everyday", "Prime", "Nature's", "Harvest", "Corner", "Local", "Farmers", "Superior"]
    idx = 0
    target = 2200
    while len(inventory) < target:
        seed = seeds[idx % len(seeds)]
        brand = brands[idx % len(brands)]
        multiplier = 1 + ((idx % 7) - 3) * 0.05
        price = round(seed[3] * max(0.5, multiplier), 2)
        # initial rating with mild variation
        rating = round(max(1.0, min(5.0, seed[4] + ((idx % 11) - 5) * 0.06)), 1)
        name = f"{brand} {seed[0]}"
        tags = list(seed[2])
        # intentionally add premium/budget markers with some distribution
        if idx % 23 == 0:
            tags.append('premium')
        if idx % 19 == 0:
            tags.append('budget')
        # Enforce quality floor for premium-tagged items: ensure rating >= 4.0
        if 'premium' in tags and rating < 4.0:
            rating = round(4.0 + abs((idx % 3)) * 0.1, 1)
            if rating > 5.0:
                rating = 5.0
        # Ensure that items labeled 'budget' can have lower ratings, leave as-is
        item = {
            'id': f'item-{idx+1}',
            'name': name,
            'category': seed[1],
            'price': price,
            'availability': 'in_stock' if (idx % 13) != 0 else 'limited',
            'tags': tags,
            'rating': rating,
        }
        inventory.append(item)
        idx += 1
    MOCK_INVENTORY = inventory
    try:
        with MOCK_FILE.open('w', encoding='utf-8') as f:
            json.dump(MOCK_INVENTORY, f, ensure_ascii=False)
    except Exception:
        pass


def mock_pinecone_lookup(item_name: str, preference: str = "budget") -> dict[str, Any]:
    # Build lookup dictionary from the loaded inventory
    catalog: dict[str, dict[str, Any]] = {}
    for item in MOCK_INVENTORY:
        key = item['name'].lower()
        catalog[key] = item

    normalized = item_name.lower().strip()
    if not normalized:
        return {"matched": False, "message": "No item provided."}

    # Exact match (but apply quality-floor if preference is 'budget')
    exact = catalog.get(normalized)
    if exact:
        if preference == "budget" and exact.get("rating", 0) < 4.0:
            # Ignore low-rated exact match and continue to find acceptable substitutes
            exact = None
        else:
            return {
                "matched": True,
                "item": exact["name"],
                "category": exact["category"],
                "price": exact["price"],
                "availability": exact["availability"],
                "tags": exact.get("tags", []),
                "rating": exact.get("rating"),
                "source": "mock_pinecone_vector_similarity",
            }

    # Collect candidate matches using substring matching
    candidates = []
    for key, product in catalog.items():
        if key in normalized or normalized in key:
            candidates.append(product)

    # If candidates found, pick based on preference and quality-floor for budget
    if candidates:
        if preference == "budget":
            # Enforce a quality floor: only consider candidates with rating >= 4.0
            high_quality = [p for p in candidates if p.get("rating", 0) >= 4.0]
            if high_quality:
                chosen = min(high_quality, key=lambda p: p.get("price", float("inf")))
            else:
                # No high-quality candidates — fall back to cheapest available but include a warning
                chosen = min(candidates, key=lambda p: p.get("price", float("inf")))
                chosen = dict(chosen)
                chosen["note"] = "Selected the cheapest available option; no high-rated alternatives found."
        else:
            # prefer premium tags, otherwise highest rated then highest priced
            premium_candidates = [p for p in candidates if any(t in p.get("tags", []) for t in ("organic", "artisanal", "premium", "high-quality"))]
            if premium_candidates:
                # Among premium candidates, prefer the highest rated then price
                chosen = max(premium_candidates, key=lambda p: (p.get("rating", 0), p.get("price", 0)))
            else:
                # Fallback: pick the highest rated candidate (quality first)
                chosen = max(candidates, key=lambda p: (p.get("rating", 0), p.get("price", 0)))

        return {
            "matched": True,
            "item": chosen["name"],
            "category": chosen["category"],
            "price": chosen["price"],
            "availability": chosen["availability"],
            "tags": chosen.get("tags", []),
            "rating": chosen.get("rating"),
            "source": "mock_pinecone_vector_similarity",
        }

    # =====================================================================
    # EXCEPTIONAL HANDLING: EXTERNAL CATALOG RESOLUTION & CACHE UPDATE
    # If the item is not found in the local cache, we simulate an external 
    # API call to find it, and then dynamically inject it into our local 
    # inventory JSON. This ensures frontend budget calculations sync perfectly.
    # =====================================================================
    
    estimated_market_price = round(random.uniform(2.50, 45.00), 2)
    average_rating = round(random.uniform(4.0, 4.8), 1)
    
    new_item_doc = {
        "id": f"item-ext-{random.randint(10000, 99999)}",
        "name": item_name.title(),
        "category": "extended_catalog",
        "price": estimated_market_price,
        "availability": "special_order",
        "tags": ["external-source", "dynamic-pricing"],
        "rating": average_rating
    }
    
    # 1. Add it to the active backend memory
    MOCK_INVENTORY.append(new_item_doc)
    
    # 2. Save it permanently to the JSON file so the frontend can read the price!
    try:
        with MOCK_FILE.open('w', encoding='utf-8') as f:
            json.dump(MOCK_INVENTORY, f, ensure_ascii=False)
    except Exception as e:
        pass # Fail silently if file is locked, backend will still process it

    return {
        "matched": True,
        "item": new_item_doc["name"],
        "category": new_item_doc["category"],
        "price": new_item_doc["price"],
        "availability": new_item_doc["availability"],
        "tags": new_item_doc["tags"],
        "rating": new_item_doc["rating"],
        "source": "external_distributor_mock",
        "note": f"Item '{item_name}' was not in local cache; resolved via external catalog simulation with estimated market pricing."
    }


def build_graph():
    if StateGraph is None or END is None or START is None:
        raise RuntimeError("langgraph is required to compile the stateful shopping graph.")

    def parse_node(state: CartState) -> CartState:
        session = get_session_state(state["user_id"])
        last_item = session.get("last_item")
        # Pass preference to the LLM parser so it can bias item interpretation and substitutions
        preference = state.get("preference", "budget")
        intent = parse_with_llm(state["raw_text"], last_item, preference)

        if re.search(r"\b(make it|change to|set it to|update to|increase to)\b", state["raw_text"].lower()) and last_item:
            intent.action = "update"
            intent.item = last_item
            quantity, _ = extract_quantity(state["raw_text"])
            intent.quantity = quantity

        state["parsed_intent"] = intent.model_dump()
        state["memory"] = list(session.get("history", [])) + [f"{intent.action}:{intent.item}:{intent.quantity}"]
        return state

    def apply_cart_node(state: CartState) -> CartState:
        session = get_session_state(state["user_id"])
        cart = dict(session.get("cart", {}))
        intent = ParsedIntent(**state["parsed_intent"])

        if intent.action == "add":
            cart[intent.item] = cart.get(intent.item, 0) + intent.quantity
        elif intent.action == "update":
            cart[intent.item] = intent.quantity
        elif intent.action == "remove":
            cart.pop(intent.item, None)
        elif intent.action == "search":
            cart = cart

        state["cart"] = cart
        state["last_item"] = intent.item
        state["last_action"] = intent.action
        return state

    def search_node(state: CartState) -> CartState:
        intent = ParsedIntent(**state["parsed_intent"])
        preference = state.get("preference", "budget")
        state["search_result"] = mock_pinecone_lookup(intent.item, preference)
        return state

    def finalize_node(state: CartState) -> CartState:
        intent = ParsedIntent(**state["parsed_intent"])
        product = state["search_result"]
        preference = state.get("preference", "budget")

        explanation = None

        if intent.action in {"add", "update", "remove"}:
            summary = {
                "status": "ok",
                "action": intent.action,
                "item": intent.item,
                "quantity": intent.quantity,
                "cart": state["cart"],
                "last_item": intent.item,
                "suggestions": [],
                "result":product,

            }

            if product.get("matched") is False:
                summary["suggestions"] = product.get("suggestions", [])
                explanation = "No direct match found; returned suggestions based on your preference."
            else:
                # Build an explanation for why this product was selected
                if product.get("note"):
                    explanation = product.get("note")
                else:
                    rating = product.get("rating")
                    price = product.get("price")
                    if preference == "budget":
                        explanation = f"Chose {product.get('item')} because it meets your budget preference and has a rating of {rating} and price ${price}."
                    else:
                        explanation = f"Chose {product.get('item')} because it matches your premium preference (tags: {', '.join(product.get('tags', []))}) with rating {rating}."

        elif intent.action == "search":
            summary = {
                "status": "ok",
                "action": "search",
                "query": intent.item,
                "result": product,
            }
            explanation = None
        else:
            summary = {"status": "ok", "action": "checkout", "cart": state["cart"]}

        if explanation:
            summary["explanation"] = explanation

        state["response"] = summary
        return state

    workflow = StateGraph(CartState)
    workflow.add_node("parse", parse_node)
    workflow.add_node("apply_cart", apply_cart_node)
    workflow.add_node("search", search_node)
    workflow.add_node("finalize", finalize_node)

    workflow.add_edge(START, "parse")
    workflow.add_edge("parse", "apply_cart")
    workflow.add_edge("apply_cart", "search")
    workflow.add_edge("search", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


shopping_graph = build_graph()


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors(), "message": "Request validation failed."})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred.", "message": str(exc)})


@app.get("/")
async def root():
    return {"message": "Voice Command Shopping Assistant is running."}


@app.post("/search")
async def search_product(payload: VoiceCommandRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        parsed = parse_with_llm(payload.text, get_session_state(payload.user_id).get("last_item"), payload.preference)
        product = mock_pinecone_lookup(parsed.item, payload.preference)

        seasonal_hint = "Seasonal recommendations: fresh berries and citrus are trending this week."
        if product.get("matched") is False:
            product["seasonal_hint"] = seasonal_hint
            product["alternatives"] = [
                "Try almond milk as a dairy-free alternative.",
                "Fresh seasonal produce is typically a good substitute for out-of-stock basics.",
            ]

        return {
            "query": payload.text,
            "parsed_intent": parsed.model_dump(),
            "result": product,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(exc)}") from exc


@app.post("/api/voice-command")
async def voice_command(payload: VoiceCommandRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Voice command text cannot be empty.")

    session = get_session_state(payload.user_id)
    state: CartState = {
        "user_id": payload.user_id,
        "cart": dict(session.get("cart", {})),
        "raw_text": payload.text,
        "memory": list(session.get("history", [])),
        "last_item": session.get("last_item"),
        "last_action": session.get("last_action"),
        "preference": payload.preference,
        "parsed_intent": {},
        "search_result": {},
        "response": {},
    }

    try:
        result = shopping_graph.invoke(state)
        session["cart"] = result["cart"]
        session["history"] = result["memory"]
        session["last_item"] = result["last_item"]
        session["last_action"] = result["last_action"]
        return result["response"]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(exc)}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
