import logging
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# MongoDB കണക്ഷൻ സെറ്റ് ചെയ്യുന്നു
myclient = AsyncIOMotorClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]
mycol = mydb['filters'] 

async def init_filters_db():
    """യൂണിവേഴ്സൽ ഫിൽറ്ററുകൾ വേഗത്തിൽ തപ്പിയെടുക്കാൻ ഇൻഡക്സ് സെറ്റ് ചെയ്യുന്നു 🚀"""
    try:
        await mycol.create_index([("group_id", 1), ("text", 1)], unique=True)
    except Exception as e:
        logger.error(f"Error creating filters database index: {e}")

async def add_filter(grp_id, text, reply_text, btn, file, alert):
    """എല്ലാ ഗ്രൂപ്പുകൾക്കും പൊതുവായി ഫിൽറ്ററുകൾ ഡാറ്റാബേസിൽ അപ്‌ഡേറ്റ് ചെയ്യുകയോ ആഡ് ചെയ്യുകയോ ചെയ്യുന്നു."""
    data = {
        'group_id': str(grp_id),
        'text': str(text).lower().strip(),
        'reply_text': str(reply_text), # ഫീൽഡ് നെയിം കറക്റ്റ് ചെയ്തു
        'btn': str(btn),
        'fileid': str(file), # ഫീൽഡ് നെയിം കറക്റ്റ് ചെയ്തു
        'alert': str(alert)
    }
    try:
        await mycol.update_one(
            {'group_id': str(grp_id), 'text': str(text).lower().strip()}, 
            {"$set": data}, 
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f'Error occurred while adding filter to database: {e}')
        return False
             
async def find_filter(group_id, name):
    """Universal ഫിൽറ്ററുകളിൽ നിന്ന് കീവേഡ് മാച്ച് ഉള്ള ഡാറ്റ കണ്ടുപിടിച്ച് നൽകുന്നു."""
    try:
        file = await mycol.find_one({"group_id": str(group_id), "text": str(name).lower().strip()})
        if file:
            # നിങ്ങളുടെ pm_filter ഫയലുമായി മാച്ച് ചെയ്യാൻ ഫീൽഡ് പേരുകൾ കൃത്യമായി റിട്ടേൺ ചെയ്യുന്നു
            return file.get('reply_text'), file.get('btn'), file.get('alert', None), file.get('fileid')
    except Exception as e:
        logger.error(f"Error finding filter: {e}")
    return None, None, None, None

async def get_filters(group_id):
    """ഡാറ്റാബേസിലുള്ള മുഴുവൻ മാനുവൽ ഫിൽറ്ററുകളുടെയും കീവേഡ് ലിസ്റ്റ് എടുക്കുന്നു."""
    texts = []
    try:
        cursor = mycol.find({"group_id": str(group_id)})
        async for file in cursor:
            texts.append(file['text'])
    except Exception as e:
        logger.error(f"Error fetching filters list: {e}")
    return texts

async def delete_filter(group_id, text):
    """ഡാറ്റാബേസിൽ നിന്ന് ഒരു പ്രത്യേക ഫിൽറ്റ റൂൾ നീക്കം ചെയ്യുന്നു."""
    myquery = {'group_id': str(group_id), 'text': str(text).lower().strip()}
    count = await mycol.count_documents(myquery)
    if count >= 1:
        await mycol.delete_one(myquery)
        return True
    return False

async def del_all(group_id):
    """ഡാറ്റാബേസിലുള്ള മുഴുവൻ യൂണിവേഴ്സൽ ഫിൽറ്ററുകളും ഒറ്റയടിക്ക് ക്ലിയർ ചെയ്യുന്നു."""
    myquery = {'group_id': str(group_id)}
    count = await mycol.count_documents(myquery)
    if count == 0:
        return False
    try:
        await mycol.delete_many(myquery)
        return True
    except Exception as e:
        logger.error(f"Error clearing universal filters: {e}")
        return False

async def count_filters(group_id):
    """ആകെ ആക്ടീവ് ആയിട്ടുള്ള യൂണിവേഴ്സൽ ഫിൽറ്ററുകളുടെ എണ്ണം റിട്ടേൺ ചെയ്യുന്നു."""
    count = await mycol.count_documents({'group_id': str(group_id)})
    return False if count == 0 else count

async def filter_stats():
    """സ്റ്റാറ്റ്സ് പാനലിന് വേണ്ടി ആകെ ഫിൽറ്ററുകളുടെ കൗണ്ട് കണക്കാക്കുന്നു."""
    try:
        totalcount = await mycol.count_documents({})
        totalcollections = len(await mycol.distinct("group_id"))
        return totalcollections, totalcount
    except Exception as e:
        logger.error(f"Error building filter stats: {e}")
        return 0, 0
