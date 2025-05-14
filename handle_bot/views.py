from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import asyncio

from telegram import Update
from telegram.ext import Application

from .codewars_bot.bot import handler
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
