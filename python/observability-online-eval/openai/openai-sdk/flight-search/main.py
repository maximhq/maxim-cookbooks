import http.client
import os
from typing import Optional

from openai import OpenAI

open_ai_api_key = os.getenv("OPENAI_API_KEY")
rapid_api_key = os.getenv("RAPID_API_KEY")
booking_com_host = os.getenv("BOOKING_COM_HOST")


def booking_com_search(
    depart_date: str,
    from_id: str,
    to_id: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    cabinClass: str = "ECONOMY",
    currency_code: str = "USD",
) -> str:
    conn = http.client.HTTPSConnection(booking_com_host)

    headers = {"x-rapidapi-key": rapid_api_key, "x-rapidapi-host": booking_com_host}

    conn.request(
        "GET",
        f"/api/v1/flights/searchFlights?fromId={from_id}&toId={to_id}&departDate={depart_date}&returnDate={return_date}&pageNo=1&adults={adults}&children={children}&sort=BEST&cabinClass={cabinClass}&currency_code={currency_code}",
        headers=headers,
    )

    res = conn.getresponse()
    data = res.read()
    return data.decode("utf-8")


def model_call():
    pass


def main():
    print("start")


if __name__ == "__main__":
    main()
