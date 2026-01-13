import warnings
import logging
import os

warnings.filterwarnings('ignore')

logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.scriptrunner_utils').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.caching').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)

os.environ['STREAMLIT_SERVER_RUN_ON_SAVE'] = 'false'
