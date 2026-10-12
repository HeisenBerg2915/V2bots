import io
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.filters_mdb import(
   add_filter,
   get_filters,
   delete_filter,
   count_filters
)

from database.connections_mdb import active_connection
from utils import get_file_id, parser, split_quotes
from info import ADMINS


@Client.on_message(filters.command(['filter', 'ad']) & filters.incoming)
async def addfilter(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return
        
    if userid not in ADMINS:
        return
        
    chat_type = message.chat.type
    args = message.text.html.split(None, 1)

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
        st.status != enums.ChatMemberStatus.ADMINISTRATOR
        and st.status != enums.ChatMemberStatus.OWNER
        and str(userid) not in ADMINS
    ):
        return

    if len(args) < 2:
        await message.reply_text("Command Incomplete :(", quote=True)
        return

    extracted = split_quotes(args[1])
    text = extracted[0].lower()

    if not message.reply_to_message and len(extracted) < 2:
        await message.reply_text("Add some content to save your filter!", quote=True)
        return

    if (len(extracted) >= 2) and not message.reply_to_message:
        reply_text, btn, alert = parser(extracted[1], text)
        fileid = None
        if not reply_text:
            await message.reply_text("You cannot have buttons alone, give some text to go with it!", quote=True)
            return

    elif message.reply_to_message and message.reply_to_message.reply_markup:
        try:
            rm = message.reply_to_message.reply_markup
            btn = rm.inline_keyboard
            msg = get_file_id(message.reply_to_message)
            if msg:
                fileid = msg.file_id
                reply_text = message.reply_to_message.caption.html
            else:
                reply_text = message.reply_to_message.text.html
                fileid = None
            alert = None
        except:
            reply_text = ""
            btn = "[]" 
            fileid = None
            alert = None

    elif message.reply_to_message and message.reply_to_message.media:
        try:
            msg = get_file_id(message.reply_to_message)
            fileid = msg.file_id if msg else None
            reply_text, btn, alert = parser(extracted[1], text) if message.reply_to_message.sticker else parser(message.reply_to_message.caption.html, text)
        except:
            reply_text = ""
            btn = "[]"
            alert = None
    elif message.reply_to_message and message.reply_to_message.text:
        try:
            fileid = None
            reply_text, btn, alert = parser(message.reply_to_message.text.html, text)
        except:
            reply_text = ""
            btn = "[]"
            alert = None
    else:
        return

    # 🟢 🛠️ തിരുത്തിയ ഭാഗം: grp_id-ക്ക് പകരം 'universal_manual_filters' എന്ന് നൽകി
    await add_filter('universal_manual_filters', text, reply_text, btn, fileid, alert)

    await message.reply_text(
        f"Filter for `{text}` added globally for **All Groups** ✅",
        quote=True,
        parse_mode=enums.ParseMode.MARKDOWN
    )


@Client.on_message(filters.command(['viewfilters', 'filters']) & filters.incoming)
async def get_all(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid or userid not in ADMINS:
        return

    # 🟢 🛠️ തിരുത്തിയ ഭാഗം: ഗ്രൂപ്പ് തിരിച്ചല്ലാതെ ആകെ ഫിൽട്ടറുകൾ ഇവിടെ ലിസ്റ്റ് ചെയ്യും
    texts = await get_filters('universal_manual_filters')
    count = await count_filters('universal_manual_filters')
    
    if count:
        filterlist = f"📊 Total Universal Filters: {count}\n\n"
        for text in texts:
            filterlist += f" × `{text}`\n"

        if len(filterlist) > 4096:
            with io.BytesIO(str.encode(filterlist.replace("`", ""))) as keyword_file:
                keyword_file.name = "universal_keywords.txt"
                await message.reply_document(document=keyword_file, quote=True)
            return
    else:
        filterlist = "There are no active filters found!"

    await message.reply_text(text=filterlist, quote=True, parse_mode=enums.ParseMode.MARKDOWN)
        
        
@Client.on_message(filters.command('delf') & filters.incoming)
async def deletefilter(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid or userid not in ADMINS:
        return

    try:
        cmd, text = message.text.split(" ", 1)
    except:
        await message.reply_text(
            "<code>/delf filtername</code>\n\nUse /viewfilters to view all available filters",
            quote=True
        )
        return

    query = text.lower().strip()

    try:
        # 🟢 🛠️ തിരുത്തിയ ഭാഗം: 'universal_manual_filters' കീയിൽ നിന്ന് ഡിലീറ്റ് ചെയ്യുന്നു
        success = await delete_filter('universal_manual_filters', query)
        
        if success:
            await message.reply_text(
                f"Global Filter `{query}` deleted successfully!",
                quote=True,
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await message.reply_text(
                f"Filter `{query}` not found!",
                quote=True,
                parse_mode=enums.ParseMode.MARKDOWN
            )
    except Exception as e:
        await message.reply_text(f"An error occurred: `{e}`", quote=True, parse_mode=enums.ParseMode.MARKDOWN)

        
@Client.on_message(filters.command('delallf') & filters.incoming)
async def delallconfirm(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid or userid not in ADMINS:
        return
        
    await message.reply_text(
        "This will delete **ALL FILTERS** from the bot database.\nDo you want to continue??",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text="YES, DELETE ALL", callback_data="delallconfirm")],
            [InlineKeyboardButton(text="CANCEL", callback_data="delallcancel")]
        ]),
        quote=True
    )
