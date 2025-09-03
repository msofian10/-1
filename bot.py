import sqlite3
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# تعريف حالات المحادثة
AGE, HOURS, LOCATION, SALARY, DETAILS = range(5)

# إنشاء قاعدة البيانات
def init_db():
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age_min INTEGER,
            age_max INTEGER,
            hours INTEGER,
            location TEXT,
            salary INTEGER,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['إضافة وظيفة', 'عرض الوظائف'],
        ['البحث عن وظائف', 'مساعدة']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'مرحباً! اختر أحد الخيارات:',
        reply_markup=reply_markup
    )

# إضافة وظيفة جديدة
async def add_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'أدنى عمر مقبول:',
        reply_markup=ReplyKeyboardRemove()
    )
    return AGE

async def age_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age_min'] = update.message.text
    await update.message.reply_text('أعلى عمر مقبول:')
    return HOURS

async def hours_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age_max'] = update.message.text
    await update.message.reply_text('عدد ساعات العمل:')
    return LOCATION

async def location_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['hours'] = update.message.text
    await update.message.reply_text('المكان:')
    return SALARY

async def salary_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['location'] = update.message.text
    await update.message.reply_text('الراتب:')
    return DETAILS

async def details_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['salary'] = update.message.text
    await update.message.reply_text('تفاصيل إضافية:')
    return ConversationHandler.END

async def save_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['details'] = update.message.text
    
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO jobs (age_min, age_max, hours, location, salary, details)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        context.user_data['age_min'],
        context.user_data['age_max'],
        context.user_data['hours'],
        context.user_data['location'],
        context.user_data['salary'],
        context.user_data['details']
    ))
    conn.commit()
    conn.close()
    
    await update.message.reply_text('تم حفظ الوظيفة بنجاح!')
    return ConversationHandler.END

# عرض الوظائف
async def show_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jobs')
    jobs = cursor.fetchall()
    conn.close()
    
    if not jobs:
        await update.message.reply_text('لا توجد وظائف متاحة حالياً.')
    else:
        for job in jobs:
            message = (
                f"🏢 **الوظيفة #{job[0]}**\n"
                f"🎯 **العمر:** {job[1]} - {job[2]} سنة\n"
                f"⏰ **ساعات العمل:** {job[3]} ساعة\n"
                f"📍 **المكان:** {job[4]}\n"
                f"💰 **الراتب:** {job[5]} جنيه\n"
                f"📝 **التفاصيل:** {job[6]}\n"
                f"─────────────────"
            )
            await update.message.reply_text(message, parse_mode='Markdown')

# حذف وظيفة
async def delete_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        job_id = int(context.args[0]) if context.args else None
        if job_id:
            conn = sqlite3.connect('jobs.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
            conn.commit()
            conn.close()
            await update.message.reply_text(f'تم حذف الوظيفة #{job_id}')
        else:
            await update.message.reply_text('يرجى تحديد رقم الوظيفة\nمثال: /delete 1')
    except:
        await update.message.reply_text('خطأ في حذف الوظيفة')

# البحث عن وظائف في مكان معين
async def filter_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = ' '.join(context.args) if context.args else None
    if location:
        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE location LIKE ?', (f'%{location}%',))
        jobs = cursor.fetchall()
        conn.close()
        
        if not jobs:
            await update.message.reply_text(f'لا توجد وظائف في {location}')
        else:
            for job in jobs:
                message = (
                    f"🏢 **الوظيفة #{job[0]}**\n"
                    f"🎯 **العمر:** {job[1]} - {job[2]} سنة\n"
                    f"⏰ **ساعات العمل:** {job[3]} ساعة\n"
                    f"📍 **المكان:** {job[4]}\n"
                    f"💰 **الراتب:** {job[5]} جنيه\n"
                    f"📝 **التفاصيل:** {job[6]}\n"
                    f"─────────────────"
                )
                await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text('يرجى تحديد المكان\nمثال: /filter القاهرة')

# مساعدة
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🎯 **أوامر البوت:**\n\n"
        "• /start - بدء البوت وعرض القائمة الرئيسية\n"
        "• /delete [رقم] - حذف وظيفة (مثال: /delete 1)\n"
        "• /filter [مكان] - البحث عن وظائف في مكان معين\n"
        "• /help - عرض هذه الرسالة\n\n"
        "💡 **طريقة الاستخدام:**\n"
        "1. اضغط على 'إضافة وظيفة' لإدخال بيانات الوظيفة\n"
        "2. اضغط على 'عرض الوظائف' لرؤية جميع الوظائف\n"
        "3. استخدم 'البحث عن وظائف' للبحث في مكان معين"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# الرئيسية
def main():
    init_db()
    application = Application.builder().token(os.environ['BOT_TOKEN']).build()
    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(إضافة وظيفة)$'), add_job)],
        states={
            AGE: [MessageHandler(filters.TEXT, age_input)],
            HOURS: [MessageHandler(filters.TEXT, hours_input)],
            LOCATION: [MessageHandler(filters.TEXT, location_input)],
            SALARY: [MessageHandler(filters.TEXT, salary_input)],
            DETAILS: [MessageHandler(filters.TEXT, save_job)]
        },
        fallbacks=[]
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("delete", delete_job))
    application.add_handler(CommandHandler("filter", filter_jobs))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Regex('^(عرض الوظائف)$'), show_jobs))
    application.add_handler(MessageHandler(filters.Regex('^(مساعدة)$'), help_command))
    
    application.run_polling()

if __name__ == "__main__":
    main()