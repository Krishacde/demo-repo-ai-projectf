import os
import hmac
import hashlib
import uuid
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_BASE_URL = "https://api.razorpay.com/v1"

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


def _check_config():
    if not RAZORPAY_KEY_ID:
        raise RuntimeError("RAZORPAY_KEY_ID is missing from .env")

    if not RAZORPAY_KEY_SECRET:
        raise RuntimeError("RAZORPAY_KEY_SECRET is missing from .env")


def create_hotel_order(
    hotel_name: str,
    amount_inr: float,
    trip_id: str,
    travelers: int = 1,
) -> dict[str, Any]:
    _check_config()

    amount_inr = float(amount_inr)

    if amount_inr <= 0:
        raise ValueError("Hotel amount must be greater than zero.")

    amount_paise = int(round(amount_inr * 100))
    receipt = f"hotel_{uuid.uuid4().hex[:18]}"

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt,
        "notes": {
            "trip_id": trip_id,
            "booking_type": "accommodation",
            "hotel_name": hotel_name[:200],
            "travelers": str(travelers),
        },
    }

    response = requests.post(
        f"{RAZORPAY_BASE_URL}/orders",
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
        json=payload,
        timeout=30,
    )

    try:
        data = response.json()
    except Exception:
        data = {}

    if response.status_code >= 400:
        error = data.get("error", {})
        raise RuntimeError(
            error.get("description")
            or error.get("reason")
            or "Razorpay order creation failed."
        )

    return {
        "id": data["id"],
        "amount": data["amount"],
        "currency": data["currency"],
        "receipt": data.get("receipt"),
        "status": data.get("status"),
        "key_id": RAZORPAY_KEY_ID,
        "hotel_name": hotel_name,
        "trip_id": trip_id,
        "booking_type": "accommodation",
    }


def verify_hotel_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> bool:
    _check_config()

    if not all(
        [razorpay_order_id, razorpay_payment_id, razorpay_signature]
    ):
        return False

    generated_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        generated_signature,
        razorpay_signature,
    )


def fetch_payment(razorpay_payment_id: str) -> dict[str, Any]:
    _check_config()

    response = requests.get(
        f"{RAZORPAY_BASE_URL}/payments/{razorpay_payment_id}",
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
        timeout=30,
    )

    response.raise_for_status()
    return response.json()
