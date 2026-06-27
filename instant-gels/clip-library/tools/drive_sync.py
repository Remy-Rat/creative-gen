#!/usr/bin/env python3
"""List or download Instant Gels footage from Google Drive.

Usage:
    python3 drive_sync.py list                 # whole shared folder summary
    python3 drive_sync.py list "09_Instant"    # summary of a named subfolder
    python3 drive_sync.py pull "09_Instant"    # parallel download into raw/

Downloads run with multiple workers, write to a .part temp then atomically rename,
and skip files already complete (resume-safe). Paths in raw/ are relative to the
targeted folder. Uses the user's legacy gcloud Drive creds (see ~/.claude/CLAUDE.md).
"""
import os
import sys
import pathlib
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

CREDS = '/Users/remy-m4/.config/gcloud/legacy_credentials/remy@glamrdip.com/adc.json'
FOLDER_ID = '1BqljYOf8OEvebiywA2Z2lLeO9ZtKRBfd'
DEST = pathlib.Path('/Users/remy-m4/Desktop/Video-ad-test/instant-gels/clip-library/raw')
WORKERS = int(os.environ.get('DRIVE_WORKERS', '6'))
SCOPES = ['https://www.googleapis.com/auth/drive']

_local = threading.local()


def get_creds():
    c = Credentials.from_authorized_user_file(CREDS, scopes=SCOPES)
    c.refresh(Request())
    return c


def svc(creds=None):
    return build('drive', 'v3', credentials=creds or get_creds(), cache_discovery=False)


def tsvc(creds):
    """One Drive service per thread (httplib2 transport is not thread-safe)."""
    if not hasattr(_local, 's'):
        _local.s = build('drive', 'v3', credentials=creds, cache_discovery=False)
    return _local.s


def walk(s, fid, prefix=''):
    items, page = [], None
    while True:
        r = s.files().list(
            q=f"'{fid}' in parents and trashed=false",
            fields="nextPageToken, files(id,name,mimeType,size)",
            pageSize=1000, pageToken=page,
            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        for f in r.get('files', []):
            rel = f"{prefix}{f['name']}"
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                items += walk(s, f['id'], rel + '/')
            else:
                items.append({'id': f['id'], 'path': rel, 'mime': f['mimeType'],
                              'size': int(f.get('size', 0) or 0)})
        page = r.get('nextPageToken')
        if not page:
            break
    return items


def human(n):
    n = float(n)
    for u in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"


def resolve(s, name_filter):
    r = s.files().list(
        q=(f"'{FOLDER_ID}' in parents and trashed=false "
           "and mimeType='application/vnd.google-apps.folder'"),
        fields="files(id,name)", supportsAllDrives=True,
        includeItemsFromAllDrives=True).execute()
    for f in r.get('files', []):
        if name_filter.lower() in f['name'].lower():
            return f['id'], f['name']
    sys.exit(f"No subfolder matching {name_filter!r}")


def download_one(creds, f, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + '.part')
    req = tsvc(creds).files().get_media(fileId=f['id'], supportsAllDrives=True)
    with open(tmp, 'wb') as fh:
        dl = MediaIoBaseDownload(fh, req, chunksize=16 * 1024 * 1024)
        done = False
        while not done:
            _, done = dl.next_chunk()
    tmp.replace(dest)   # atomic: a complete file never appears partial
    return f


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    cmd = args[0] if args else 'list'
    name_filter = args[1] if len(args) > 1 else None
    creds = get_creds()
    s = svc(creds)
    target_id = FOLDER_ID
    if name_filter:
        target_id, target_name = resolve(s, name_filter)
        print(f"target folder: {target_name}")
    files = walk(s, target_id)
    total = sum(f['size'] for f in files)
    vids = [f for f in files if f['mime'].startswith('video')
            or f['path'].lower().endswith(('.mp4', '.mov', '.m4v', '.webm', '.avi'))]
    print(f"{len(files)} files | {len(vids)} videos | total {human(total)}")
    by = defaultdict(lambda: [0, 0])
    for f in files:
        top = f['path'].split('/')[0] if '/' in f['path'] else '(root)'
        by[top][0] += 1
        by[top][1] += f['size']
    for k in sorted(by):
        print(f"  {k}: {by[k][0]} files, {human(by[k][1])}")

    if cmd == 'pull':
        DEST.mkdir(parents=True, exist_ok=True)
        todo = []
        for f in files:
            dest = DEST / f['path']
            if dest.exists() and f['size'] and dest.stat().st_size == f['size']:
                continue
            todo.append((f, dest))
        print(f"{len(files) - len(todo)} already complete | {len(todo)} to fetch "
              f"with {WORKERS} workers", flush=True)
        ok = err = 0
        lock = threading.Lock()
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(download_one, creds, f, dest): f for f, dest in todo}
            for fut in as_completed(futs):
                f = futs[fut]
                try:
                    fut.result()
                    with lock:
                        ok += 1
                        print(f"  [{ok}/{len(todo)}] {f['path']} ({human(f['size'])})", flush=True)
                except Exception as e:
                    with lock:
                        err += 1
                        print(f"  ERR {f['path']}: {e}", flush=True)
        print(f"done: {ok} downloaded, {err} errors -> {DEST}")


if __name__ == '__main__':
    main()
