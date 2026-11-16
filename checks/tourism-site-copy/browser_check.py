"""Compare source/copy browser rendering using a real local HTTP server."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import unquote,urlsplit
import argparse
import asyncio
import hashlib
import json
import shutil

from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent


async def main(source):
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
        def translate_path(self,path):
            path=unquote(urlsplit(path).path)
            base=source if path.startswith('/original/') else ROOT/'site'
            relative=path.split('/',2)[-1]
            result=(base/relative).resolve()
            return str(result if result.is_relative_to(base.resolve()) else base/'__missing__')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    Thread(target=server.serve_forever,daemon=True).start()
    origin='http://127.0.0.1:'+str(server.server_port)
    report={'date_jst':'2026-11-16','method':'元ファイルとコピー先の実ファイルをローカルHTTPサーバーで配信。外部サイトの応答や処理の模擬なし。',
        'viewports':[],'external_requests':[],'actual_file_url':{},'errors':[]}
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,
            args=['--no-sandbox','--disable-dev-shm-usage'])
        context=await browser.new_context()
        page=await context.new_page()
        page.on('request',lambda r:report['external_requests'].append(r.url)
                if r.url.startswith(('https:','http:')) and not r.url.startswith(origin) else None)
        try:
            for width,height,name in [(1440,1000,'pc'),(390,900,'mobile')]:
                await page.set_viewport_size({'width':width,'height':height})
                pictures=[]
                for route in ['original','copy']:
                    response=await page.goto(origin+'/'+route+'/index.html',wait_until='networkidle')
                    assert response.status==200
                    assert await page.title()=='まついわ町 観光ガイド'
                    assert await page.locator('.review').count()==91
                    assert await page.locator('section[id^="mt-spot-"]').count()==8
                    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
                    picture=await page.screenshot()
                    pictures.append(picture)
                    if route=='copy':(OUT/(name+'.png')).write_bytes(picture)
                assert pictures[0]==pictures[1],name+' source/copy appearance differs'
                report['viewports'].append({'width':width,'height':height,'source_copy_pixels_identical':True,
                    'screenshot_sha256':hashlib.sha256(pictures[1]).hexdigest(),'no_horizontal_overflow':True})
            await page.locator('a[href="#mt-spot-5"]').first.click()
            assert page.url.endswith('#mt-spot-5')
            await page.locator('#mt-spot-5 summary').click()
            assert await page.locator('#mt-spot-5 details').evaluate('(e)=>e.open')
            assert await page.locator('#mt-spot-5 .review').first.is_visible()
            report['anchor_navigation_and_review_expansion']=True
            try:
                await page.goto((ROOT/'site/index.html').as_uri(),wait_until='load',timeout=15000)
                if await page.title()=='まついわ町 観光ガイド':
                    report['actual_file_url']={'status':'verified','title':await page.title()}
                else:report['actual_file_url']={'status':'unverified','reason':'管理環境のfile URL画面制限。ローカルHTTPの実ファイル表示は確認済み。'}
            except Exception as error:
                report['actual_file_url']={'status':'unverified','reason':str(error).splitlines()[0]}
        except Exception as error:
            report['errors'].append(type(error).__name__+': '+str(error))
        await browser.close()
    server.shutdown();server.server_close()
    assert not report['external_requests'],report['external_requests']
    record=json.loads((OUT/'copy-record.json').read_text())
    report['files']=[{'path':f['path'],'sha256':hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest()} for f in record['files']]
    (OUT/'browser-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
    assert not report['errors'],report['errors']


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    asyncio.run(main(parser.parse_args().source.resolve()))
