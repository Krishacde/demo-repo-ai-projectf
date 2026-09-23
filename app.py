# import sys
# import asyncio
# import threading
# import time
# import os
# from pathlib import Path
# # app.py
# # ADD THESE IMPORTS



# import logging
# import traceback
# import uvicorn

# from fastapi import FastAPI, Request

# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# from pydantic import BaseModel, Field

# from backend import RequestCancelled, TripRequest, run_travel_agent, run_trip, run_discovery, replanning_agent
# from tools.flight_tool import API_KEY as AVIATIONSTACK_API_KEY

# from fastapi.responses import HTMLResponse, JSONResponse
# from pydantic import BaseModel, Field

# from tools.razorpay_payment import (
#     create_hotel_order,
#     verify_hotel_payment,
#     fetch_payment,
#     fetch_order,
# )

# # Reconfigure stdout/stderr for Windows UTF-8 console output
# if sys.platform == "win32":
#     try:
#         sys.stdout.reconfigure(encoding='utf-8', errors='replace')
#         sys.stderr.reconfigure(encoding='utf-8', errors='replace')
#     except Exception:
#         pass

# BASE_DIR = Path(__file__).resolve().parent

# # Edit these two values to tune the request limiter for local or hosted use.
# RATE_LIMIT_WINDOW_SECONDS = 60
# RATE_LIMIT_MAX_REQUESTS = 6
# _rate_limit_history: dict[str, list[float]] = {}
# _rate_limit_lock = threading.Lock()
# logger = logging.getLogger("tripmate.api")
# logger.setLevel(logging.INFO)
# log_formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")



# if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers):
#     console_handler = logging.StreamHandler(sys.stdout)
#     console_handler.setFormatter(log_formatter)
#     logger.addHandler(console_handler)

# if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
#     file_handler = logging.FileHandler(BASE_DIR / "tripmate.log", encoding="utf-8")
#     file_handler.setFormatter(log_formatter)
#     logger.addHandler(file_handler)

# app = FastAPI(
#     title="TripMate AI",
#     description="LangGraph Multi-Agent Travel Planner with FastAPI Frontend",
#     version="2.0.0"
# )

# app.mount(
#     "/static",
#     StaticFiles(directory=str(BASE_DIR / "static")),
#     name="static"
# )

# templates = Jinja2Templates(
#     directory=str(BASE_DIR / "templates")
# )


# def rate_limit_response(request: Request, bucket: str) -> JSONResponse | None:
#     client_key = f"{bucket}:{request.client.host if request.client else 'unknown'}"
#     now = time.monotonic()
#     with _rate_limit_lock:
#         recent = [stamp for stamp in _rate_limit_history.get(client_key, []) if now - stamp < RATE_LIMIT_WINDOW_SECONDS]
#         if len(recent) >= RATE_LIMIT_MAX_REQUESTS:
#             _rate_limit_history[client_key] = recent
#             return JSONResponse(
#                 status_code=429,
#                 content={"success": False, "error": "Too many requests. Please wait before starting another agent run."},
#                 headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
#             )
#         recent.append(now)
#         _rate_limit_history[client_key] = recent
#     return None


# async def run_cancellable(request: Request, operation, *args, **kwargs):
#     cancellation_event = threading.Event()
#     task = asyncio.create_task(asyncio.to_thread(operation, *args, cancellation_event=cancellation_event, **kwargs))
#     while not task.done():
#         await asyncio.wait({task}, timeout=0.25)
#         if await request.is_disconnected():
#             cancellation_event.set()
#             break
#     try:
#         return await task
#     except RequestCancelled:
#         raise


# class TravelRequest(BaseModel):
#     message: str
#     thread_id: str | None = None


# class GuidedTripRequest(TripRequest):
#     thread_id: str | None = None


# class ProviderSelectionRequest(BaseModel):
#     trip_id: str
#     provider_type: str
#     option: dict

# # app.py
# # ADD THESE PYDANTIC MODELS AFTER ProviderSelectionRequest

# class HotelPaymentOrderRequest(BaseModel):
#     trip_id: str
#     hotel: dict
#     travelers: int = Field(default=1, ge=1, le=50)


# class HotelPaymentVerifyRequest(BaseModel):
#     trip_id: str
#     hotel: dict

#     razorpay_order_id: str
#     razorpay_payment_id: str
#     razorpay_signature: str


# class HotelBookingConfirmRequest(BaseModel):
#     trip_id: str
#     hotel: dict

#     razorpay_order_id: str
#     razorpay_payment_id: str


# class DiscoveryQueryRequest(BaseModel):
#     origin: str
#     month: str = "August"
#     year: int = 2026
#     days: int = Field(default=5, ge=1, le=30)
#     start_date: str | None = None
#     end_date: str | None = None
#     travelers: int = 1
#     budget: float | None = None
#     currency: str = "INR"
#     mood: str | None = None
#     interests: list[str] = []
#     weather_preference: str | None = "Pleasant"
#     pace: str | None = "Balanced"
#     accommodation: str | None = "Mid-range hotel"
#     special_requirements: str | None = None


# class ReplanPayload(BaseModel):
#     trip_id: str
#     change_text: str
#     itinerary: list[dict] = []
#     trip_context: dict = {}


# @app.get("/", response_class=HTMLResponse)
# async def home(request: Request):
#     return templates.TemplateResponse(
#         request=request,
#         name="index.html",
#         context={}
#     )


# @app.get("/discover", response_class=HTMLResponse)
# async def discover_page(request: Request):
#     return templates.TemplateResponse(
#         request=request,
#         name="discover.html",
#         context={}
#     )


# @app.post("/api/travel")
# async def travel_planner(request: Request, request_data: TravelRequest):
#     limited = rate_limit_response(request, "travel")
#     if limited:
#         return limited
#     try:
#         user_message = request_data.message.strip()
#         if not user_message:
#             return JSONResponse(
#                 status_code=400,
#                 content={"success": False, "error": "Message cannot be empty."}
#             )

#         result = run_travel_agent(
#             user_input=user_message,
#             thread_id=request_data.thread_id
#         )

#         return JSONResponse(
#             content={
#                 "success": True,
#                 "thread_id": result["thread_id"],
#                 "answer": result["answer"],
#                 "flight_results": result["flight_results"],
#                 "hotel_results": result["hotel_results"],
#                 "itinerary": result["itinerary"],
#                 "llm_calls": result["llm_calls"],
#             }
#         )

#     except Exception as e:
#         logger.exception("travel_planner failed: %s", e)
#         traceback.print_exc()
#         return JSONResponse(
#             status_code=500,
#             content={"success": False, "error": str(e)}
#         )


# @app.post("/api/trips/{trip_id}/selections")
# async def select_provider(
#     trip_id: str,
#     request_data: ProviderSelectionRequest,
# ):
#     """
#     Provider selection router.

#     Hotel:
#         selection -> frontend opens Payment Agent

#     Flight/Cab:
#         existing demo selection behavior
#     """

#     if trip_id != request_data.trip_id:
#         return JSONResponse(
#             status_code=400,
#             content={
#                 "success": False,
#                 "error": "Trip id does not match selection.",
#             },
#         )

#     provider_type = request_data.provider_type

#     if provider_type not in {
#         "flight",
#         "hotel",
#         "cab",
#     }:
#         return JSONResponse(
#             status_code=400,
#             content={
#                 "success": False,
#                 "error": "Unsupported provider selection.",
#             },
#         )

#     option = request_data.option

#     option_name = (
#         option.get("name")
#         or option.get("airline")
#         or "Selected option"
#     )

#     # HOTEL SELECTION
#     #
#     # We intentionally do NOT mark the hotel as booked here.
#     #
#     # The next step is:
#     #
#     # Hotel Selected
#     #      ↓
#     # Payment Agent
#     #      ↓
#     # Razorpay
#     #      ↓
#     # Payment Verification
#     #      ↓
#     # Booking Agent

#     if provider_type == "hotel":
#         return {
#             "success": True,
#             "trip_id": trip_id,
#             "selection": {
#                 "type": "hotel",
#                 "name": option_name,
#                 "option": option,
#             },
#             "next_action": "PAYMENT_REQUIRED",
#             "payment_required": True,
#             "message": (
#                 f"{option_name} selected. "
#                 "Payment is required to confirm accommodation."
#             ),
#         }

#     # Existing behavior for flight/cab
#     detail = (
#         option.get("flight_number")
#         or option.get("area")
#         or option.get("location")
#         or "provider option"
#     )

#     label = {
#         "flight": "flight",
#         "cab": "transport",
#     }[provider_type]

#     return {
#         "success": True,
#         "trip_id": trip_id,
#         "selection": {
#             "type": provider_type,
#             "name": option_name,
#             "option": option,
#         },
#         "itinerary_update": {
#             "time": "Plan update",
#             "title": f"Selected {label}: {option_name}",
#             "description": (
#                 f"{detail} added to the plan. "
#                 "Connected provider APIs can replace this estimate."
#             ),
#         },
#         "message": (
#             f"{option_name} added. "
#             "Your itinerary was refreshed."
#         ),
#     }

# @app.post("/api/trips")
# async def create_trip(request: Request, request_data: GuidedTripRequest):
#     """Run the evidence-first LangGraph planner with structured user choices."""
#     limited = rate_limit_response(request, "trip")
#     if limited:
#         return limited
#     try:
#         payload = request_data.model_dump(mode="json", exclude={"thread_id"})
#         logger.info("request=trip_create status=started thread_id=%s destination=%s", request_data.thread_id or "new", payload.get("destination"))
#         trip = await run_cancellable(request, run_trip, payload, request_data.thread_id)
#         return JSONResponse(content={"success": True, "trip": trip})
#     except RequestCancelled:
#         return JSONResponse(status_code=499, content={"success": False, "cancelled": True, "error": "Trip research cancelled."})
#     except Exception as exc:
#         logger.exception("request=trip_create status=failed error=%s", exc)
#         traceback.print_exc()
#         return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})


# @app.post("/api/discover")
# async def discover_destinations(request: Request, request_data: DiscoveryQueryRequest):
#     """Run LangGraph Multi-Agent Discovery Pipeline to find clean, ranked destination cards."""
#     limited = rate_limit_response(request, "discover")
#     if limited:
#         return limited
#     try:
#         logger.info(
#             "request=destination_discovery status=started origin=%s month=%s year=%s",
#             request_data.origin, request_data.month, request_data.year
#         )
#         discovery_result = await run_cancellable(request, run_discovery,
#             origin=request_data.origin.strip(),
#             month=request_data.month.strip(),
#             year=request_data.year,
#             days=request_data.days,
#             interests=request_data.interests,
#             mood=request_data.mood
#         )
#         return JSONResponse(content={
#             "success": True,
#             "destinations": discovery_result["destinations"],
#             "scout_summary": discovery_result["scout_summary"],
#             "progress": discovery_result["progress"],
#             "warnings": discovery_result["warnings"]
#         })
#     except RequestCancelled:
#         return JSONResponse(status_code=499, content={"success": False, "cancelled": True, "error": "Destination research cancelled."})
#     except Exception as exc:
#         logger.exception("request=destination_discovery status=failed error=%s", exc)
#         traceback.print_exc()
#         return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


# @app.post("/api/trips/replan")
# async def replan_itinerary(request: Request, request_data: ReplanPayload):
#     """Run ReplanningAgent to adjust itinerary based on user input without full regeneration."""
#     limited = rate_limit_response(request, "replan")
#     if limited:
#         return limited
#     try:
#         logger.info("request=trip_replan status=started trip_id=%s change=%s", request_data.trip_id, request_data.change_text)
#         result = replanning_agent(
#             change_text=request_data.change_text,
#             current_itinerary=request_data.itinerary,
#             trip_context=request_data.trip_context
#         )
#         return JSONResponse(content={"success": True, **result})
#     except Exception as exc:
#         logger.exception("request=trip_replan status=failed error=%s", exc)
#         traceback.print_exc()
#         return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


# @app.get("/api/diagnostics")
# async def diagnostics():
#     """Report integration readiness without exposing secret values."""
#     def key_state(name: str) -> str:
#         value = os.getenv(name, "").strip()
#         if not value:
#             return "missing"
#         if value.lower().startswith("your_") or value.lower() in {"change_me", "placeholder"}:
#             return "placeholder"
#         return "configured"

#     keys = {
#         "GEMINI_API_KEY": key_state("GEMINI_API_KEY"),
#         "TAVILY_API_KEY": key_state("TAVILY_API_KEY"),
#         "AVIATIONSTACK_API_KEY": key_state("AVIATIONSTACK_API_KEY"),
#         "DATABASE_URL": key_state("DATABASE_URL"),
#          "RAZORPAY_KEY_ID": key_state("RAZORPAY_KEY_ID"),
#     "RAZORPAY_KEY_SECRET": key_state("RAZORPAY_KEY_SECRET"),
#     }
#     logger.info("request=diagnostics keys=%s", keys)
#     return {
#         "status": "ok",
#         "keys": {name: "configured" if value else "missing" for name, value in keys.items()},
#         "notes": {
#             "AVIATIONSTACK_API_KEY": "Live flight status lookup.",
#             "GEMINI_API_KEY": "Required for multi-agent reasoning, ranking, planning and replanning.",
#             "TAVILY_API_KEY": "Required for web research, verified events, and hotel evidence.",
#             "RAZORPAY_KEY_ID": "Razorpay Test Mode checkout key.",
#     "RAZORPAY_KEY_SECRET": "Server-side Razorpay Test Mode secret."
#         }
#     }


# @app.get("/health")
# async def health_check():
#     return {
#         "status": "ok",
#         "message": "TripMate AI Multi-Agent Planner is running"
#     }


# @app.get("/favicon.ico")
# async def favicon():
#     return JSONResponse(content={})

# @app.post("/api/payments/hotel/order")
# async def create_hotel_payment_order(
#     request_data: HotelPaymentOrderRequest,
# ):
#     """
#     Payment Agent:
#     Creates a Razorpay Test Mode order for hotel accommodation.
#     """

#     try:
#         trip_id = request_data.trip_id
#         hotel = request_data.hotel

#         hotel_name = (
#             hotel.get("name")
#             or hotel.get("hotel_name")
#             or hotel.get("title")
#             or "Selected Hotel"
#         )

#         price = hotel.get("price_num")

#         if price is None:
#             price = hotel.get("price")

#         if price is None:
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "success": False,
#                     "error": "Hotel price is missing."
#                 },
#             )

#         # Handle values such as:
#         # 4500
#         # "4500"
#         # "₹4,500"
#         if isinstance(price, str):
#             cleaned_price = (
#                 price.replace("₹", "")
#                 .replace(",", "")
#                 .replace("INR", "")
#                 .strip()
#             )

#             try:
#                 price = float(cleaned_price)
#             except ValueError:
#                 return JSONResponse(
#                     status_code=400,
#                     content={
#                         "success": False,
#                         "error": f"Invalid hotel price: {price}"
#                     },
#                 )

#         price = float(price)

#         if price <= 0:
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "success": False,
#                     "error": "Hotel price must be greater than zero."
#                 },
#             )

#         order = create_hotel_order(
#             hotel_name=hotel_name,
#             amount_inr=price,
#             trip_id=trip_id,
#             travelers=request_data.travelers,
#         )

#         logger.info(
#             "PAYMENT AGENT | hotel order created | trip=%s | order=%s | amount=%s",
#             trip_id,
#             order["id"],
#             order["amount"],
#         )

#         return {
#             "success": True,
#             "payment_status": "ORDER_CREATED",
#             "agent": "PaymentAgent",
#             "order": order,
#         }

#     except Exception as e:
#         logger.exception(
#             "Hotel payment order creation failed: %s",
#             e,
#         )

#         return JSONResponse(
#             status_code=500,
#             content={
#                 "success": False,
#                 "error": str(e),
#             },
#         )
# @app.post("/api/payments/hotel/verify")
# async def verify_hotel_payment_api(
#     request_data: HotelPaymentVerifyRequest,
# ):
#     """
#     Deterministic Payment Verification Node.

#     IMPORTANT:
#     The LLM does NOT decide whether payment succeeded.
#     Razorpay signature + Razorpay payment status are authoritative.
#     """

#     try:
#         valid_signature = verify_hotel_payment(
#             razorpay_order_id=request_data.razorpay_order_id,
#             razorpay_payment_id=request_data.razorpay_payment_id,
#             razorpay_signature=request_data.razorpay_signature,
#         )

#         if not valid_signature:
#             logger.warning(
#                 "PAYMENT VERIFICATION FAILED | trip=%s | order=%s",
#                 request_data.trip_id,
#                 request_data.razorpay_order_id,
#             )

#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "success": False,
#                     "payment_status": "VERIFICATION_FAILED",
#                     "error": "Invalid Razorpay payment signature.",
#                 },
#             )

#         # Verify actual payment with Razorpay
#         payment = fetch_payment(
#             request_data.razorpay_payment_id
#         )

#         payment_status = payment.get("status")

#         logger.info(
#             "PAYMENT VERIFICATION | trip=%s | payment=%s | status=%s",
#             request_data.trip_id,
#             request_data.razorpay_payment_id,
#             payment_status,
#         )

#         if payment_status != "captured":
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "success": False,
#                     "payment_status": payment_status,
#                     "error": (
#                         "Payment signature is valid, "
#                         "but payment is not captured."
#                     ),
#                 },
#             )

#         return {
#             "success": True,
#             "payment_status": "PAID",
#             "verified": True,
#             "agent": "PaymentVerificationNode",
#             "trip_id": request_data.trip_id,
#             "payment": {
#                 "payment_id": request_data.razorpay_payment_id,
#                 "order_id": request_data.razorpay_order_id,
#                 "status": payment_status,
#                 "amount": payment.get("amount"),
#                 "currency": payment.get("currency"),
#                 "method": payment.get("method"),
#             },
#         }

#     except Exception as e:
#         logger.exception(
#             "Hotel payment verification failed: %s",
#             e,
#         )

#         return JSONResponse(
#             status_code=500,
#             content={
#                 "success": False,
#                 "payment_status": "VERIFICATION_ERROR",
#                 "error": str(e),
#             },
#         )
# @app.post("/api/trips/{trip_id}/accommodation/confirm")
# async def confirm_accommodation_booking(
#     trip_id: str,
#     request_data: HotelBookingConfirmRequest,
# ):
#     """
#     Booking Agent.

#     This runs ONLY after Payment Verification succeeds.
#     """

#     if trip_id != request_data.trip_id:
#         return JSONResponse(
#             status_code=400,
#             content={
#                 "success": False,
#                 "error": "Trip ID mismatch."
#             },
#         )

#     try:
#         hotel = request_data.hotel

#         hotel_name = (
#             hotel.get("name")
#             or hotel.get("hotel_name")
#             or hotel.get("title")
#             or "Selected Hotel"
#         )

#         booking_id = (
#             f"HTL-{uuid.uuid4().hex[:10].upper()}"
#         )

#         booking = {
#             "booking_id": booking_id,
#             "booking_type": "accommodation",
#             "status": "CONFIRMED",
#             "hotel": hotel_name,
#             "hotel_details": hotel,
#             "trip_id": trip_id,
#             "payment": {
#                 "status": "PAID",
#                 "razorpay_order_id": request_data.razorpay_order_id,
#                 "razorpay_payment_id": request_data.razorpay_payment_id,
#             },
#         }

#         logger.info(
#             "BOOKING AGENT | accommodation confirmed | trip=%s | booking=%s",
#             trip_id,
#             booking_id,
#         )

#         return {
#             "success": True,
#             "agent": "AccommodationBookingAgent",
#             "booking": booking,
#             "itinerary_update": {
#                 "type": "accommodation",
#                 "title": f"Hotel confirmed: {hotel_name}",
#                 "description": (
#                     f"{hotel_name} has been confirmed "
#                     "after successful payment."
#                 ),
#                 "status": "CONFIRMED",
#             },
#             "message": (
#                 f"{hotel_name} confirmed successfully."
#             ),
#         }

#     except Exception as e:
#         logger.exception(
#             "Accommodation confirmation failed: %s",
#             e,
#         )

#         return JSONResponse(
#             status_code=500,
#             content={
#                 "success": False,
#                 "error": str(e),
#             },
#         )


# if __name__ == "__main__":
#     uvicorn.run(
#         "app:app",
#         host="127.0.0.1",
#         port=8000,
#         reload=False
#     )


#     # app.py
# # ADD THESE ENDPOINTS

# @app.post("/api/payments/hotel/order")
# async def create_hotel_payment_order(
#     request: Request,
#     request_data: HotelPaymentOrderRequest,
# ):
#     """
#     Create a Razorpay TEST MODE order for accommodation.

#     Only hotel/accommodation payments are enabled currently.
#     Flights/cabs are intentionally not handled here yet.
#     """

#     try:
#         hotel = request_data.hotel or {}

#         hotel_name = (
#             hotel.get("name")
#             or hotel.get("hotel_name")
#             or "Accommodation"
#         )

#         # Your existing CleanHotelCard contains price_num.
#         # Example:
#         # price_num = 13500
#         amount = hotel.get("price_num")

#         if amount is None:
#             total_price = hotel.get("total_price")

#             if isinstance(total_price, str):
#                 import re

#                 numbers = re.findall(
#                     r"[\d,]+(?:\.\d+)?",
#                     total_price,
#                 )

#                 if numbers:
#                     amount = float(numbers[0].replace(",", ""))

#         if amount is None:
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "success": False,
#                     "error": "Hotel price is missing."
#                 },
#             )

#         try:
#             amount = float(amount)
#         except (TypeError, ValueError):
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "success": False,
#                     "error": "Invalid hotel price."
#                 },
#             )

#         if amount <= 0:
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "success": False,
#                     "error": "Hotel price must be greater than zero."
#                 },
#             )

#         order = create_hotel_order(
#             hotel_name=hotel_name,
#             amount_inr=amount,
#             trip_id=request_data.trip_id,
#             travelers=request_data.travelers,
#         )

#         return JSONResponse(
#             content={
#                 "success": True,
#                 "payment": {
#                     "key_id": order["key_id"],
#                     "order_id": order["id"],
#                     "amount": order["amount"],
#                     "currency": order["currency"],
#                     "hotel_name": order["hotel_name"],
#                     "trip_id": order["trip_id"],
#                     "booking_type": "accommodation",
#                 },
#             }
#         )

#     except Exception as exc:
#         logger.exception(
#             "hotel_payment_order_failed: %s",
#             exc,
#         )

#         return JSONResponse(
#             status_code=500,
#             content={
#                 "success": False,
#                 "error": str(exc),
#             },
#         )


# @app.post("/api/payments/hotel/verify")
# async def verify_hotel_payment_endpoint(
#     request_data: HotelPaymentVerifyRequest,
# ):
#     """
#     Verify Razorpay payment signature.

#     Payment is considered successful only after this
#     server-side verification succeeds.
#     """

#     try:
#         valid = verify_hotel_payment(
#             razorpay_order_id=request_data.razorpay_order_id,
#             razorpay_payment_id=request_data.razorpay_payment_id,
#             razorpay_signature=request_data.razorpay_signature,
#         )

#         if not valid:
#             return JSONResponse(
#                 status_code=400,
#                 content={
#                     "success": False,
#                     "payment_verified": False,
#                     "error": "Invalid Razorpay payment signature.",
#                 },
#             )

#         payment = fetch_payment(
#             request_data.razorpay_payment_id
#         )

#         payment_status = payment.get("status")

#         return JSONResponse(
#             content={
#                 "success": True,
#                 "payment_verified": True,
#                 "booking_type": "accommodation",
#                 "trip_id": request_data.trip_id,
#                 "hotel": request_data.hotel,
#                 "payment": {
#                     "payment_id": request_data.razorpay_payment_id,
#                     "order_id": request_data.razorpay_order_id,
#                     "status": payment_status,
#                     "amount": payment.get("amount"),
#                     "currency": payment.get("currency"),
#                     "method": payment.get("method"),
#                 },
#                 "message": (
#                     "Accommodation payment verified successfully."
#                     if payment_status == "captured"
#                     else f"Payment verified. Razorpay status: {payment_status}"
#                 ),
#             }
#         )

#     except Exception as exc:
#         logger.exception(
#             "hotel_payment_verification_failed: %s",
#             exc,
#         )

#         return JSONResponse(
#             status_code=500,
#             content={
#                 "success": False,
#                 "payment_verified": False,
#                 "error": str(exc),
#             },
#         )

import sys
import asyncio
import threading
import time
import os
import uuid
from pathlib import Path

# Reconfigure stdout/stderr for Windows UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import logging
import traceback
import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from backend import RequestCancelled, TripRequest, run_travel_agent, run_trip, run_discovery, replanning_agent
from tools.flight_tool import API_KEY as AVIATIONSTACK_API_KEY
from tools.razorpay_payment import (
    create_hotel_order,
    verify_hotel_payment,
    fetch_payment,
)

BASE_DIR = Path(__file__).resolve().parent

# Edit these two values to tune the request limiter for local or hosted use.
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 6
_rate_limit_history: dict[str, list[float]] = {}
_rate_limit_lock = threading.Lock()
logger = logging.getLogger("tripmate.api")
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers):
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
    file_handler = logging.FileHandler(BASE_DIR / "tripmate.log", encoding="utf-8")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

app = FastAPI(
    title="TripMate AI",
    description="LangGraph Multi-Agent Travel Planner with FastAPI Frontend",
    version="2.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


def rate_limit_response(request: Request, bucket: str) -> JSONResponse | None:
    client_key = f"{bucket}:{request.client.host if request.client else 'unknown'}"
    now = time.monotonic()
    with _rate_limit_lock:
        recent = [stamp for stamp in _rate_limit_history.get(client_key, []) if now - stamp < RATE_LIMIT_WINDOW_SECONDS]
        if len(recent) >= RATE_LIMIT_MAX_REQUESTS:
            _rate_limit_history[client_key] = recent
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": "Too many requests. Please wait before starting another agent run."},
                headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
            )
        recent.append(now)
        _rate_limit_history[client_key] = recent
    return None


async def run_cancellable(request: Request, operation, *args, **kwargs):
    cancellation_event = threading.Event()
    task = asyncio.create_task(asyncio.to_thread(operation, *args, cancellation_event=cancellation_event, **kwargs))
    while not task.done():
        await asyncio.wait({task}, timeout=0.25)
        if await request.is_disconnected():
            cancellation_event.set()
            break
    try:
        return await task
    except RequestCancelled:
        raise


class TravelRequest(BaseModel):
    message: str
    thread_id: str | None = None


class GuidedTripRequest(TripRequest):
    thread_id: str | None = None


class ProviderSelectionRequest(BaseModel):
    trip_id: str
    provider_type: str
    option: dict


class HotelPaymentOrderRequest(BaseModel):
    trip_id: str
    hotel: dict
    travelers: int = Field(default=1, ge=1, le=50)


class HotelPaymentVerifyRequest(BaseModel):
    trip_id: str
    hotel: dict
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class HotelBookingConfirmRequest(BaseModel):
    trip_id: str
    hotel: dict
    razorpay_order_id: str
    razorpay_payment_id: str


class DiscoveryQueryRequest(BaseModel):
    origin: str
    month: str = "August"
    year: int = 2026
    days: int = Field(default=5, ge=1, le=30)
    start_date: str | None = None
    end_date: str | None = None
    travelers: int = 1
    budget: float | None = None
    currency: str = "INR"
    mood: str | None = None
    interests: list[str] = []
    weather_preference: str | None = "Pleasant"
    pace: str | None = "Balanced"
    accommodation: str | None = "Mid-range hotel"
    special_requirements: str | None = None


class ReplanPayload(BaseModel):
    trip_id: str
    change_text: str
    itinerary: list[dict] = []
    trip_context: dict = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.get("/discover", response_class=HTMLResponse)
async def discover_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="discover.html",
        context={}
    )


@app.post("/api/travel")
async def travel_planner(request: Request, request_data: TravelRequest):
    limited = rate_limit_response(request, "travel")
    if limited:
        return limited
    try:
        user_message = request_data.message.strip()
        if not user_message:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Message cannot be empty."}
            )

        result = run_travel_agent(
            user_input=user_message,
            thread_id=request_data.thread_id
        )

        return JSONResponse(
            content={
                "success": True,
                "thread_id": result["thread_id"],
                "answer": result["answer"],
                "flight_results": result["flight_results"],
                "hotel_results": result["hotel_results"],
                "itinerary": result["itinerary"],
                "llm_calls": result["llm_calls"],
            }
        )

    except Exception as e:
        logger.exception("travel_planner failed: %s", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/trips/{trip_id}/selections")
async def select_provider(
    trip_id: str,
    request_data: ProviderSelectionRequest,
):
    """
    Provider selection router.

    Hotel selection intentionally does NOT confirm a booking.
    It tells the frontend that payment is the next action.
    """

    if trip_id != request_data.trip_id:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Trip id does not match selection.",
            },
        )

    if request_data.provider_type not in {"flight", "hotel", "cab"}:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Unsupported provider selection.",
            },
        )

    option_name = (
        request_data.option.get("name")
        or request_data.option.get("airline")
        or "Selected option"
    )

    if request_data.provider_type == "hotel":
        return {
            "success": True,
            "trip_id": trip_id,
            "selection": {
                "type": "hotel",
                "name": option_name,
                "option": request_data.option,
            },
            "next_action": "PAYMENT_REQUIRED",
            "payment_required": True,
            "message": (
                f"{option_name} selected. "
                "Payment is required to confirm accommodation."
            ),
        }

    detail = (
        request_data.option.get("flight_number")
        or request_data.option.get("area")
        or request_data.option.get("location")
        or "provider option"
    )

    label = {
        "flight": "flight",
        "cab": "transport",
    }[request_data.provider_type]

    return {
        "success": True,
        "trip_id": trip_id,
        "selection": {
            "type": request_data.provider_type,
            "name": option_name,
            "option": request_data.option,
        },
        "itinerary_update": {
            "time": "Plan update",
            "title": f"Selected {label}: {option_name}",
            "description": (
                f"{detail} added to the plan. "
                "Connected provider APIs can replace this estimate."
            ),
        },
        "message": (
            f"{option_name} added. "
            "Your itinerary was refreshed."
        ),
    }


@app.post("/api/payments/hotel/order")
async def create_hotel_payment_order(
    request_data: HotelPaymentOrderRequest,
):
    """
    Payment Agent:
    Creates a Razorpay Test Mode order for accommodation.
    """

    try:
        hotel = request_data.hotel

        hotel_name = (
            hotel.get("name")
            or hotel.get("hotel_name")
            or hotel.get("title")
            or "Selected Hotel"
        )

        price = (
            hotel.get("total_num")
            or hotel.get("total_price")
            or hotel.get("price_num")
            or hotel.get("price")
        )

        if price is None:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Hotel price is missing.",
                },
            )

        if isinstance(price, str):
            cleaned = (
                price.replace("₹", "")
                .replace(",", "")
                .replace("INR", "")
                .strip()
            )
            try:
                price = float(cleaned)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": f"Invalid hotel price: {price}",
                    },
                )

        amount_inr = float(price)

        if amount_inr <= 0:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Hotel price must be greater than zero.",
                },
            )

        order = create_hotel_order(
            hotel_name=hotel_name,
            amount_inr=amount_inr,
            trip_id=request_data.trip_id,
            travelers=request_data.travelers,
        )

        logger.info(
            "PAYMENT AGENT | hotel order created | trip=%s | order=%s | amount=%s",
            request_data.trip_id,
            order["id"],
            order["amount"],
        )

        return {
            "success": True,
            "payment_status": "ORDER_CREATED",
            "agent": "PaymentAgent",
            "order": order,
        }

    except Exception as e:
        logger.exception(
            "Hotel payment order creation failed: %s",
            e,
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
            },
        )


@app.post("/api/payments/hotel/verify")
async def verify_hotel_payment_api(
    request_data: HotelPaymentVerifyRequest,
):
    """
    Deterministic Payment Verification Node.

    The LLM never decides whether payment succeeded.
    Razorpay signature + captured payment status are authoritative.
    """

    try:
        valid_signature = verify_hotel_payment(
            razorpay_order_id=request_data.razorpay_order_id,
            razorpay_payment_id=request_data.razorpay_payment_id,
            razorpay_signature=request_data.razorpay_signature,
        )

        if not valid_signature:
            logger.warning(
                "PAYMENT VERIFICATION FAILED | trip=%s | order=%s",
                request_data.trip_id,
                request_data.razorpay_order_id,
            )

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "payment_status": "VERIFICATION_FAILED",
                    "verified": False,
                    "error": "Invalid Razorpay payment signature.",
                },
            )

        payment = fetch_payment(
            request_data.razorpay_payment_id
        )

        payment_status = payment.get("status")

        if payment_status != "captured":
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "payment_status": payment_status,
                    "verified": False,
                    "error": (
                        "Payment signature is valid, "
                        "but payment is not captured."
                    ),
                },
            )

        logger.info(
            "PAYMENT VERIFIED | trip=%s | payment=%s | status=%s",
            request_data.trip_id,
            request_data.razorpay_payment_id,
            payment_status,
        )

        return {
            "success": True,
            "payment_status": "PAID",
            "verified": True,
            "agent": "PaymentVerificationNode",
            "trip_id": request_data.trip_id,
            "payment": {
                "payment_id": request_data.razorpay_payment_id,
                "order_id": request_data.razorpay_order_id,
                "status": payment_status,
                "amount": payment.get("amount"),
                "currency": payment.get("currency"),
                "method": payment.get("method"),
            },
        }

    except Exception as e:
        logger.exception(
            "Hotel payment verification failed: %s",
            e,
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "payment_status": "VERIFICATION_ERROR",
                "verified": False,
                "error": str(e),
            },
        )


@app.post("/api/trips/{trip_id}/accommodation/confirm")
async def confirm_accommodation_booking(
    trip_id: str,
    request_data: HotelBookingConfirmRequest,
):
    """
    Accommodation Booking Agent.

    Runs only after the Payment Verification Node has confirmed
    a captured Razorpay payment.
    """

    if trip_id != request_data.trip_id:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Trip ID mismatch.",
            },
        )

    try:
        hotel = request_data.hotel

        hotel_name = (
            hotel.get("name")
            or hotel.get("hotel_name")
            or hotel.get("title")
            or "Selected Hotel"
        )

        booking_id = f"HTL-{uuid.uuid4().hex[:10].upper()}"

        booking = {
            "booking_id": booking_id,
            "booking_type": "accommodation",
            "status": "CONFIRMED",
            "hotel": hotel_name,
            "hotel_details": hotel,
            "trip_id": trip_id,
            "payment": {
                "status": "PAID",
                "razorpay_order_id": request_data.razorpay_order_id,
                "razorpay_payment_id": request_data.razorpay_payment_id,
            },
        }

        logger.info(
            "BOOKING AGENT | accommodation confirmed | trip=%s | booking=%s",
            trip_id,
            booking_id,
        )

        return {
            "success": True,
            "agent": "AccommodationBookingAgent",
            "booking": booking,
            "itinerary_update": {
                "type": "accommodation",
                "title": f"Hotel confirmed: {hotel_name}",
                "description": (
                    f"{hotel_name} has been confirmed "
                    "after successful payment."
                ),
                "status": "CONFIRMED",
            },
            "message": (
                f"{hotel_name} confirmed successfully."
            ),
        }

    except Exception as e:
        logger.exception(
            "Accommodation confirmation failed: %s",
            e,
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
            },
        )


@app.post("/api/trips")
async def create_trip(request: Request, request_data: GuidedTripRequest):
    """Run the evidence-first LangGraph planner with structured user choices."""
    limited = rate_limit_response(request, "trip")
    if limited:
        return limited
    try:
        payload = request_data.model_dump(mode="json", exclude={"thread_id"})
        logger.info("request=trip_create status=started thread_id=%s destination=%s", request_data.thread_id or "new", payload.get("destination"))
        trip = await run_cancellable(request, run_trip, payload, request_data.thread_id)
        return JSONResponse(content={"success": True, "trip": trip})
    except RequestCancelled:
        return JSONResponse(status_code=499, content={"success": False, "cancelled": True, "error": "Trip research cancelled."})
    except Exception as exc:
        logger.exception("request=trip_create status=failed error=%s", exc)
        traceback.print_exc()
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})


@app.post("/api/discover")
async def discover_destinations(request: Request, request_data: DiscoveryQueryRequest):
    """Run LangGraph Multi-Agent Discovery Pipeline to find clean, ranked destination cards."""
    limited = rate_limit_response(request, "discover")
    if limited:
        return limited
    try:
        logger.info(
            "request=destination_discovery status=started origin=%s month=%s year=%s",
            request_data.origin, request_data.month, request_data.year
        )
        discovery_result = await run_cancellable(request, run_discovery,
            origin=request_data.origin.strip(),
            month=request_data.month.strip(),
            year=request_data.year,
            days=request_data.days,
            interests=request_data.interests,
            mood=request_data.mood
        )
        return JSONResponse(content={
            "success": True,
            "destinations": discovery_result["destinations"],
            "scout_summary": discovery_result["scout_summary"],
            "progress": discovery_result["progress"],
            "warnings": discovery_result["warnings"]
        })
    except RequestCancelled:
        return JSONResponse(status_code=499, content={"success": False, "cancelled": True, "error": "Destination research cancelled."})
    except Exception as exc:
        logger.exception("request=destination_discovery status=failed error=%s", exc)
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


@app.post("/api/trips/replan")
async def replan_itinerary(request: Request, request_data: ReplanPayload):
    """Run ReplanningAgent to adjust itinerary based on user input without full regeneration."""
    limited = rate_limit_response(request, "replan")
    if limited:
        return limited
    try:
        logger.info("request=trip_replan status=started trip_id=%s change=%s", request_data.trip_id, request_data.change_text)
        result = replanning_agent(
            change_text=request_data.change_text,
            current_itinerary=request_data.itinerary,
            trip_context=request_data.trip_context
        )
        return JSONResponse(content={"success": True, **result})
    except Exception as exc:
        logger.exception("request=trip_replan status=failed error=%s", exc)
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": str(exc)})


@app.get("/api/diagnostics")
async def diagnostics():
    """Report integration readiness without exposing secret values."""
    def key_state(name: str) -> str:
        value = os.getenv(name, "").strip()
        if not value:
            return "missing"
        if value.lower().startswith("your_") or value.lower() in {"change_me", "placeholder"}:
            return "placeholder"
        return "configured"

    keys = {
        "GEMINI_API_KEY": key_state("GEMINI_API_KEY"),
        "TAVILY_API_KEY": key_state("TAVILY_API_KEY"),
        "AVIATIONSTACK_API_KEY": key_state("AVIATIONSTACK_API_KEY"),
        "DATABASE_URL": key_state("DATABASE_URL"),
    }
    logger.info("request=diagnostics keys=%s", keys)
    return {
        "status": "ok",
        "keys": {name: "configured" if value else "missing" for name, value in keys.items()},
        "notes": {
            "AVIATIONSTACK_API_KEY": "Live flight status lookup.",
            "GEMINI_API_KEY": "Required for multi-agent reasoning, ranking, planning and replanning.",
            "TAVILY_API_KEY": "Required for web research, verified events, and hotel evidence."
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "TripMate AI Multi-Agent Planner is running"
    }


@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )

