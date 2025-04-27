import os
import asyncio
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Khởi tạo các biến toàn cục
total_profit = 0
total_spending = 0
current_day = None
waiting_for_expense = False

def clean_number(number_str):
    return int(re.sub(r'[^\d]', '', number_str))

def save_daily_report():
    with open("daily_report.txt", "w", encoding="utf-8") as f:
        f.write(f"{total_profit},{total_spending},{current_day}")

def load_daily_report():
    global total_profit, total_spending, current_day
    if os.path.exists("daily_report.txt"):
        with open("daily_report.txt", "r", encoding="utf-8") as f:
            data = f.read().split(",")
            if len(data) == 3:
                total_profit, total_spending, current_day = int(data[0]), int(data[1]), data[2]

def save_history(text):
    with open("history.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

def load_history():
    if os.path.exists("history.txt"):
        with open("history.txt", "r", encoding="utf-8") as f:
            return f.readlines()
    return []

def is_date(text):
    return bool(re.match(r"^\d{1,2}/\d{1,2}$", text.strip()))

async def send_header(update: Update):
    today = datetime.now().strftime("%d/%m/%Y")
    hup = total_profit  # tổng lãi hiện tại (dù âm hay dương)
    
    await update.message.reply_text(
        f"""<b>✨✨✨ CHÚC ÔNG CHỦ MAY MẮN NHÉ ✨✨✨</b>\n
<b>🎲 Baccarat Sexy 🎲</b>\n
📅 <b>Ngày hôm nay:</b> {today}\n
💰 <b>Tổng lãi hiện tại:</b> {hup}\n
🛒 <b>Chi tiêu:</b> (vui lòng nhập hoặc đã nhập)\n
\n🥇 <b>Bùi Hữu Thướng - gnouht6.six mãi đỉnh!!!</b>""",
        parse_mode="HTML"
    )

async def send_full_report(update: Update):
    history = load_history()
    profits = []
    spendings = []
    days = []
    current_profit = 0
    current_spending = 0
    current_day_local = None

    for line in history:
        line = line.strip()
        if is_date(line):
            if current_day_local and (current_profit or current_spending):
                profits.append(current_profit)
                spendings.append(current_spending)
                days.append(current_day_local)
            current_day_local = line
            current_profit = 0
            current_spending = 0
        elif "lãi" in line:
            current_profit += clean_number(line)
        elif "vốn" in line:
            current_spending += clean_number(line)

    if current_day_local and (current_profit or current_spending):
        profits.append(current_profit)
        spendings.append(current_spending)
        days.append(current_day_local)

    report = "📋 Tổng hợp báo cáo:\n\n"
    for d, p, s in zip(days, profits, spendings):
        report += f"📅 {d}: +{p} / vốn {s}\n"

    await update.message.reply_text(report)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_profit, total_spending, current_day, waiting_for_expense

    await send_header(update)

    text = update.message.text.strip()
    save_history(text)

    if waiting_for_expense:
        try:
            expense = clean_number(text)
            hup = total_profit - expense
            await update.message.reply_text(
                f"✅ Đã ghi nhận chi tiêu: {expense}\n\n🍗 Húp (lãi - chi tiêu): {hup}"
            )
            waiting_for_expense = False
        except ValueError:
            await update.message.reply_text("❗ Vui lòng nhập số tiền chi tiêu hợp lệ.")
        return

    if is_date(text):
        current_day = text
        await update.message.reply_text(f"📅 Bắt đầu ngày mới: {current_day}")
        return

    if "lãi" in text:
        amount = clean_number(text)
        total_profit += amount
        await update.message.reply_text(f"💰 Đã cộng lãi: +{amount}\nTổng lãi: {total_profit}")
        save_daily_report()

    elif "vốn" in text:
        amount = clean_number(text)
        total_spending += amount
        await update.message.reply_text(f"🛍️ Đã cộng vốn: {amount}\nTổng vốn: {total_spending}")
        save_daily_report()

    elif text.lower() == "xem":
        await send_full_report(update)

async def tong_ngay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_header(update)

    if total_spending == 0:
        await update.message.reply_text("❗ Chưa có vốn ghi nhận hôm nay.")
        return
    percent = round(total_profit / total_spending * 100, 2)
    await update.message.reply_text(
        f"📅 Ngày {current_day}:\nLãi: {total_profit}\nVốn: {total_spending}\nTỉ lệ lãi: {percent}%"
    )

async def tong10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_header(update)

    history = load_history()[-10:]
    profit = 0
    spending = 0

    for line in history:
        line = line.strip()
        if "lãi" in line:
            profit += clean_number(line)
        elif "vốn" in line:
            spending += clean_number(line)

    if spending == 0:
        await update.message.reply_text("❗ Không có vốn trong 10 dòng cuối.")
        return

    percent = round(profit / spending * 100, 2)
    await update.message.reply_text(
        f"🔟 Tổng 10 dòng cuối:\nLãi: {profit}\nVốn: {spending}\nTỉ lệ lãi: {percent}%"
    )

async def tong30(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_header(update)

    history = load_history()[-30:]
    profit = 0
    spending = 0

    for line in history:
        line = line.strip()
        if "lãi" in line:
            profit += clean_number(line)
        elif "vốn" in line:
            spending += clean_number(line)

    if spending == 0:
        await update.message.reply_text("❗ Không có vốn trong 30 dòng cuối.")
        return

    percent = round(profit / spending * 100, 2)
    await update.message.reply_text(
        f"3⃣0⃣ Tổng 30 dòng cuối:\nLãi: {profit}\nVốn: {spending}\nTỉ lệ lãi: {percent}%"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_expense
    waiting_for_expense = True
    await send_header(update)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_profit, total_spending, current_day
    total_profit = 0
    total_spending = 0
    current_day = None
    if os.path.exists("history.txt"):
        os.remove("history.txt")
    if os.path.exists("daily_report.txt"):
        os.remove("daily_report.txt")
    await send_header(update)
    await update.message.reply_text("✅ Đã reset toàn bộ dữ liệu.")

def main():
    load_daily_report()

    app = ApplicationBuilder().token('TOKEN_CUA_BAN').build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('tong10', tong10))
    app.add_handler(CommandHandler('tong30', tong30))
    app.add_handler(CommandHandler('reset', reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot đã chạy thành công!")
    app.run_polling()

if __name__ == '__main__':
    import sys
    if sys.platform.startswith('win') and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    main()
