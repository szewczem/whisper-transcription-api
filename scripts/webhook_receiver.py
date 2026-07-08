from fastapi import FastAPI, Request

app = FastAPI()


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, str]:
    payload = await request.json()
    print("Webhook received:", payload, flush=True)

    return {"status": "received"}
