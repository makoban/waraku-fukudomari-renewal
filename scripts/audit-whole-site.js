async (page) => {
  const paths = /*PAGES*/ [];
  const widths = [320,360,375,390,393,412,430,768,1024,1440];
  const records = [];
  await page.emulateMedia({reducedMotion:'reduce'});
  for (const path of paths) {
    await page.setViewportSize({width:390,height:844});
    await page.goto('http://127.0.0.1:8798/'+path,{waitUntil:'load'});
    await page.evaluate(()=>document.fonts.ready);
    for (const width of widths) {
      await page.setViewportSize({width,height:844});
      const audit = await page.evaluate(() => {
        const visible = e => {const b=e.getBoundingClientRect(),s=getComputedStyle(e);return b.width>0&&b.height>0&&s.visibility!=='hidden'&&s.display!=='none'&&!e.closest('dialog:not([open]),[hidden]');};
        const label=e=>e.tagName.toLowerCase()+'.'+e.className;
        const all=[...document.querySelectorAll('body *')].filter(visible).filter(e=>!e.closest('svg')&&!e.classList.contains('sr-only')&&!e.classList.contains('skip-link'));
        const viewportOverflow=all.filter(e=>{const b=e.getBoundingClientRect();return b.left< -1||b.right>document.documentElement.clientWidth+1;}).map(e=>({element:label(e),text:e.textContent.slice(0,75)}));
        const selectors='.hero-grid>*,.services-grid>*,.conversation-grid>*,.access-grid>*,.photo-gallery>*,.header-inner>*,.footer-grid>*,.global-site-nav>a,.hero-actions>*,.contact-methods>*,.section-nav>a,.mobile-contact>a,.service-card-grid>*,.service-card>*,.home-intro-grid>*,.two-column-editorial>*,.facility-summary>*,.floor-gallery>*,.journal-grid>*,.journal-teasers>*,.page-intro-grid>*,.service-detail-grid>*,.rehab-detail-grid>*,.company-grid>*,.company-table>div>*,.salary-table>div>*,.recruit-grid>*,.blog-filter>*,.blog-filter input,.blog-filter select,.post-photo-grid>*,.article-neighbors>*,.daily-timeline>li>*';
        const parentOverflow=[...document.querySelectorAll(selectors)].filter(visible).flatMap(e=>{const b=e.getBoundingClientRect(),p=e.parentElement,pb=p.getBoundingClientRect(),s=getComputedStyle(p);const left=pb.left+parseFloat(s.borderLeftWidth)+parseFloat(s.paddingLeft),right=pb.right-parseFloat(s.borderRightWidth)-parseFloat(s.paddingRight);return b.left<left-1||b.right>right+1?[{element:label(e),parent:label(p),text:e.textContent.slice(0,60),left:b.left,right:b.right,parentLeft:left,parentRight:right}]:[];});
        const phraseOverflow=[...document.querySelectorAll('.phrase,.keep')].filter(visible).flatMap(e=>{const r=document.createRange();r.selectNodeContents(e);const text=r.getBoundingClientRect(),box=e.getBoundingClientRect();return text.width>box.width+1?[{text:e.textContent,width:text.width,box:box.width}]:[];});
        return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,viewportOverflow,parentOverflow,phraseOverflow};
      });
      records.push({path,...audit});
    }
  }
  return {checked_pages:paths, widths, checks:records.length, failures:records.filter(r=>r.viewportOverflow.length||r.parentOverflow.length||r.phraseOverflow.length)};
}
