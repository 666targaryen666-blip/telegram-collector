from collector.db import connect, get_cursor, store_batch

def test_dedup_and_cursor(tmp_path):
    conn = connect(tmp_path/'test.sqlite3')
    row = dict(source='example',message_id=5,author='@example',url='https://t.me/example/5',date='2026-01-01T00:00:00+00:00',text='hello',media_type=None)
    assert get_cursor(conn,'example')[0] == 0
    assert store_batch(conn,'example',[row],'new',5) == 1
    assert store_batch(conn,'example',[row],'new',5) == 0
    assert get_cursor(conn,'example')[0] == 5
    assert conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0] == 1
    conn.close()

def test_backfill_cursor(tmp_path):
    conn = connect(tmp_path/'test.sqlite3')
    get_cursor(conn,'example')
    store_batch(conn,'example',[],'backfill',100,False)
    assert get_cursor(conn,'example') == (0,100,0)
    store_batch(conn,'example',[],'backfill',None,True)
    assert get_cursor(conn,'example')[2] == 1
