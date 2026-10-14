import httpx
import logging
from database import db_manager

logger = logging.getLogger(__name__)

EXCHANGE_API_URL = "https://open.er-api.com/v6/latest/USD"

async def fetch_and_update_exchange_rates():
    """
    Fetches live USD exchange rates from open API and updates DB for currencies
    unless an admin has set a manual override (`is_manual = 1`).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(EXCHANGE_API_URL)
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})

                db_rates = await db_manager.get_exchange_rates()

                # Supported target currencies
                target_currencies = ['IQD', 'GEL', 'TJS', 'AFN', 'IRR']

                for curr in target_currencies:
                    existing = db_rates.get(curr, {})
                    # If manually overridden by admin, preserve manual rate unless reset
                    if existing.get('is_manual') == 1:
                        logger.info(f"Preserving manual exchange rate for {curr}: {existing.get('rate_to_usd')}")
                        continue

                    if curr in rates:
                        live_rate = float(rates[curr])
                        await db_manager.set_exchange_rate(curr, live_rate, is_manual=0)
                        logger.info(f"Updated live exchange rate for {curr}: {live_rate}")
                    elif curr == 'IRR':
                        # Fallback default estimate if IRR not in er-api
                        if 'IRR' not in existing:
                            await db_manager.set_exchange_rate('IRR', 650000.0, is_manual=0)

                logger.info("Automatic exchange rate update completed.")
            else:
                logger.warning(f"Failed to fetch exchange rates, status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching live exchange rates: {e}")
