import argparse
import asyncio
import csv
import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse, unquote

from dotenv import load_dotenv
from telethon import TelegramClient, errors
from telethon.tl.types import Channel
from collector.db import connect, get_cursor, store_batch

LOG = logging.getLogger('collector')

def config():
    load_dotenv()
    return {
        'api_id': os.getenv('TELEGRAM_API_ID', ''),
        'api_hash': os.getenv('TELEGRAM_API_HASH', ''),
        'session': os.getenv('TELEGRAM_SESSION', 'collector_session'),
        'channels': [x.strip().lstrip('@') for x in os.getenv('CHANNELS', 'durov,telegram').split(',') if x.strip()],
        'db': os.getenv('DATABASE_PATH', 'data/messages.sqlite3'),
        'batch': max(1, min(int(os.getenv('BATCH_SIZE', '100')), 500)),
        'delay': max(1.0, float(os.getenv('REQUEST_DELAY_SECONDS', '2'))),
        'max_wait': int(os.getenv('MAX_FLOOD_WAIT_SECONDS', '900')),
        'proxy': os.getenv('PROXY_URL', ''),
    }

def parse_proxy(url):
    if not url:
        return None
    import socks
    u = urlparse(url)
    kinds = {'socks5': socks.SOCKS5, 'socks4': socks.SOCKS4, 'http': socks.HTTP}
    if u.scheme not in kinds or not u.hostname or not u.port:
        raise ValueError('PROXY_URL must be socks5://host:port or http://host:port')
    return (kinds[u.scheme], u.hostname, u.port, True, unquote(u.username) if u.username else None,
            unquote(u.password) if u.password else None)

def canonical(channel, msg):
    username = channel.username
    return {
        'source': username.lower(),
        'message_id': msg.id,
        'author': f'@{username}',
        'url': f'https://t.me/{username}/{msg.id}',
        'date': msg.date.isoformat(),
        'text': msg.message or '',
        'media_type': type(msg.media).__name__ if msg.media else None,
    }

async def fetch(client, entity, mode, cursor, limit, delay):
    records = []
    kwargs = {'limit': limit, 'wait_time': delay}
    if mode == 'new':
        kwargs['min_id'] = cursor[0]
        kwargs['reverse'] = True
    else:
        if cursor[2]:
            return [], None, True
        if cursor[1] is not None:
            kwargs['max_id'] = cursor[1]
    async for msg in client.iter_messages(entity, **kwargs):
        records.append(canonical(entity, msg))
    if mode == 'new':
        return records, max((r['message_id'] for r in records), default=None), False
    next_id = min((r['message_id'] for r in records), default=None)
    return records, next_id, len(records) < limit

async def collect(args, cfg):
    if not cfg['api_id'] or not cfg['api_hash']:
        raise SystemExit('Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env (see README).')
    conn = connect(cfg['db'])
    client = TelegramClient(cfg['session'], int(cfg['api_id']), cfg['api_hash'],
                            proxy=parse_proxy(cfg['proxy']), flood_sleep_threshold=0,
                            request_retries=2)
    try:
        await client.start()
        for source in cfg['channels']:
            try:
                entity = await client.get_entity(source)
                if not isinstance(entity, Channel) or not entity.username:
                    LOG.warning('Skipping %s: public channel username required', source)
                    continue
                key = entity.username.lower()
                cursor = get_cursor(conn, key)
                if args.mode == 'backfill' and cursor[0] == 0:
                    LOG.warning('Run collect first to establish the latest cursor for %s', key)
                    continue
                records, next_id, complete = await fetch(client, entity, args.mode, cursor, args.limit or cfg['batch'], cfg['delay'])
                inserted = store_batch(conn, key, records, args.mode, next_id, complete)
                LOG.info('%s mode=%s fetched=%d inserted=%d cursor=%s complete=%s', key,args.mode,len(records),inserted,next_id,complete)
            except errors.FloodWaitError as exc:
                LOG.warning('FloodWait source=%s seconds=%s; stopping requests to respect limit', source, exc.seconds)
                with conn:
                    conn.execute('INSERT INTO runs(source,mode,inserted,status,detail) VALUES (?,?,?,?,?)',
                                 (source,args.mode,0,'rate_limited',f'FloodWait {exc.seconds}s'))
                # Do not rotate accounts or bypass Telegram flood restrictions.
            except Exception as exc:
                LOG.exception('Source %s failed: %s', source, exc)
                with conn:
                    conn.execute('INSERT INTO runs(source,mode,inserted,status,detail) VALUES (?,?,?,?,?)',
                                 (source,args.mode,0,'error',str(exc)[:500]))
            await asyncio.sleep(cfg['delay'])
    finally:
        await client.disconnect()
        conn.close()

def export(cfg, output):
    conn = connect(cfg['db'])
    rows = conn.execute('SELECT author,url,date,text,media_type,source,message_id FROM messages ORDER BY date,url').fetchall()
    columns = ['author','url','date','text','media_type','source','message_id']
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, 'w', encoding='utf-8', newline='') as f:
        if output.endswith('.csv'):
            w = csv.writer(f); w.writerow(columns); w.writerows(rows)
        else:
            for row in rows:
                f.write(json.dumps(dict(zip(columns,row)),ensure_ascii=False)+'\n')
    print(f'Exported {len(rows)} records to {output}')
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Incremental public Telegram channel collector')
    parser.add_argument('command', choices=['collect','backfill','export'])
    parser.add_argument('--limit', type=int, default=None, help='max records per channel per run')
    parser.add_argument('--output', default='data/messages.jsonl')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.StreamHandler()])
    cfg = config()
    if args.command == 'export':
        export(cfg,args.output)
    else:
        args.mode = 'new' if args.command == 'collect' else 'backfill'
        asyncio.run(collect(args,cfg))

if __name__ == '__main__':
    main()
