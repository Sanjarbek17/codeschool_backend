from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import asyncio
import requests

from telegram import Update
from telegram.ext import Application

from .codewars_bot.main import handler
from .codewars_bot.config import TELEGRAM_BOT_TOKEN

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
application = handler(application)


@csrf_exempt
async def webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            update = Update.de_json(data, application.bot)

            # Process Update
            await application.process_update(update)

            return HttpResponse("OK")
        except Exception as e:
            return HttpResponse(str(e), status=500)
    return HttpResponseForbidden()


def set_webhook(request):
    """View to set up the Telegram webhook"""
    try:
        # Get your domain from the request
        domain = request.get_host()
        protocol = "https" if request.is_secure() else "http"
        webhook_url = f"{protocol}://{domain}/bot/webhook/"

        # Telegram API endpoint for setting webhook
        api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"

        # Set the webhook
        response = requests.post(api_url, json={"url": webhook_url})

        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Webhook set to {webhook_url}",
                        "result": result,
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f'Telegram API Error: {result.get("description")}',
                        "result": result,
                    },
                    status=400,
                )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"HTTP Error: {response.status_code}",
                    "response": response.text,
                },
                status=400,
            )

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)
