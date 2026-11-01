import os
import sqlite3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(page_title='Telegram Collector', layout='wide')
st.title('Telegram Collector — статистика')
path = os.getenv('DATABASE_PATH', 'data/collector.sqlite')
if not os.path.exists(path):
    st.info('Run the collector first to create the SQLite database.')
    st.stop()
conn = sqlite3.connect(path)
try:
    total = pd.read_sql_query('SELECT COUNT(*) AS total FROM messages',conn).iloc[0]['total']
    channels = pd.read_sql_query('SELECT COUNT(DISTINCT source) AS n FROM messages',conn).iloc[0]['n']
    runs = pd.read_sql_query('SELECT COUNT(*) AS n FROM runs',conn).iloc[0]['n']
    a,b,c = st.columns(3)
    a.metric('Повідомлення',int(total)); b.metric('Канали',int(channels)); c.metric('Прогони',int(runs))
    st.subheader('Повідомлення за каналами')
    st.bar_chart(pd.read_sql_query('SELECT source,COUNT(*) AS count FROM messages GROUP BY source',conn).set_index('source'))
    st.subheader('Журнал запусків')
    st.dataframe(pd.read_sql_query('SELECT * FROM runs ORDER BY id DESC LIMIT 100',conn),use_container_width=True)
    st.subheader('Останні повідомлення')
    st.dataframe(pd.read_sql_query('SELECT author,url,date,text FROM messages ORDER BY date DESC LIMIT 50',conn),use_container_width=True)
finally:
    conn.close()
